from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from .forms import RegistroForm
from .models import Cliente


def registro(
    request,
):  # los views en Django responde a peticiones HTTP donde reciben un request(tiene toda la informacion)  y tiene dos metodos get para por ejemplo dame esta pagina y post cuando manda datos para procesarlos
    if request.method == "POST":  # si el usuario mando datos para procesar
        form = RegistroForm(
            request.POST
        )  # Creo un objeto formulario y le meto los datos del usuario para que después los pueda validar
        if form.is_valid():  #  Valida los campos segun las restricciones de la clase, despues llama a clean() para las validaciones extras, y retorna True si todo paso , ademas crea clean data dentro del objeto
            # Crear el User de Django
            user = User.objects.create_user(  # create_user hashea automaticamente
                username=form.cleaned_data["email"],
                email=form.cleaned_data["email"],
                password=form.cleaned_data["password1"],
            )
            # Crear el Cliente vinculado al User
            Cliente.objects.create(
                user=user,
                nombre=form.cleaned_data["nombre"],
                apellido=form.cleaned_data["apellido"],
                pasaporte=form.cleaned_data["pasaporte"],
                nacionalidad=form.cleaned_data["nacionalidad"],
                telefono=form.cleaned_data["telefono"],
            )
            messages.success(request, "Cuenta creada!! Iniciá sesión")
            return redirect(
                "usuarios:login"
            )  # si  se logra registrar lo redirige a el login
    else:  # si no mando datos entonces significa que no los lleno muestre el formulario
        form = RegistroForm()

    return render(
        request, "usuarios/registro.html", {"form": form}
    )  # si es la primera vez o si falla el registro muestra el formulario


def login_view(request):
    return render(request, "usuarios/login.html")


def logout_view(request):
    from django.http import HttpResponse

    return HttpResponse("logout - próximamente")
