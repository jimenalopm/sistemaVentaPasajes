import re
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from datetime import datetime, date
from .models import Cliente, Tarjeta

SOLO_LETRAS = re.compile(r"^[A-Za-zÁÉÍÓÚÑáéíóúñ\s]+$")
ALFANUMERICO = re.compile(r"^[A-Za-z0-9]+$")
TELEFONO_VALIDO = re.compile(r"^[0-9\s\-+]+$")


class RegistroForm(forms.Form):
    # Datos de la cuenta
    email = forms.EmailField(label="Correo electrónico")
    password1 = forms.CharField(label="Contraseña", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirmar contraseña", widget=forms.PasswordInput)

    # Datos personales
    nombre = forms.CharField(label="Nombre", max_length=50)
    apellido = forms.CharField(label="Apellidos", max_length=50)
    pasaporte = forms.CharField(label="Pasaporte", max_length=20)
    nacionalidad = forms.CharField(label="Nacionalidad", max_length=50)
    telefono = forms.CharField(label="Teléfono", max_length=20, required=False)

    def clean(self):
        cleaned_data = super().clean()

        p1 = cleaned_data.get("password1")
        p2 = cleaned_data.get("password2")
        if p1 and len(p1) < 8:
            self.add_error('password1', "La contraseña debe tener al menos 8 caracteres.")
        if p1 and p2 and p1 != p2:
            self.add_error('password2', "Las contraseñas no coinciden.")

        email = cleaned_data.get("email")
        if email and User.objects.filter(username=email).exists():
            self.add_error('email', "Este correo ya está registrado.")

        nombre = cleaned_data.get("nombre")
        if nombre and not SOLO_LETRAS.match(nombre):
            self.add_error('nombre', "El nombre solo puede contener letras.")

        apellido = cleaned_data.get("apellido")
        if apellido and not SOLO_LETRAS.match(apellido):
            self.add_error('apellido', "El apellido solo puede contener letras.")

        pasaporte = cleaned_data.get("pasaporte")
        if pasaporte and not ALFANUMERICO.match(pasaporte):
            self.add_error('pasaporte', "El pasaporte solo puede contener letras y números.")
        elif pasaporte and Cliente.objects.filter(pasaporte=pasaporte).exists():
            self.add_error('pasaporte', "Este número de pasaporte ya existe.")

        nacionalidad = cleaned_data.get("nacionalidad")
        if nacionalidad and not SOLO_LETRAS.match(nacionalidad):
            self.add_error('nacionalidad', "La nacionalidad solo puede contener letras.")

        telefono = cleaned_data.get("telefono")
        if telefono and not TELEFONO_VALIDO.match(telefono):
            self.add_error('telefono', "El teléfono solo puede contener números, espacios, + y -.")

        return cleaned_data


class TarjetaForm(forms.Form):
    """Formulario para registrar/usar una tarjeta. Compartido entre el checkout y la gestión de tarjetas."""
    TIPO_CHOICES = [
        ("Visa", "Visa"),
        ("MasterCard", "MasterCard"),
        ("American Express", "American Express"),
    ]

    titular_tarjeta = forms.CharField(label="Nombre en la tarjeta", max_length=100)
    numero_tarjeta = forms.CharField(label="Número de tarjeta", max_length=19)
    expiracion = forms.CharField(label="Vencimiento (MM/YY)", max_length=5)
    ccv = forms.CharField(label="CCV", max_length=4, widget=forms.PasswordInput)
    tipo = forms.ChoiceField(label="Tipo", choices=TIPO_CHOICES)

    def clean(self):
        cleaned_data = super().clean()

        titular = cleaned_data.get("titular_tarjeta")
        if titular and not SOLO_LETRAS.match(titular):
            self.add_error('titular_tarjeta', "El nombre del titular solo puede contener letras.")

        numero = (cleaned_data.get("numero_tarjeta") or "").replace(" ", "")
        if numero and (not numero.isdigit() or not (13 <= len(numero) <= 19)):
            self.add_error('numero_tarjeta', "El número de tarjeta solo puede contener dígitos (13-19).")
        elif numero and Tarjeta.objects.filter(numero_tarjeta=numero).exists():
            self.add_error('numero_tarjeta', "Esta tarjeta ya está registrada.")
        else:
            cleaned_data["numero_tarjeta"] = numero

        expiracion = cleaned_data.get("expiracion")
        if expiracion:
            try:
                mes, anio = expiracion.split("/")
                mes_int = int(mes)
                if not (1 <= mes_int <= 12):
                    self.add_error('expiracion', "El mes debe estar entre 01 y 12.")
                else:
                    fecha_exp = datetime.strptime(f"20{anio}-{mes}-01", "%Y-%m-%d").date()
                    hoy = date.today().replace(day=1)
                    if fecha_exp < hoy:
                        self.add_error('expiracion', "La tarjeta ya está vencida.")
                    else:
                        cleaned_data["fecha_vencimiento"] = fecha_exp
            except (ValueError, AttributeError):
                self.add_error('expiracion', "Formato inválido. Usá MM/YY.")

        ccv = cleaned_data.get("ccv")
        if ccv and (not ccv.isdigit() or not (3 <= len(ccv) <= 4)):
            self.add_error('ccv', "El CCV debe tener 3 o 4 dígitos.")

        return cleaned_data


class LoginForm(AuthenticationForm):
    username = forms.EmailField(label="Correo electrónico", widget=forms.EmailInput(attrs={"class": "form-control"}))
    password = forms.CharField(label="Contraseña", widget=forms.PasswordInput(attrs={"class": "form-control"}))
