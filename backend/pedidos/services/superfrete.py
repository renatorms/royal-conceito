"""Thin client for the SuperFrete shipping-quote API (cálculo de frete).

Only talks to POST {SUPERFRETE_BASE_URL}/api/v0/calculator — no Django/DRF
concerns here (no exceptions tied to DRF, no request/response objects from a
view). The caller (pedidos/views.py::FreteCalcularView) maps the exceptions
below onto actual HTTP responses.

Request/response shapes were confirmed against the real SuperFrete sandbox
via curl while building this integration (the official docs don't show a
full response example) — see CLAUDE.md for the verified payloads and the
sandbox/production base URLs.
"""

import re
from decimal import Decimal

import requests
from django.conf import settings

# PAC (1), SEDEX (2), Mini Envios (17) — the three Correios-based services
# enabled on this SuperFrete account. SuperFrete silently omits any service
# from the response that doesn't apply (e.g. too heavy/large for Mini
# Envios) rather than erroring, so it's safe to always ask for all three.
SERVICOS = "1,2,17"

# Required by the SuperFrete API per its own docs — format is "app name
# (contact email)". The sandbox tolerated a missing User-Agent during
# testing, but this is sent unconditionally anyway, matching the documented
# contract rather than the sandbox's leniency.
USER_AGENT = "Royal Conceito (rramosmachados16@gmail.com)"

TIMEOUT_SEGUNDOS = 10


class SuperFreteError(Exception):
    """Base class for any SuperFrete API failure. The message is meant for
    logs, not for showing a client directly — it may include raw API
    responses. FreteCalcularView catches the specific subclasses below,
    never this base class directly, so every failure is deliberately
    classified rather than falling through to a generic case."""


class SuperFreteConfiguracaoError(SuperFreteError):
    """Auth/config problem on our side (missing or invalid
    SUPERFRETE_TOKEN) — not something the client did wrong, and not safe to
    describe to them (would leak that our credentials are broken)."""


class SuperFreteDestinoInvalidoError(SuperFreteError):
    """The destination CEP was rejected by SuperFrete as invalid/
    unserviceable — a genuine client-input problem, safe to say so."""


class SuperFreteIndisponivelError(SuperFreteError):
    """Network failure, timeout, or any other non-200/unexpected response —
    SuperFrete (or the network path to it) is having trouble, not something
    fixable by the client changing their input."""


def calcular_frete(cep_destino, produtos):
    """Calls the SuperFrete calculator and returns the available shipping
    options.

    `produtos` is an iterable of dicts, one per cart line, each with:
      - altura, largura, comprimento: cm (int)
      - peso: kg (Decimal/float)
      - quantidade: int
      - valor: Decimal/float — this line's unit price, used only to sum a
        total declared/insured value for the shipment (SuperFrete takes one
        insurance_value for the whole shipment, not per product — confirmed
        via the real API, see CLAUDE.md).

    Returns a list of dicts, one per shipping option SuperFrete offers:
      {"id", "nome", "transportadora", "preco", "prazo_dias"}

    Raises a SuperFreteError subclass on any failure — never returns a
    partial/guessed result.
    """
    produtos = list(produtos)
    valor_segurado = sum(
        Decimal(str(produto["valor"])) * produto["quantidade"] for produto in produtos
    )

    payload = {
        "from": {"postal_code": settings.SUPERFRETE_CEP_ORIGEM},
        # Strips non-digits so either "01153-000" or "01153000" from the
        # caller works the same way — the API itself only accepts the
        # 8-digit form, confirmed via curl.
        "to": {"postal_code": re.sub(r"\D", "", cep_destino)},
        "services": SERVICOS,
        "options": {
            "own_hand": False,
            "receipt": False,
            "insurance_value": float(valor_segurado),
            "use_insurance_value": True,
        },
        "products": [
            {
                "quantity": produto["quantidade"],
                "height": produto["altura"],
                "length": produto["comprimento"],
                "width": produto["largura"],
                "weight": float(produto["peso"]),
            }
            for produto in produtos
        ],
    }

    try:
        response = requests.post(
            f"{settings.SUPERFRETE_BASE_URL}/api/v0/calculator",
            json=payload,
            headers={
                "Authorization": f"Bearer {settings.SUPERFRETE_TOKEN}",
                "User-Agent": USER_AGENT,
            },
            timeout=TIMEOUT_SEGUNDOS,
        )
    except requests.RequestException as exc:
        raise SuperFreteIndisponivelError(
            f"Falha de rede ao chamar a API da SuperFrete: {exc}"
        ) from exc

    if response.status_code in (401, 403):
        # Confirmed via curl against the real sandbox with a bogus token:
        # {"message": "Token inválida!", "error": "Token inválida!"}, 401.
        raise SuperFreteConfiguracaoError(
            f"SuperFrete rejeitou o token configurado (status {response.status_code}): "
            f"{response.text[:500]}"
        )

    if response.status_code == 400:
        raise _classificar_erro_400(response)

    if response.status_code != 200:
        raise SuperFreteIndisponivelError(
            f"SuperFrete retornou {response.status_code}: {response.text[:500]}"
        )

    try:
        opcoes = response.json()
    except ValueError as exc:
        raise SuperFreteIndisponivelError(
            f"Resposta da SuperFrete não é um JSON válido: {response.text[:500]}"
        ) from exc

    if not isinstance(opcoes, list):
        raise SuperFreteIndisponivelError(
            f"Formato de resposta inesperado da SuperFrete: {opcoes!r}"
        )

    return [
        {
            "id": opcao["id"],
            "nome": opcao["name"],
            "transportadora": opcao.get("company", {}).get("name", ""),
            "preco": opcao["price"],
            "prazo_dias": opcao["delivery_time"],
        }
        for opcao in opcoes
        if not opcao.get("has_error")
    ]


def _classificar_erro_400(response):
    # SuperFrete returns 400 both for a genuinely bad/unserviceable
    # destination CEP and for other validation problems (e.g. malformed
    # dimensions — a bug on our side, not the client's). Only the CEP case
    # is safe to report back to the client as their own mistake; distinguish
    # by checking for the specific error keys SuperFrete uses for
    # postal-code problems, confirmed via curl against the real sandbox
    # (`{"errors": {"correios.destination_postcode": [...],
    # "ms-freight-calculator.no_result": [...]}, "message": "..."}`) — see
    # CLAUDE.md for the full reproduction.
    try:
        corpo = response.json()
    except ValueError:
        return SuperFreteIndisponivelError(
            f"SuperFrete 400 sem JSON válido: {response.text[:500]}"
        )

    chaves_erro = corpo.get("errors", {}) if isinstance(corpo, dict) else {}
    if any(
        "postal_code" in chave or "postcode" in chave or "no_result" in chave
        for chave in chaves_erro
    ):
        return SuperFreteDestinoInvalidoError(
            f"CEP de destino rejeitado pela SuperFrete: {corpo}"
        )
    return SuperFreteIndisponivelError(f"SuperFrete 400 inesperado: {corpo}")
