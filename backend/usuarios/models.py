from django.conf import settings
from django.db import models


class PerfilUsuario(models.Model):
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="perfil"
    )
    # CASCADE, não PROTECT: diferente de Pedido/ItemPedido (histórico de
    # venda que precisa sobreviver mesmo que o usuário seja removido), este
    # é só dado de perfil — não existe razão para mantê-lo órfão se a conta
    # em si deixa de existir. Mesmo padrão de Endereco.usuario.
    telefone = models.CharField(max_length=20, null=True, blank=True)
    # null=True, blank=True: nem todo usuário (em especial os já existentes
    # antes deste campo) tem telefone cadastrado. Sem formatação/validação
    # de padrão brasileiro imposta aqui de propósito — o frontend não impõe
    # uma máscara rígida, e um CharField livre evita rejeitar um número
    # internacional ou um formato que o usuário prefira digitar.

    def __str__(self):
        return f"Perfil de {self.usuario}"
