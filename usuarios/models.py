from django.db import models
from django.contrib.auth.models import User


class Cliente(
    models.Model
):  # no usamos correo , contrasena y username con Django para poder despues utilizar funciones ya listas de Django
    user = models.OneToOneField(  # funcion para vincular 1 cliente a 1 user de django
        User,
        on_delete=models.CASCADE,
        related_name="cliente",  # permite despues poder usar request.user.cliente para acceder al perfil
    )
    nombre = models.CharField(max_length=50)
    apellido = models.CharField(max_length=50)
    pasaporte = models.CharField(max_length=20, unique=True)
    nacionalidad = models.CharField(max_length=50)
    telefono = models.CharField(max_length=20, null=True, blank=True)

    class Meta:
        db_table = "clientes"

    def __str__(self):
        return f"{self.nombre} {self.apellido} ({self.user.email})"


class Tarjeta(models.Model):
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        db_column="id_cliente",
        related_name="tarjetas",  # Permite cliente.tarjetas.all() para listar las tarjetas de un cliente.
    )
    numero_tarjeta = models.CharField(max_length=20, unique=True)
    ccv = models.CharField(max_length=4)
    fecha_vencimiento = models.DateField()
    titular = models.CharField(max_length=100)
    tipo = models.CharField(max_length=20)

    class Meta:
        db_table = "tarjetas"

    def __str__(self):
        return f"{self.tipo} - {self.numero_tarjeta} ({self.titular})"
