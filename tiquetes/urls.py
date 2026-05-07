from django.urls import path
from . import views

app_name = "tiquetes"

urlpatterns = [
    path("comprar/<int:horario_id>/", views.comprar, name="comprar"),
    path("mis-tiquetes/", views.mis_tiquetes, name="mis_tiquetes"),
    path("pdf/<int:tiquete_id>/", views.descargar_pdf, name="pdf"),
]
