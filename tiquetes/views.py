from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta, datetime
import uuid

from .models import Tiquete
from rutas.models import Horario, Bus
from usuarios.models import Tarjeta 

@login_required(login_url="/usuarios/login/")
def comprar(request, horario_id):
    horario = get_object_or_404(Horario.objects.select_related("ruta"), id=horario_id)
    cliente = request.user.cliente 

    # 1. Validación: Máximo 5 pasajes por persona [cite: 59]
    total_tiquetes = Tiquete.objects.filter(cliente=cliente).count()
    if total_tiquetes >= 5:
        messages.error(request, "No podés comprar más de 5 pasajes en total.")
        return redirect("rutas:lista_rutas")

    # 2. Rango de fechas: Máximo una semana [cite: 59]
    hoy = timezone.now().date()
    fecha_min = hoy + timedelta(days=1)
    fecha_max = hoy + timedelta(days=7)

    if request.method == "POST":
        # Captura de datos del formulario 
        fecha_str = request.POST.get("fecha_salida")
        titular = request.POST.get("titular")
        num_tarjeta = request.POST.get("numero_tarjeta")
        expiracion = request.POST.get("expiracion")
        codigo_seguridad = request.POST.get("cvv") # Dato del HTML

        # Validar que todos los campos requeridos estén llenos 
        if not all([fecha_str, titular, num_tarjeta, expiracion, codigo_seguridad]):
            messages.error(request, "Todos los datos de pago son obligatorios.")
            return redirect("tiquetes:comprar", horario_id=horario_id)

        try:
            fecha_salida = datetime.strptime(fecha_str, "%Y-%m-%d").date()
            if fecha_salida < fecha_min or fecha_salida > fecha_max:
                raise ValueError
        except ValueError:
            messages.error(request, f"Fecha fuera de rango ({fecha_min} a {fecha_max}).")
            return redirect("tiquetes:comprar", horario_id=horario_id)

        # 3. Crear Tarjeta (Corregido a 'ccv' según el requerimiento del examen) 
        try:
            tarjeta_obj = Tarjeta.objects.create(
                cliente=cliente,
                titular=titular,
                numero_tarjeta=num_tarjeta.replace(" ", ""),
                fecha_vencimiento=expiracion,
                ccv=codigo_seguridad, # <--- CAMBIADO A 'ccv' PARA EVITAR EL ERROR
                tipo="Visa"
            )
        except TypeError:
            # Si 'ccv' tampoco funciona, intenta con 'cvv' o revisa tu usuarios/models.py
            messages.error(request, "Error técnico con los campos de la tarjeta.")
            return redirect("tiquetes:comprar", horario_id=horario_id)

        # 4. Asignar Bus y generar código único [cite: 62]
        bus = Bus.objects.filter(estado="Activo").first()
        fecha_salida_dt = timezone.make_aware(datetime.combine(fecha_salida, horario.hora_salida))
        codigo_ticket = f"{horario.ruta.codigo_ruta}-{str(uuid.uuid4()).upper()[:8]}"

        # 5. Crear Tiquete Final
        Tiquete.objects.create(
            horario=horario,
            tarjeta=tarjeta_obj,
            cliente=cliente,
            bus=bus,
            codigo=codigo_ticket,
            fecha_salida=fecha_salida_dt,
            monto_pagado=horario.ruta.precio,
            estado="Activo",
        )

        messages.success(request, f"¡Compra exitosa! Código de viaje: {codigo_ticket}")
        return redirect("tiquetes:mis_tiquetes")

    return render(request, "tiquetes/comprar.html", {
        "horario": horario,
        "fecha_min": fecha_min,
        "fecha_max": fecha_max,
    })
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta, datetime
import uuid

from .models import Tiquete
from rutas.models import Horario, Bus
from usuarios.models import Tarjeta 

@login_required(login_url="/usuarios/login/")
def comprar(request, horario_id):
    horario = get_object_or_404(Horario.objects.select_related("ruta"), id=horario_id)
    cliente = request.user.cliente 

    # 1. Validación de cantidad (Examen)
    if Tiquete.objects.filter(cliente=cliente).count() >= 5:
        messages.error(request, "No podés comprar más de 5 pasajes en total.")
        return redirect("rutas:lista_rutas")

    hoy = timezone.now().date()
    fecha_min, fecha_max = hoy + timedelta(days=1), hoy + timedelta(days=7)

    if request.method == "POST":
        f_salida = request.POST.get("fecha_salida")
        titular = request.POST.get("titular")
        num_t = request.POST.get("numero_tarjeta")
        expira_raw = request.POST.get("expiracion") # Viene como "05/29"
        cod_s = request.POST.get("cvv")

        # Verificar que nada venga vacío
        if not all([f_salida, titular, num_t, expira_raw, cod_s]):
            messages.error(request, "Todos los campos son obligatorios.")
            return redirect("tiquetes:comprar", horario_id=horario_id)

        try:
            # A. Procesar Fecha de Viaje
            dt_viaje = datetime.strptime(f_salida, "%Y-%m-%d").date()
            if dt_viaje < fecha_min or dt_viaje > fecha_max:
                messages.error(request, "Fecha de viaje fuera de rango.")
                return redirect("tiquetes:comprar", horario_id=horario_id)
            
            # B. PROCESAR MES/AÑO DE EXPIRACIÓN (Convertir "05/29" a fecha válida)
            # Separamos el mes y el año
            mes, anio = expira_raw.split('/')
            # Creamos una fecha: Año 20XX, Mes XX, Día 01
            fecha_exp_db = datetime.strptime(f"20{anio}-{mes}-01", "%Y-%m-%d").date()

            # 2. Crear Tarjeta (Usando 'ccv' con doble C como pide el examen)
            tarjeta_obj = Tarjeta.objects.create(
                cliente=cliente,
                titular=titular,
                numero_tarjeta=num_t.replace(" ", ""),
                fecha_vencimiento=fecha_exp_db, # <--- Enviamos la fecha ya convertida
                ccv=cod_s, 
                tipo="Visa"
            )

            # 3. Generar Tiquete
            bus = Bus.objects.filter(estado="Activo").first()
            cod_u = f"{horario.ruta.codigo_ruta}-{str(uuid.uuid4()).upper()[:8]}"
            
            Tiquete.objects.create(
                horario=horario,
                tarjeta=tarjeta_obj,
                cliente=cliente,
                bus=bus,
                codigo=cod_u,
                fecha_salida=timezone.make_aware(datetime.combine(dt_viaje, horario.hora_salida)),
                monto_pagado=horario.ruta.precio,
                estado="Activo",
            )

            messages.success(request, f"¡Compra exitosa! Código: {cod_u}")
            return redirect("tiquetes:mis_tiquetes")

        except Exception as e:
            # Este error captura si el split('/') falla o si el formato no es MM/YY
            messages.error(request, "Formato de expiración incorrecto (Debe ser MM/YY)")
            return redirect("tiquetes:comprar", horario_id=horario_id)

    return render(request, "tiquetes/comprar.html", {
        "horario": horario, "fecha_min": fecha_min, "fecha_max": fecha_max,
    })
# PASO 2: Ver mis tiquetes comprados
@login_required(login_url="/usuarios/login/")
def mis_tiquetes(request):
    cliente = request.user.cliente
    tiquetes = Tiquete.objects.filter(cliente=cliente).select_related(
        "horario__ruta", "bus", "tarjeta"
    ).order_by("-fecha_compra")

    return render(request, "tiquetes/mis_tiquetes.html", {
        "tiquetes": tiquetes,
    })


# PASO 3: Descargar PDF del tiquete
@login_required(login_url="/usuarios/login/")
def descargar_pdf(request, tiquete_id):
    tiquete = get_object_or_404(
        Tiquete.objects.select_related("horario__ruta", "cliente__user", "bus"),
        id=tiquete_id,
        cliente=request.user.cliente,
    )

    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from django.http import HttpResponse
    import io

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    ancho, alto = A4

    p.setFillColor(colors.HexColor("#1a1a2e"))
    p.rect(0, alto - 120, ancho, 120, fill=True, stroke=False)
    p.setFillColor(colors.white)
    p.setFont("Helvetica-Bold", 22)
    p.drawString(2 * cm, alto - 50, "🚌 Transportes Centroamericanos")
    p.setFont("Helvetica", 12)
    p.drawString(2 * cm, alto - 75, "Comprobante Electrónico de Viaje")

    p.setFillColor(colors.HexColor("#e94560"))
    p.roundRect(2 * cm, alto - 200, ancho - 4 * cm, 60, 10, fill=True, stroke=False)
    p.setFillColor(colors.white)
    p.setFont("Helvetica-Bold", 11)
    p.drawCentredString(ancho / 2, alto - 160, "CÓDIGO DE TIQUETE")
    p.setFont("Helvetica-Bold", 18)
    p.drawCentredString(ancho / 2, alto - 185, tiquete.codigo)

    p.setFillColor(colors.HexColor("#1a1a2e"))
    p.setFont("Helvetica-Bold", 14)
    p.drawString(2 * cm, alto - 240, "Información del Viaje")
    p.setStrokeColor(colors.HexColor("#e94560"))
    p.setLineWidth(2)
    p.line(2 * cm, alto - 248, ancho - 2 * cm, alto - 248)

    datos = [
        ("Ruta:", f"{tiquete.horario.ruta.lugar_salida} → {tiquete.horario.ruta.lugar_llegada}"),
        ("Código de ruta:", tiquete.horario.ruta.codigo_ruta),
        ("Hora de salida:", tiquete.horario.hora_salida.strftime("%I:%M %p")),
        ("Fecha de viaje:", tiquete.fecha_salida.strftime("%d/%m/%Y")),
        ("Monto pagado:", f"${tiquete.moted_pagado if hasattr(tiquete, 'moted_pagado') else tiquete.monto_pagado}"),
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
        y -= 28

    p.setFillColor(colors.HexColor("#1a1a2e"))
    p.setFont("Helvetica-Bold", 14)
    p.drawString(2 * cm, y - 10, "Datos del Pasajero")
    p.setStrokeColor(colors.HexColor("#e94560"))
    p.line(2 * cm, y - 18, ancho - 2 * cm, y - 18)

    y -= 40
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

    p.setFillColor(colors.HexColor("#f0f0f0"))
    p.rect(0, 0, ancho, 60, fill=True, stroke=False)
    p.setFillColor(colors.gray)
    p.setFont("Helvetica", 9)
    p.drawCentredString(ancho / 2, 35, "Presente este comprobante al abordar el bus.")
    p.drawCentredString(ancho / 2, 20, "Transportes Centroamericanos S.A. | info@transcentro.com")

    p.showPage()
    p.save()
    buffer.seek(0)
    response = HttpResponse(buffer, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="tiquete-{tiquete.codigo}.pdf"'
    return response