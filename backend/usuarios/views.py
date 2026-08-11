from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import (
    AlterarSenhaSerializer,
    AtualizarPerfilSerializer,
    MeSerializer,
    RegisterSerializer,
)


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    throttle_scope = "registro"


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        return Response(MeSerializer(request.user).data)

    def patch(self, request, *args, **kwargs):
        # Same resource as GET above (the current user), not a separate
        # endpoint — PATCH is the natural verb for a partial update, and a
        # dedicated /api/perfil/ route would just duplicate the "who is the
        # current user" resolution GET already does via `request.user`.
        # `partial=True` even though AtualizarPerfilSerializer only has one
        # field today: standard PATCH semantics (a client can send `{}` and
        # nothing changes, rather than `email` becoming spuriously required).
        serializer = AtualizarPerfilSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(MeSerializer(request.user).data)


class AlterarSenhaView(APIView):
    # Same URL family as MeView ("current user"), but its own view/route
    # rather than a third verb on MeView: unlike GET/PATCH above (both
    # reading/writing the same MeSerializer-shaped resource), changing a
    # password is an action with its own input shape (senha_atual/
    # nova_senha, neither of which is `password` on User directly — see
    # AlterarSenhaSerializer) and its own distinct success/failure semantics
    # (wrong current password is a 400 naming *why*, not a generic
    # validation error on a "current user" PATCH).
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = AlterarSenhaSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Senha alterada com sucesso."})
