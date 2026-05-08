from django.shortcuts import render
from django.http import HttpResponse


def lista_rutas(request):
    return render(request, "rutas/lista.html")


def inicio(request):
    return render(request, "rutas/lista.html")