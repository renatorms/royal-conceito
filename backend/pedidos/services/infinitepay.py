"""Thin client for the InfinitePay checkout-link API (link de pagamento).

Same shape as pedidos/services/superfrete.py — no Django/DRF concerns here
(no exceptions tied to DRF, no request/response objects from a view). The
caller (pedidos/views.py) maps the exceptions below onto actual HTTP
responses.

Request/response shapes for POST /links and POST /payment_check were
confirmed against the real InfinitePay API via curl while building this
integration (using the dev/test handle "renato-ramos-0g5") — see CLAUDE.md
for the verified payloads. Unlike SuperFrete, InfinitePay doesn't expose a
separate sandbox host or require a per-request auth token: any caller that
knows a valid handle can generate a checkout link for that account (the
handle itself is the public identifier, same idea as a payment.me/handle
link) — so INFINITEPAY_BASE_URL is a fixed constant, not derived from DEBUG
like SUPERFRETE_BASE_URL is.
"""

import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

INFINITEPAY_BASE_URL = "https://api.checkout.infinitepay.io"

TIMEOUT_SEGUNDOS = 10


class InfinitePayError(Exception):
    """Base class for any InfinitePay API failure. The message is meant for
    logs, not for showing a client directly. Callers catch the specific
    subclasses below, never this base class directly."""


class InfinitePayConfiguracaoError(InfinitePayError):
    """Our own setup is broken — INFINITEPAY_HANDLE isn't configured, or the
    API rejected the handle itself as invalid/nonexistent. Not the
    customer's fault, and not safe to describe to them (would leak that our
    account configuration is broken)."""


class InfinitePayIndisponivelError(InfinitePayError):
    """Network failure, timeout, or any other unexpected response —
    InfinitePay (or the network path to it) is having trouble, or our own
    request payload was malformed. Either way, not something the customer
    can fix by changing their input (unlike SuperFrete's destination-CEP
    case, every field sent to InfinitePay here is server-generated from the
    Pedido itself, never taken directly from client input — so there's no
    "safe to relay to the client" case to split out separately)."""


def criar_link_pagamento(order_nsu, itens, redirect_url, webhook_url):
    """Calls POST /links and returns the checkout URL for the customer to
    complete payment.

    `itens` is an iterable of dicts, one per line, each with:
      - descricao: str
      - quantidade: int
      - preco_centavos: int — unit price in cents (confirmed via curl: this
        API's `price` field is per unit, not a line total — a {quantity: 3,
        price: 500} line is a distinct link from a {quantity: 1, price:
        1500} one).

    Raises an InfinitePayError subclass on any failure — never returns a
    partial/guessed result.
    """
    if not settings.INFINITEPAY_HANDLE:
        raise InfinitePayConfiguracaoError("INFINITEPAY_HANDLE não está configurado.")

    payload = {
        "handle": settings.INFINITEPAY_HANDLE,
        "order_nsu": order_nsu,
        "redirect_url": redirect_url,
        "webhook_url": webhook_url,
        "items": [
            {
                "quantity": item["quantidade"],
                "price": item["preco_centavos"],
                "description": item["descricao"],
            }
            for item in itens
        ],
    }

    try:
        response = requests.post(
            f"{INFINITEPAY_BASE_URL}/links",
            json=payload,
            timeout=TIMEOUT_SEGUNDOS,
        )
    except requests.RequestException as exc:
        raise InfinitePayIndisponivelError(
            f"Falha de rede ao chamar a API da InfinitePay: {exc}"
        ) from exc

    if response.status_code == 200:
        try:
            corpo = response.json()
        except ValueError as exc:
            raise InfinitePayIndisponivelError(
                f"Resposta da InfinitePay não é um JSON válido: {response.text[:500]}"
            ) from exc

        url = corpo.get("url")
        if not url:
            raise InfinitePayIndisponivelError(
                f"Resposta da InfinitePay sem campo 'url': {corpo!r}"
            )
        return url

    # Confirmed via curl: a handle InfinitePay doesn't recognize returns 422
    # with {"success": false, "message": "Unable to create checkout link"} —
    # distinct from a malformed-payload 400/422 (missing/invalid field on a
    # payload we fully control), which is a bug on our side rather than a
    # bad handle specifically. Both end up mapped to the same 503 by the
    # view (there's no "safe to tell the client" case here either way), but
    # kept as separate exception classes for clearer logging, same reasoning
    # as the SuperFrete client's error split.
    if response.status_code == 422:
        try:
            corpo = response.json()
        except ValueError:
            corpo = {}
        if corpo.get("message") == "Unable to create checkout link":
            raise InfinitePayConfiguracaoError(
                f"InfinitePay rejeitou o handle configurado: {response.text[:500]}"
            )

    raise InfinitePayIndisponivelError(
        f"InfinitePay retornou {response.status_code}: {response.text[:500]}"
    )


def verificar_pagamento(order_nsu, transaction_nsu, slug):
    """Calls POST /payment_check to independently confirm, directly with
    InfinitePay, whether a given transaction was actually paid — see
    InfinitePayWebhookView (pedidos/views.py) for why this call exists at
    all: InfinitePay's webhook payload carries no signature/HMAC/secret of
    any kind (confirmed via their docs — nothing to verify a POST to our
    webhook endpoint genuinely came from InfinitePay and wasn't forged), so
    the webhook body's claim of "paid" is never trusted on its own. This
    call is the actual authentication step: it asks InfinitePay's own API,
    using the specific transaction_nsu/slug the webhook claimed, whether
    that transaction really exists and is really paid, for that handle and
    order_nsu. A forged webhook naming a transaction_nsu that doesn't exist
    (or was never paid) gets a real {"success": false} back here — the
    request itself has no auth of its own (confirmed via curl: an
    unrecognized transaction_nsu still returns 200 rather than 401/403), but
    that's fine, since the property being checked isn't "is the caller
    InfinitePay" — it's "does InfinitePay's own ledger agree this specific
    transaction was paid."

    Returns {"paid": bool, "amount_centavos": int | None}. `amount_centavos`
    is None when `paid` is False (a fake/unpaid transaction_nsu returns just
    {"success": false} with no amount field, confirmed via curl).

    Raises an InfinitePayError subclass if the check itself couldn't be
    completed (network/unexpected response) — deliberately distinct from a
    successful check that came back unpaid, so the caller can tell "we
    don't know" apart from "we know it's not paid".
    """
    payload = {
        "handle": settings.INFINITEPAY_HANDLE,
        "order_nsu": order_nsu,
        "transaction_nsu": transaction_nsu,
        "slug": slug,
    }

    try:
        response = requests.post(
            f"{INFINITEPAY_BASE_URL}/payment_check",
            json=payload,
            timeout=TIMEOUT_SEGUNDOS,
        )
    except requests.RequestException as exc:
        raise InfinitePayIndisponivelError(
            f"Falha de rede ao chamar payment_check da InfinitePay: {exc}"
        ) from exc

    if response.status_code != 200:
        raise InfinitePayIndisponivelError(
            f"InfinitePay payment_check retornou {response.status_code}: {response.text[:500]}"
        )

    try:
        corpo = response.json()
    except ValueError as exc:
        raise InfinitePayIndisponivelError(
            f"Resposta do payment_check não é um JSON válido: {response.text[:500]}"
        ) from exc

    if not corpo.get("success") or not corpo.get("paid"):
        return {"paid": False, "amount_centavos": None}

    return {"paid": True, "amount_centavos": corpo.get("amount")}
