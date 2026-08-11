from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import PerfilUsuario


class MeSerializer(serializers.ModelSerializer):
    # SerializerMethodField, not CharField(source="perfil.telefone"):
    # `perfil` is a reverse OneToOneField accessor (see PerfilUsuario.usuario
    # below), and there's no PerfilUsuario row for every User — in
    # particular, every account that existed before this field was added.
    # Accessing a missing reverse OneToOne in Django raises
    # `User.perfil.RelatedObjectDoesNotExist` (a subclass of both
    # `ObjectDoesNotExist` and `AttributeError`) — rather than lean on
    # exactly how DRF's field resolution happens to handle that exception
    # today, get_telefone() below checks explicitly and returns `None` for
    # any user with no PerfilUsuario yet, same as if `telefone` had simply
    # never been set.
    telefone = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "email", "is_staff", "telefone"]

    def get_telefone(self, obj):
        perfil = getattr(obj, "perfil", None)
        return perfil.telefone if perfil else None


class AtualizarPerfilSerializer(serializers.ModelSerializer):
    # `email` in `Meta.fields` (a real `User` field) — `username` is
    # deliberately not editable through this endpoint at all (not read_only,
    # just absent, so a client sending it is silently ignored, same pattern
    # used elsewhere in this project to protect a field — e.g.
    # Pedido.usuario). Reasoning: username is the login identifier (`POST
    # /api/token/` takes username/password, there's no login-by-email flow),
    # so letting it change risks a user locking themselves out of their own
    # saved/autofilled credentials for no real benefit here — nothing in the
    # UI surfaces username as a "profile" concept beyond the Header greeting.
    # email, unlike username, is an ordinary contact field with no
    # auth-identifier role, so it's the one field that makes sense to let
    # the user correct themselves.
    #
    # `telefone` is declared explicitly, not left to ModelSerializer's
    # auto-generation: it isn't a `User` field at all (see PerfilUsuario
    # above), so there's nothing for Meta.model=User to introspect it from.
    # `allow_blank=True` lets a client clear a previously-set phone number
    # by sending `""`, distinct from omitting the field entirely on a
    # partial PATCH (see update() below, which only touches PerfilUsuario
    # when `telefone` was actually part of the request).
    telefone = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, max_length=20
    )

    class Meta:
        model = User
        fields = ["email", "telefone"]

    def validate_email(self, value):
        # Django's default User model has no unique=True on email, and
        # RegisterSerializer doesn't enforce it either — a real, pre-existing
        # inconsistency (see CLAUDE.md) not fixed here, since two users
        # registering with the same email is a separate, out-of-scope gap.
        # This check only guards the update path: excludes the current user
        # so saving your own unchanged email never false-positives as a
        # duplicate.
        if User.objects.exclude(pk=self.instance.pk).filter(email=value).exists():
            raise serializers.ValidationError("Este e-mail já está em uso por outra conta.")
        return value

    def update(self, instance, validated_data):
        # `telefone` isn't a `User` field, so it has to be popped out before
        # handing the rest to ModelSerializer's default update() (which
        # would otherwise try `User(**validated_data)` and fail on an
        # unexpected keyword). Only touches PerfilUsuario when `telefone`
        # was actually present in this request — a PATCH that only sends
        # `email` must not implicitly wipe an already-saved phone number by
        # writing `None` over it.
        telefone_enviado = "telefone" in validated_data
        telefone = validated_data.pop("telefone", None)
        instance = super().update(instance, validated_data)

        if telefone_enviado:
            # get_or_create, not a plain PerfilUsuario.objects.get(): most
            # users today have no PerfilUsuario row at all (see MeSerializer
            # above) — the first time anyone sets a phone number, this is
            # what actually creates that row, rather than requiring a
            # separate signup-time step or a backfill migration for every
            # existing account.
            perfil, _ = PerfilUsuario.objects.get_or_create(usuario=instance)
            perfil.telefone = telefone
            perfil.save(update_fields=["telefone"])

        return instance


class AlterarSenhaSerializer(serializers.Serializer):
    """Input shape for POST /me/senha/ — not a ModelSerializer: neither
    field maps to a real, directly-settable `User` column (`password` is
    always set via `set_password()`, never assigned raw), so there's no
    `Meta.model` this would meaningfully derive from.
    """

    senha_atual = serializers.CharField(write_only=True)
    nova_senha = serializers.CharField(write_only=True)

    def validate_senha_atual(self, value):
        # request.user, not self.instance: this serializer has no instance,
        # since there's nothing to partially update — the view passes the
        # request in via context (see AlterarSenhaView below) the same way
        # DRF's own PasswordChangeSerializer pattern does.
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Senha atual incorreta.")
        return value

    def validate_nova_senha(self, value):
        # Django's own validate_password() runs the same
        # AUTH_PASSWORD_VALIDATORS configured in core/settings.py (minimum
        # length, not-too-common, not-all-numeric, ...) — the same rules a
        # Django-admin-created superuser's password already has to satisfy.
        # Passing `user=` lets UserAttributeSimilarityValidator check the new
        # password isn't just the username/email again. Note this is a real,
        # pre-existing inconsistency with registration: RegisterSerializer
        # (above) never calls validate_password() at all today, so a new
        # account can still be created with a trivially weak password — not
        # fixed here, same "flagged, not fixed, separate task" treatment as
        # the duplicate-email gap already documented on that path.
        validate_password(value, user=self.context["request"].user)
        return value

    def save(self):
        user = self.context["request"].user
        user.set_password(self.validated_data["nova_senha"])
        user.save(update_fields=["password"])
        return user


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["username", "email", "password"]

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
        )
        return user
