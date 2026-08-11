from django.urls import path

from .views import AlterarSenhaView, MeView, RegisterView

urlpatterns = [
    path("registro/", RegisterView.as_view(), name="registro"),
    path("me/", MeView.as_view(), name="me"),
    path("me/senha/", AlterarSenhaView.as_view(), name="me-senha"),
]
