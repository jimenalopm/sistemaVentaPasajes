from django.db import models


class Cliente(models.Model):
    nombre = models.CharField(max_length=50)
    apellido = models.CharField(max_length=50)
    pasaporte = models.CharField(max_length=20, unique=True)
    nacionalidad = models.CharField(max_length=50)
    correo = models.CharField(max_length=100, unique=True)
    telefono = models.CharField(
        max_length=20, null=True, blank=True
    )  # null=true es para la base de datos y blank=true es para los formularios de django
    contrasena = models.CharField(max_length=255)  # es mas grande para poder usar hash

    class Meta:
        db_table = "clientes"

    def __str__(self):
        return f"{self.nombre} {self.apellido} ({self.correo})"


class Tarjeta(models.Model):
    cliente = models.ForeignKey(
        Cliente, on_delete=models.CASCADE, db_column="id_cliente"
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
