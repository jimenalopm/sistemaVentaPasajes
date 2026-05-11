from django.urls import path
from . import views

app_name = "usuarios"

urlpatterns = [
    path("registro/", views.registro, name="registro"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("tarjetas/", views.mis_tarjetas, name="mis_tarjetas"),
    path("tarjetas/agregar/", views.agregar_tarjeta, name="agregar_tarjeta"),
    path("tarjetas/<int:tarjeta_id>/eliminar/", views.eliminar_tarjeta, name="eliminar_tarjeta"),
]
