from django.contrib.auth.models import User
from rest_framework import serializers


class MeSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "is_staff"]


class AtualizarPerfilSerializer(serializers.ModelSerializer):
    # Only `email` in `fields` — `username` is deliberately not editable
    # through this endpoint at all (not read_only, just absent, so a client
    # sending it is silently ignored, same pattern used elsewhere in this
    # project to protect a field — e.g. Pedido.usuario). Reasoning: username
    # is the login identifier (`POST /api/token/` takes username/password,
    # there's no login-by-email flow), so letting it change risks a user
    # locking themselves out of their own saved/autofilled credentials for
    # no real benefit here — nothing in the UI surfaces username as a
    # "profile" concept beyond the Header greeting. email, unlike username,
    # is an ordinary contact field with no auth-identifier role, so it's the
    # one field that makes sense to let the user correct themselves.
    class Meta:
        model = User
        fields = ["email"]

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
