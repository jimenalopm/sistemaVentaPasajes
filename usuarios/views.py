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
            # ... tu lógica de creación de User y Cliente que ya tienes ...
            # (Asegúrate de que el redirect esté aquí adentro)
            return redirect("rutas:inicio") 
        
        # Si NO es válido, el código saltará aquí y pasará al render de abajo
        messages.error(request, "Por favor corrija los errores en el formulario.")
    else:
        form = RegistroForm()

    # ESTA LÍNEA DEBE ESTAR FUERA DEL IF DEL POST
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