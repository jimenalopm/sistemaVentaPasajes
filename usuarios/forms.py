from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from .models import Cliente

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
        
        # 1. Validar Contraseñas
        p1 = cleaned_data.get("password1")
        p2 = cleaned_data.get("password2")
        if p1 and p2 and p1 != p2:
            self.add_error('password2', "Las contraseñas no coinciden.")

        # 2. Validar Correo Duplicado
        email = cleaned_data.get("email")
        if email and User.objects.filter(username=email).exists():
            self.add_error('email', "Este correo ya está registrado.")

        # 3. Validar Pasaporte Duplicado
        pasaporte = cleaned_data.get("pasaporte")
        if pasaporte and Cliente.objects.filter(pasaporte=pasaporte).exists():
            self.add_error('pasaporte', "Este número de pasaporte ya existe.")

        return cleaned_data

class LoginForm(AuthenticationForm):
    username = forms.EmailField(label="Correo electrónico", widget=forms.EmailInput(attrs={"class": "form-control"}))
    password = forms.CharField(label="Contraseña", widget=forms.PasswordInput(attrs={"class": "form-control"}))