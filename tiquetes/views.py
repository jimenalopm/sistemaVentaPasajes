from django.shortcuts import render
from django.http import HttpResponse


def comprar(request, horario_id):
    return HttpResponse("comprar - próximamente")


def mis_tiquetes(request):
    return HttpResponse("mis tiquetes - próximamente")


def descargar_pdf(request, tiquete_id):
    return HttpResponse("pdf - próximamente")
