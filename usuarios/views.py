from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from .forms import RegistroForm, LoginForm
from .models import Cliente, Tarjeta

def registro(request):
    if request.method == "POST":
        form = RegistroForm(request.POST)
        if form.is_valid():
            # Paso 1: Crear el User
            user = User.objects.create_user(
                username=form.cleaned_data["email"],
                email=form.cleaned_data["email"],
                password=form.cleaned_data["password1"],
            )

            # Paso 2: Crear el Cliente
            cliente = Cliente.objects.create(
                user=user,
                nombre=form.cleaned_data["nombre"],
                apellido=form.cleaned_data["apellido"],
                pasaporte=form.cleaned_data["pasaporte"],
                nacionalidad=form.cleaned_data["nacionalidad"],
                telefono=form.cleaned_data["telefono"],
            )

            # Paso 3: Crear la Tarjeta
            Tarjeta.objects.create(
                cliente=cliente,
                numero_tarjeta=form.cleaned_data["numero_tarjeta"],
                ccv=form.cleaned_data["ccv"],
                fecha_vencimiento=form.cleaned_data["fecha_vencimiento"],
                titular=form.cleaned_data["titular_tarjeta"],
                tipo=form.cleaned_data["tipo_tarjeta"],
            )

            messages.success(request, "¡Cuenta creada exitosamente! Ya puedes navegar.")
            
            # CAMBIO AQUÍ: Logueamos al usuario de una vez y lo mandamos al INICIO
            login(request, user)
            return redirect("rutas:inicio") 

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
            
            # CAMBIO AQUÍ: Redirigir a tu diseño de inicio
            return redirect("rutas:inicio")
    else:
        form = LoginForm()

    return render(request, "usuarios/login.html", {"form": form})


def logout_view(request):
    logout(request)
    messages.info(request, "Cerraste sesión correctamente.")
    
    # CAMBIO AQUÍ: Al salir, que vuelva a tu diseño de inicio
    return redirect("rutas:inicio")