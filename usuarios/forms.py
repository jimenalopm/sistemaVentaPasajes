from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from .models import Cliente


class RegistroForm(forms.Form):

    #Datos de la cuenta 
    email = forms.EmailField(
        label="Correo electrónico"
    )
    password1 = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput
    )
    password2 = forms.CharField(
        label="Confirmar contraseña",
        widget=forms.PasswordInput
    )

    # Datos personales 
    nombre = forms.CharField(label="Nombre", max_length=50)
    apellido = forms.CharField(label="Apellidos", max_length=50)
    pasaporte = forms.CharField(label="Pasaporte", max_length=20)
    nacionalidad = forms.CharField(label="Nacionalidad", max_length=50)
    telefono = forms.CharField(label="Teléfono", max_length=20, required=False)

    # Datos de la tarjeta 
    # El enunciado pide: Tarjeta, CCV y fecha de vencimiento
    numero_tarjeta = forms.CharField(
        label="Número de tarjeta",
        max_length=20,
        widget=forms.TextInput(attrs={"placeholder": "1234 5678 9012 3456"})
    )
    ccv = forms.CharField(
        label="CCV",
        max_length=4,
        widget=forms.TextInput(attrs={"placeholder": "123"})
    )
    fecha_vencimiento = forms.DateField(
        label="Fecha de vencimiento",
        widget=forms.DateInput(attrs={"type": "date"})
        # type=date hace que aparezca el selector de fecha en el navegador
    )
    titular_tarjeta = forms.CharField(
        label="Nombre del titular",
        max_length=100,
        widget=forms.TextInput(attrs={"placeholder": "Como aparece en la tarjeta"})
    )
    tipo_tarjeta = forms.ChoiceField(
        label="Tipo de tarjeta",
        choices=[
            ("", "-- Seleccioná --"),
            ("Visa", "Visa"),
            ("Mastercard", "Mastercard"),
            ("American Express", "American Express"),
        ]
    )

    # Validaciones extra 
    def clean(self):
        cleaned_data = super().clean()

        # Verificar que las contraseñas coincidan
        p1 = cleaned_data.get("password1")
        p2 = cleaned_data.get("password2")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Las contraseñas no coinciden.")

        # Verificar que el correo no esté ya registrado
        email = cleaned_data.get("email")
        if email and User.objects.filter(email=email).exists():
            raise forms.ValidationError("Este correo ya está registrado.")

        return cleaned_data


# Formulario de login 
class LoginForm(AuthenticationForm):
    username = forms.EmailField(
        label="Correo electrónico",
        widget=forms.EmailInput(attrs={"class": "form-control"})
    )
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={"class": "form-control"})
    )