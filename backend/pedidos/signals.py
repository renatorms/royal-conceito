from django.db import transaction
from django.db.models import F
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver
from rest_framework.exceptions import ValidationError

from produtos.models import Variacao

from .models import ItemPedido


@receiver(pre_save, sender=ItemPedido)
def calcula_subtotal(sender, instance, **kwargs):
    instance.subtotal = instance.quantidade * instance.preco_unitario


@receiver(post_save, sender=ItemPedido)
@transaction.atomic
def diminui_estoque(sender, instance, created, **kwargs):
    if created:
        # select_for_update() locks this row for the rest of the current
        # transaction on backends that support it (Postgres, MySQL/InnoDB) —
        # a second concurrent transaction's own select_for_update() on the
        # same row blocks until this one commits/rolls back, so it always
        # sees this decrement's result rather than racing against it. SQLite
        # does NOT support this (connection.features.has_select_for_update is
        # False there — confirmed via `manage.py shell`), so on the project's
        # current dev DB this call is a silent no-op: no error, no lock,
        # just a plain SELECT. That's exactly why the decrement below does
        # NOT rely on this lock alone.
        variacao = Variacao.objects.select_for_update().get(pk=instance.variacao_id)

        # Valida se tem estoque suficiente
        if variacao.estoque < instance.quantidade:
            # `detail` is passed as a dict (not a bare string) so DRF's
            # exception_handler serializes this as {"detail": "..."} instead
            # of coercing it into a bare list (ValidationError.__init__ does
            # that for any non-dict/non-list detail) — matches the
            # {"detail": ...} shape every other error in this API already
            # uses (see PermissionDenied usages in views.py), which is what
            # the frontend's error handling expects.
            raise ValidationError(
                {
                    "detail": (
                        f"Estoque insuficiente. Restam apenas {variacao.estoque} unidades."
                    )
                }
            )

        # Atomic conditional UPDATE — not `variacao.estoque -= quantidade;
        # variacao.save()`, which reads the value into Python, computes an
        # *absolute* new value, and writes it back with no guarantee the row
        # hasn't changed since the read (a classic lost-update: two
        # concurrent transactions both read estoque=1, both compute 1-1=0,
        # both write 0, even though two units were "sold"). This single SQL
        # statement instead evaluates `estoque__gte=quantidade` and
        # `F("estoque") - quantidade` together, against whatever the row's
        # current value is at the moment the statement runs — a concurrent
        # writer can't split "check" from "write" apart here, so this is
        # safe against the race on *any* backend, including SQLite, where
        # the select_for_update() lock above is a no-op. This is the real
        # backstop; the check above is what gives an accurate, immediate
        # error message in the common (non-racing) case.
        linhas_afetadas = Variacao.objects.filter(
            pk=variacao.pk, estoque__gte=instance.quantidade
        ).update(estoque=F("estoque") - instance.quantidade)

        if linhas_afetadas == 0:
            # Lost a race between the check above and this UPDATE — should be
            # unreachable while select_for_update() actually holds the lock
            # (Postgres/MySQL), but is the path that matters on SQLite,
            # where that lock never happened. Re-read for an accurate
            # message rather than reusing the now-stale in-memory value.
            variacao.refresh_from_db(fields=["estoque"])
            raise ValidationError(
                {
                    "detail": (
                        f"Estoque insuficiente. Restam apenas {variacao.estoque} unidades."
                    )
                }
            )


@receiver(post_save, sender=ItemPedido)
@transaction.atomic
def atualiza_total_pedido(
    sender, instance, **kwargs
):  # recalcula total de pedido automaticamente
    pedido = instance.pedido
    itens = pedido.itens.all()
    total = sum(item.subtotal for item in itens)
    pedido.total = total
    pedido.save()


@receiver(post_delete, sender=ItemPedido)
@transaction.atomic
def atualiza_total_ao_deletar(sender, instance, **kwargs):
    pedido = instance.pedido
    itens = pedido.itens.all()
    pedido.total = sum(item.subtotal for item in itens)
    pedido.save()
