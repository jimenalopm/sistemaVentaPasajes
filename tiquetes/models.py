from django.db import models
from rutas.models import Ruta, Bus, Horario
from usuarios.models import Cliente, Tarjeta
# importaciones de las otras tablas para las FKs


class Tiquete(models.Model):
    horario = models.ForeignKey(
        Horario, on_delete=models.PROTECT, db_column="id_horario"
    )
    tarjeta = models.ForeignKey(
        Tarjeta, on_delete=models.PROTECT, db_column="id_tarjeta"
    )
    cliente = models.ForeignKey(
        Cliente, on_delete=models.PROTECT, db_column="id_cliente"
    )
    bus = models.ForeignKey(
        Bus,
        on_delete=models.PROTECT,
        to_field="placa",
        db_column="placa",  # to_field es para decirle directamente cuando no es la id default
    )
    codigo = models.CharField(max_length=30, unique=True)
    fecha_compra = models.DateTimeField(
        auto_now_add=True
    )  # auto_now_add es para poner la hora y fecha automaticamente
    fecha_salida = models.DateTimeField()
    monto_pagado = models.DecimalField(max_digits=8, decimal_places=2)
    estado = models.CharField(max_length=20, default="Activo")

    class Meta:
        db_table = "tiquetes"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(monto_pagado__gte=0),  # greater than or equal
                name="chk_tiquetes_monto_positivo",
            )
        ]

    def __str__(self):
        return f"{self.codigo} - {self.cliente} ({self.fecha_salida})"
