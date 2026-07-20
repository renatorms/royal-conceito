from rest_framework import exceptions
from rest_framework.authentication import CSRFCheck
from rest_framework_simplejwt.authentication import JWTAuthentication


class CookieJWTAuthentication(JWTAuthentication):
    """Autentica via JWT lido do cookie httpOnly 'access_token' em vez do header Authorization.

    Como o token passa a viajar num cookie enviado automaticamente pelo
    navegador, aplicamos a mesma checagem de CSRF que a SessionAuthentication
    do DRF usa, exigindo o header X-CSRFToken em requisições que alteram dado.
    """

    def authenticate(self, request):
        raw_token = request.COOKIES.get("access_token")
        if raw_token is None:
            return None

        validated_token = self.get_validated_token(raw_token)
        user = self.get_user(validated_token)

        self.enforce_csrf(request)

        return user, validated_token

    def enforce_csrf(self, request):
        def dummy_get_response(request):
            return None

        check = CSRFCheck(dummy_get_response)
        check.process_request(request)
        reason = check.process_view(request, None, (), {})
        if reason:
            raise exceptions.PermissionDenied(f"CSRF Failed: {reason}")
