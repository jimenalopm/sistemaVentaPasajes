from django.contrib import admin
from django.urls import path, include
from rutas import views  # Importamos las vistas de rutas #cambio tavo


urlpatterns = [  # todo esto es para saber dependiendo de como empieze la url a que parte de nuestro codigo mandar la peticion
    path("admin/", admin.site.urls),
    path("usuarios/", include("usuarios.urls")),
    path("rutas/", include("rutas.urls")),
    path("tiquetes/", include("tiquetes.urls")),
    # path("", include("rutas.urls_home")),

    # ESTA ES LA QUE FALTA: La ruta vacía para el inicio
    path('', views.inicio, name='inicio'),
]
