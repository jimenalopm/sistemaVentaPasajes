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

            #Paso 1: Crear el User de Django 
            # create_user hashea la contraseña automáticamente, nunca se guarda en texto plano
            user = User.objects.create_user(
                username=form.cleaned_data["email"],
                email=form.cleaned_data["email"],
                password=form.cleaned_data["password1"],
            )

            #  Paso 2: Crear el Cliente vinculado al User 
            cliente = Cliente.objects.create(
                user=user,
                nombre=form.cleaned_data["nombre"],
                apellido=form.cleaned_data["apellido"],
                pasaporte=form.cleaned_data["pasaporte"],
                nacionalidad=form.cleaned_data["nacionalidad"],
                telefono=form.cleaned_data["telefono"],
            )

            #  Paso 3: Crear la Tarjeta vinculada al Cliente 
            # Aquí es lo nuevo: guardamos la tarjeta en la misma operación del registro
            Tarjeta.objects.create(
                cliente=cliente,
                numero_tarjeta=form.cleaned_data["numero_tarjeta"],
                ccv=form.cleaned_data["ccv"],
                fecha_vencimiento=form.cleaned_data["fecha_vencimiento"],
                titular=form.cleaned_data["titular_tarjeta"],
                tipo=form.cleaned_data["tipo_tarjeta"],
            )

            messages.success(request, "¡Cuenta creada exitosamente! Iniciá sesión.")
            return redirect("usuarios:login")

    else:
        # Si el usuario apenas abre la página, mostramos el formulario vacío
        form = RegistroForm()

    return render(request, "usuarios/registro.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)  # esto crea la sesión en el navegador
            messages.success(request, f"¡Bienvenido de nuevo, {user.cliente.nombre}!")
            return redirect("rutas:lista_rutas")
    else:
        form = LoginForm()

    return render(request, "usuarios/login.html", {"form": form})


def logout_view(request):
    logout(request)  # elimina la sesión
    messages.info(request, "Cerraste sesión correctamente.")
    return redirect("/")