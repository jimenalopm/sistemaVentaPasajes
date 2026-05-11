from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .forms import RegistroForm, LoginForm, TarjetaForm
from .models import Cliente, Tarjeta


def registro(request):
    if request.method == "POST":
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data["email"],
                email=form.cleaned_data["email"],
                password=form.cleaned_data["password1"],
            )
            Cliente.objects.create(
                user=user,
                nombre=form.cleaned_data["nombre"],
                apellido=form.cleaned_data["apellido"],
                pasaporte=form.cleaned_data["pasaporte"],
                nacionalidad=form.cleaned_data["nacionalidad"],
                telefono=form.cleaned_data["telefono"],
            )
            messages.success(request, "Cuenta creada!! Iniciá sesión")
            return redirect("usuarios:login")
    else:
        form = RegistroForm()

    return render(request, "usuarios/registro.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"¡Bienvenido de nuevo, {user.cliente.nombre}!")
            return redirect("rutas:inicio")
    else:
        form = LoginForm()

    return render(request, "usuarios/login.html", {"form": form})


def logout_view(request):
    logout(request)
    messages.info(request, "Cerraste sesión correctamente.")
    return redirect("rutas:inicio")


@login_required(login_url="/usuarios/login/")
def mis_tarjetas(request):
    cliente = request.user.cliente
    tarjetas = cliente.tarjetas.all().order_by("id")
    return render(request, "usuarios/mis_tarjetas.html", {"tarjetas": tarjetas})


@login_required(login_url="/usuarios/login/")
def agregar_tarjeta(request):
    cliente = request.user.cliente
    if request.method == "POST":
        form = TarjetaForm(request.POST)
        if form.is_valid():
            Tarjeta.objects.create(
                cliente=cliente,
                titular=form.cleaned_data["titular_tarjeta"],
                numero_tarjeta=form.cleaned_data["numero_tarjeta"],
                fecha_vencimiento=form.cleaned_data["fecha_vencimiento"],
                ccv=form.cleaned_data["ccv"],
                tipo=form.cleaned_data["tipo"],
            )
            messages.success(request, "Tarjeta agregada correctamente.")
            return redirect("usuarios:mis_tarjetas")
    else:
        form = TarjetaForm()

    return render(request, "usuarios/agregar_tarjeta.html", {"form": form})


@login_required(login_url="/usuarios/login/")
def eliminar_tarjeta(request, tarjeta_id):
    cliente = request.user.cliente
    tarjeta = get_object_or_404(Tarjeta, id=tarjeta_id, cliente=cliente)
    if request.method == "POST":
        try:
            tarjeta.delete()
            messages.success(request, "Tarjeta eliminada.")
        except Exception:
            messages.error(request, "No se puede eliminar: la tarjeta tiene tiquetes asociados.")
        return redirect("usuarios:mis_tarjetas")
    return redirect("usuarios:mis_tarjetas")
