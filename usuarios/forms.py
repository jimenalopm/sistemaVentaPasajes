from django import forms
from django.contrib.auth.models import User
from .models import Cliente


class RegistroForm(
    forms.Form
):  # los formularios tienen que ir con forms.forma asi Django ya sabe que es un formulario y agrega funcionalidades
    # Datos del User
    email = forms.EmailField(
        label="Correo electrónico"
    )  # emailfield hace q se haga la verificacion de que si tenga lo necesario para ser un email
    password1 = forms.CharField(
        label="Contraseña", widget=forms.PasswordInput
    )  # widget=forms.PasswordInput para que no se vea la contrasena al escribirla
    password2 = forms.CharField(
        label="Confirmar contraseña", widget=forms.PasswordInput
    )

    # Datos del Cliente
    nombre = forms.CharField(label="Nombre", max_length=50)
    apellido = forms.CharField(label="Apellido", max_length=50)
    pasaporte = forms.CharField(label="Pasaporte", max_length=20)
    nacionalidad = forms.CharField(label="Nacionalidad", max_length=50)
    telefono = forms.CharField(
        label="Teléfono", max_length=20, required=False
    )  # todos se verifica q no se pase del tamano maximo de la DB y en telefono permite q lo pueda mandar sin esto como en la db

    def clean(self):
        cleaned_data = super().clean()  # esta funcion devuelve el diccionario si la validacion fue correcta, la que hace la validacion con las restricciones de arriba es la funcion valid que esta en view
        p1 = cleaned_data.get("password1")
        p2 = cleaned_data.get(
            "password2"
        )  # sacamos las dos contrasenas del diccionario para poder usarlas abajo

        # Validar que las contraseñas coincidan
        if (
            p1 and p2 and p1 != p2
        ):  # p1 tiene valor ? and p2 tiene valor ?  esto para que no dar 2 errores por que si esta vacio le va a dar el de que no puede estar vacio , despues se verifica si son iguales y si no lo son se lo dice
            raise forms.ValidationError(
                "Las contraseñas no coinciden"
            )  # raise lanza una excepcion y detiene la ejecucion  mostrando el mensaje del error, form.validationerror funciona bien con Django y muestra el mensaje de error de mejor forma

        email = cleaned_data.get("email")  # saca el email del diccionario para usarlo

        if (
            email and User.objects.filter(email=email).exists()
        ):  # primero verifica si no esta vacio para ni siquiera buscar,  y la otra funcion es una que trae Django para buscar si existe algun email igual
            raise forms.ValidationError("Este correo ya está registrado")

        return cleaned_data  # si no existieron errores se pasa a la parte de views aqui nada mas se hacen comprobaciones de que la informacion este bien
