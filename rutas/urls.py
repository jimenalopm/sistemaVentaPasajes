from django.urls import path
from . import views

app_name = "rutas"

urlpatterns = [
    path("", views.inicio, name="inicio"), 
    path("lista/", views.lista_rutas, name="lista_rutas"),
]
