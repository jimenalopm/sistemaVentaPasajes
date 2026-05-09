from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required  # protege páginas con sesión
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
import uuid  # para generar códigos únicos

from .models import Tiquete
from rutas.models import Horario, Bus



# PASO 1: El usuario elige la fecha de viaje
# URL: /tiquetes/comprar/<horario_id>/

@login_required(login_url="/usuarios/login/")
# @login_required protege esta vista: si el usuario NO está logueado
# lo redirige automáticamente al login en vez de mostrar la página

def comprar(request, horario_id):
    # Buscamos el horario elegido o devolvemos error 404 si no existe
    horario = get_object_or_404(Horario.objects.select_related("ruta"), id=horario_id)
    cliente = request.user.cliente  # accedemos al perfil del usuario logueado

    #Validación 1: el cliente no puede tener más de 5 tiquetes
    total_tiquetes = Tiquete.objects.filter(cliente=cliente).count()
    if total_tiquetes >= 5:
        messages.error(request, "No podés comprar más de 5 pasajes en total.")
        return redirect("rutas:lista_rutas")

    # Validación 2: el cliente debe tener una tarjeta registrada 
    tarjetas = cliente.tarjetas.all()
    if not tarjetas.exists():
        messages.warning(request, "Necesitás registrar una tarjeta antes de comprar.")
        return redirect("rutas:lista_rutas")

    #  Calculamos el rango de fechas permitidas (maximo 1 semana) 
    hoy = timezone.now().date()
    fecha_min = hoy + timedelta(days=1)   # minimo mañana
    fecha_max = hoy + timedelta(days=7)   # maximo 7 días

   
    # Si el usuario envió el formulario con la fecha
   
    if request.method == "POST":
        fecha_str = request.POST.get("fecha_salida")  # leemos la fecha del form

        # Validamos que se mandó una fecha
        if not fecha_str:
            messages.error(request, "Debés seleccionar una fecha de salida.")
            return redirect("tiquetes:comprar", horario_id=horario_id)

        # Convertimos el string de fecha a objeto date
        from datetime import datetime
        try:
            fecha_salida = datetime.strptime(fecha_str, "%Y-%m-%d").date()
        except ValueError:
            messages.error(request, "Fecha inválida.")
            return redirect("tiquetes:comprar", horario_id=horario_id)

        #  Validación 3: la fecha debe estar dentro del rango 
        if fecha_salida < fecha_min or fecha_salida > fecha_max:
            messages.error(request, f"La fecha debe estar entre {fecha_min} y {fecha_max}.")
            return redirect("tiquetes:comprar", horario_id=horario_id)

        # Combinamos fecha elegida + hora del horario para tener el datetime completo
        fecha_salida_dt = timezone.make_aware(
            datetime.combine(fecha_salida, horario.hora_salida)
        )

        # Buscamos un bus disponible (activo)
        bus = Bus.objects.filter(estado="Activo").first()
        if not bus:
            messages.error(request, "No hay buses disponibles en este momento.")
            return redirect("rutas:lista_rutas")

        # Usamos la primera tarjeta del cliente
        tarjeta = tarjetas.first()

        #  Generamos el código único del tiquete 
        # uuid4() genera un código aleatorio, tomamos los primeros 8 caracteres
        # y lo combinamos con el código de ruta para que sea más legible
        # Ejemplo: CR-NI-A3F9B2C1
        codigo_unico = f"{horario.ruta.codigo_ruta}-{str(uuid.uuid4()).upper()[:8]}"

        #  Creamos el tiquete en la base de datos 
        tiquete = Tiquete.objects.create(
            horario=horario,
            tarjeta=tarjeta,
            cliente=cliente,
            bus=bus,
            codigo=codigo_unico,
            fecha_salida=fecha_salida_dt,
            monto_pagado=horario.ruta.precio,
            estado="Activo",
        )

        messages.success(request, f"¡Tiquete comprado exitosamente! Tu código es: {codigo_unico}")
        # Redirigimos a la página de mis tiquetes
        return redirect("tiquetes:mis_tiquetes")

    # Si el usuario solo abrió la página (GET)
    # le mostramos el formulario con los datos del horario
  
    return render(request, "tiquetes/comprar.html", {
        "horario": horario,
        "tarjetas": tarjetas,
        "fecha_min": fecha_min,
        "fecha_max": fecha_max,
    })



# PASO 2: Ver mis tiquetes comprados
# URL: /tiquetes/mis-tiquetes/

@login_required(login_url="/usuarios/login/")
def mis_tiquetes(request):
    cliente = request.user.cliente

    # Traemos todos los tiquetes del cliente con los datos relacionados en una sola consulta
    tiquetes = Tiquete.objects.filter(cliente=cliente).select_related(
        "horario__ruta", "bus", "tarjeta"
    ).order_by("-fecha_compra")  # los más recientes primero

    return render(request, "tiquetes/mis_tiquetes.html", {
        "tiquetes": tiquetes,
    })



# PASO 3: Descargar PDF del tiquete
# URL: /tiquetes/pdf/<tiquete_id>/

@login_required(login_url="/usuarios/login/")
def descargar_pdf(request, tiquete_id):
    # Solo puede ver el PDF de sus propios tiquetes
    tiquete = get_object_or_404(
        Tiquete.objects.select_related("horario__ruta", "cliente__user", "bus"),
        id=tiquete_id,
        cliente=request.user.cliente,  # seguridad: solo el dueño puede verlo
    )

    # Generamos el PDF con reportlab (hay que instalarlo: pip install reportlab)
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from django.http import HttpResponse
    import io

    # Creamos el PDF en memoria (no en disco)
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    ancho, alto = A4  # A4 = 595 x 842 puntos

    #  Fondo del encabezado 
    p.setFillColor(colors.HexColor("#1a1a2e"))
    p.rect(0, alto - 120, ancho, 120, fill=True, stroke=False)

    #  Título del encabezado 
    p.setFillColor(colors.white)
    p.setFont("Helvetica-Bold", 22)
    p.drawString(2 * cm, alto - 50, "🚌 Transportes Centroamericanos")

    p.setFont("Helvetica", 12)
    p.drawString(2 * cm, alto - 75, "Comprobante Electrónico de Viaje")

    #  Caja del código del tiquete (lo más importante) 
    p.setFillColor(colors.HexColor("#e94560"))
    p.roundRect(2 * cm, alto - 200, ancho - 4 * cm, 60, 10, fill=True, stroke=False)

    p.setFillColor(colors.white)
    p.setFont("Helvetica-Bold", 11)
    p.drawCentredString(ancho / 2, alto - 160, "CÓDIGO DE TIQUETE")
    p.setFont("Helvetica-Bold", 18)
    p.drawCentredString(ancho / 2, alto - 185, tiquete.codigo)

    #  Datos del pasaje 
    p.setFillColor(colors.HexColor("#1a1a2e"))
    p.setFont("Helvetica-Bold", 14)
    p.drawString(2 * cm, alto - 240, "Información del Viaje")

    # Línea separadora
    p.setStrokeColor(colors.HexColor("#e94560"))
    p.setLineWidth(2)
    p.line(2 * cm, alto - 248, ancho - 2 * cm, alto - 248)

    # Datos en dos columnas
    p.setFont("Helvetica", 11)
    p.setFillColor(colors.black)

    datos = [
        ("Ruta:", f"{tiquete.horario.ruta.lugar_salida} → {tiquete.horario.ruta.lugar_llegada}"),
        ("Código de ruta:", tiquete.horario.ruta.codigo_ruta),
        ("Hora de salida:", tiquete.horario.hora_salida.strftime("%I:%M %p")),
        ("Fecha de viaje:", tiquete.fecha_salida.strftime("%d/%m/%Y")),
        ("Monto pagado:", f"${tiquete.monto_pagado}"),
        ("Bus asignado:", tiquete.bus.placa),
        ("Fecha de compra:", tiquete.fecha_compra.strftime("%d/%m/%Y %H:%M")),
        ("Estado:", tiquete.estado),
    ]

    y = alto - 270
    for etiqueta, valor in datos:
        p.setFont("Helvetica-Bold", 11)
        p.drawString(2 * cm, y, etiqueta)
        p.setFont("Helvetica", 11)
        p.drawString(7 * cm, y, valor)
        y -= 28  # bajamos para el siguiente dato

    #  Datos del pasajero 
    p.setFillColor(colors.HexColor("#1a1a2e"))
    p.setFont("Helvetica-Bold", 14)
    p.drawString(2 * cm, y - 10, "Datos del Pasajero")

    p.setStrokeColor(colors.HexColor("#e94560"))
    p.line(2 * cm, y - 18, ancho - 2 * cm, y - 18)

    y -= 40
    p.setFont("Helvetica", 11)
    p.setFillColor(colors.black)

    cliente_datos = [
        ("Nombre:", f"{tiquete.cliente.nombre} {tiquete.cliente.apellido}"),
        ("Pasaporte:", tiquete.cliente.pasaporte),
        ("Nacionalidad:", tiquete.cliente.nacionalidad),
        ("Correo:", tiquete.cliente.user.email),
    ]
    for etiqueta, valor in cliente_datos:
        p.setFont("Helvetica-Bold", 11)
        p.drawString(2 * cm, y, etiqueta)
        p.setFont("Helvetica", 11)
        p.drawString(7 * cm, y, valor)
        y -= 28

    #  Pie de página 
    p.setFillColor(colors.HexColor("#f0f0f0"))
    p.rect(0, 0, ancho, 60, fill=True, stroke=False)
    p.setFillColor(colors.gray)
    p.setFont("Helvetica", 9)
    p.drawCentredString(ancho / 2, 35, "Presente este comprobante al abordar el bus.")
    p.drawCentredString(ancho / 2, 20, "Transportes Centroamericanos S.A. | info@transcentro.com | Tel: +506 2200-0000")

    p.showPage()
    p.save()

    # Enviamos el PDF como respuesta HTTP para que el navegador lo descargue
    buffer.seek(0)
    response = HttpResponse(buffer, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="tiquete-{tiquete.codigo}.pdf"'
    return response