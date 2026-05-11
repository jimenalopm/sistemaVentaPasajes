from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta, datetime, date
import uuid

from .models import Tiquete
from rutas.models import Horario, Bus
from usuarios.models import Tarjeta


def _validar_tarjeta_nueva(post):
    """Valida los campos de una tarjeta nueva ingresada en el checkout.
    Devuelve (datos_dict, error_str). Si error_str es None, datos_dict es válido."""
    import re
    SOLO_LETRAS = re.compile(r"^[A-Za-zÁÉÍÓÚÑáéíóúñ\s]+$")

    titular = (post.get("titular_tarjeta") or "").strip()
    numero = (post.get("numero_tarjeta") or "").replace(" ", "")
    expiracion = (post.get("expiracion") or "").strip()
    ccv = (post.get("ccv_nueva") or "").strip()
    tipo = (post.get("tipo") or "").strip()

    if not (titular and numero and expiracion and ccv and tipo):
        return None, "Completá todos los datos de la tarjeta nueva."
    if not SOLO_LETRAS.match(titular):
        return None, "El nombre del titular solo puede contener letras."
    if not numero.isdigit() or not (13 <= len(numero) <= 19):
        return None, "El número de tarjeta debe tener entre 13 y 19 dígitos."
    if Tarjeta.objects.filter(numero_tarjeta=numero).exists():
        return None, "Esa tarjeta ya está registrada."
    if tipo not in ("Visa", "MasterCard", "American Express"):
        return None, "Tipo de tarjeta inválido."
    if not ccv.isdigit() or not (3 <= len(ccv) <= 4):
        return None, "El CCV debe tener 3 o 4 dígitos."

    try:
        mes, anio = expiracion.split("/")
        mes_int = int(mes)
        if not (1 <= mes_int <= 12):
            return None, "Mes de vencimiento inválido."
        fecha_exp = datetime.strptime(f"20{anio}-{mes}-01", "%Y-%m-%d").date()
        if fecha_exp < date.today().replace(day=1):
            return None, "La tarjeta ya está vencida."
    except (ValueError, AttributeError):
        return None, "Formato de vencimiento inválido. Usá MM/YY."

    return {
        "titular": titular,
        "numero_tarjeta": numero,
        "fecha_vencimiento": fecha_exp,
        "ccv": ccv,
        "tipo": tipo,
    }, None


@login_required(login_url="/usuarios/login/")
def comprar(request, horario_id):
    horario = get_object_or_404(Horario.objects.select_related("ruta"), id=horario_id)
    cliente = request.user.cliente

    tiquetes_actuales = Tiquete.objects.filter(cliente=cliente).count()
    disponibles = 5 - tiquetes_actuales
    if disponibles <= 0:
        messages.error(request, "No podés comprar más de 5 pasajes en total.")
        return redirect("rutas:lista_rutas")

    tarjetas = list(cliente.tarjetas.all().order_by("id"))

    hoy = timezone.now().date()
    fecha_min = hoy + timedelta(days=1)
    fecha_max = hoy + timedelta(days=7)

    if request.method == "POST":
        f_salida = request.POST.get("fecha_salida")
        cantidad_str = request.POST.get("cantidad")
        metodo = request.POST.get("metodo_pago")  # "existente" o "nueva"

        if not f_salida or not cantidad_str or not metodo:
            messages.error(request, "Todos los campos son obligatorios.")
            return redirect("tiquetes:comprar", horario_id=horario_id)

        try:
            cantidad = int(cantidad_str)
        except ValueError:
            messages.error(request, "Cantidad inválida.")
            return redirect("tiquetes:comprar", horario_id=horario_id)

        if cantidad < 1 or cantidad > disponibles:
            messages.error(request, f"Cantidad inválida. Podés comprar entre 1 y {disponibles} tiquete(s).")
            return redirect("tiquetes:comprar", horario_id=horario_id)

        try:
            dt_viaje = datetime.strptime(f_salida, "%Y-%m-%d").date()
        except ValueError:
            messages.error(request, "Fecha inválida.")
            return redirect("tiquetes:comprar", horario_id=horario_id)

        if dt_viaje < fecha_min or dt_viaje > fecha_max:
            messages.error(request, f"Fecha fuera de rango ({fecha_min} a {fecha_max}).")
            return redirect("tiquetes:comprar", horario_id=horario_id)

        tarjeta_para_pago = None

        if metodo == "existente":
            if not tarjetas:
                messages.error(request, "No tenés tarjetas registradas.")
                return redirect("tiquetes:comprar", horario_id=horario_id)

            tarjeta_id = request.POST.get("tarjeta_id")
            cvv_ingresado = (request.POST.get("cvv") or "").strip()
            if not tarjeta_id or not cvv_ingresado:
                messages.error(request, "Seleccioná una tarjeta e ingresá el CCV.")
                return redirect("tiquetes:comprar", horario_id=horario_id)

            try:
                tarjeta_para_pago = Tarjeta.objects.get(id=tarjeta_id, cliente=cliente)
            except Tarjeta.DoesNotExist:
                messages.error(request, "Tarjeta no válida.")
                return redirect("tiquetes:comprar", horario_id=horario_id)

            if cvv_ingresado != tarjeta_para_pago.ccv:
                messages.error(request, "CCV incorrecto.")
                return redirect("tiquetes:comprar", horario_id=horario_id)

        elif metodo == "nueva":
            datos, error = _validar_tarjeta_nueva(request.POST)
            if error:
                messages.error(request, error)
                return redirect("tiquetes:comprar", horario_id=horario_id)

            tarjeta_para_pago = Tarjeta.objects.create(
                cliente=cliente,
                titular=datos["titular"],
                numero_tarjeta=datos["numero_tarjeta"],
                fecha_vencimiento=datos["fecha_vencimiento"],
                ccv=datos["ccv"],
                tipo=datos["tipo"],
            )
        else:
            messages.error(request, "Método de pago inválido.")
            return redirect("tiquetes:comprar", horario_id=horario_id)

        bus = Bus.objects.filter(estado="Activo").first()
        codigos = []
        for _ in range(cantidad):
            codigo_ticket = f"{horario.ruta.codigo_ruta}-{str(uuid.uuid4()).upper()[:8]}"
            Tiquete.objects.create(
                horario=horario,
                tarjeta=tarjeta_para_pago,
                cliente=cliente,
                bus=bus,
                codigo=codigo_ticket,
                fecha_salida=timezone.make_aware(datetime.combine(dt_viaje, horario.hora_salida)),
                monto_pagado=horario.ruta.precio,
                estado="Activo",
            )
            codigos.append(codigo_ticket)

        if cantidad == 1:
            messages.success(request, f"¡Compra exitosa! Código: {codigos[0]}")
        else:
            messages.success(request, f"¡Compra exitosa! Se generaron {cantidad} tiquetes: {', '.join(codigos)}")
        return redirect("tiquetes:mis_tiquetes")

    return render(request, "tiquetes/comprar.html", {
        "horario": horario,
        "fecha_min": fecha_min,
        "fecha_max": fecha_max,
        "tarjetas": tarjetas,
        "tiene_tarjetas": bool(tarjetas),
        "disponibles": disponibles,
        "rango_cantidad": range(1, disponibles + 1),
    })


@login_required(login_url="/usuarios/login/")
def mis_tiquetes(request):
    cliente = request.user.cliente
    tiquetes = Tiquete.objects.filter(cliente=cliente).select_related(
        "horario__ruta", "bus", "tarjeta"
    ).order_by("-fecha_compra")

    return render(request, "tiquetes/mis_tiquetes.html", {
        "tiquetes": tiquetes,
    })


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
