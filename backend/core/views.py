from django.conf import settings
from django.middleware.csrf import get_token
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

ACCESS_COOKIE_NAME = "access_token"
REFRESH_COOKIE_NAME = "refresh_token"
REFRESH_COOKIE_PATH = "/api/token/refresh/"


def _set_auth_cookies(response, access=None, refresh=None):
    if access is not None:
        response.set_cookie(
            ACCESS_COOKIE_NAME,
            access,
            httponly=True,
            secure=not settings.DEBUG,
            samesite="Lax",
            path="/",
        )
    if refresh is not None:
        response.set_cookie(
            REFRESH_COOKIE_NAME,
            refresh,
            httponly=True,
            secure=not settings.DEBUG,
            samesite="Lax",
            path=REFRESH_COOKIE_PATH,
        )


class ThrottledTokenObtainPairView(TokenObtainPairView):
    throttle_scope = "login"

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        access = response.data.pop("access", None)
        refresh = response.data.pop("refresh", None)
        _set_auth_cookies(response, access=access, refresh=refresh)

        # Garante o Set-Cookie do csrftoken para as próximas requisições
        # autenticadas via cookie (ver CookieJWTAuthentication.enforce_csrf).
        get_token(request)

        return response


class CookieTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get(REFRESH_COOKIE_NAME)
        if refresh_token is None:
            return Response({"detail": "Refresh token não encontrado."}, status=401)

        serializer = self.get_serializer(data={"refresh": refresh_token})
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0]) from e

        access = serializer.validated_data.get("access")
        # "refresh" só existe em validated_data se ROTATE_REFRESH_TOKENS estiver ativo.
        refresh = serializer.validated_data.get("refresh")

        response = Response({}, status=status.HTTP_200_OK)
        _set_auth_cookies(response, access=access, refresh=refresh)

        return response


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        response = Response(status=204)
        response.delete_cookie(ACCESS_COOKIE_NAME, path="/")
        response.delete_cookie(REFRESH_COOKIE_NAME, path=REFRESH_COOKIE_PATH)
        return response
