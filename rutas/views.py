from django.shortcuts import render
from .models import Horario

def lista_rutas(request):
    # Trae todos los horarios conn los datos de la ruta en una sola consulta
    horarios = Horario.objects.select_related("ruta").all().order_by("ruta__codigo_ruta")
    return render(request, "rutas/lista.html", {
        "horarios": horarios,
    })

def inicio(request):
    return render(request, "rutas/lista.html")