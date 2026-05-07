from django.db import models


class Ruta(
    models.Model
):  # se usa models.model para que django sepa que estamos hablando de una tabla , ademas la PK en este caso ID se pone por dafault y ademas se autoincrementa , solo es necesaria ponerla si no es un id como por ejemplo en la buseta y placa
    lugar_salida = models.CharField(max_length=50)  # lugar_salida  VARCHAR(50) NOT NULL
    lugar_llegada = models.CharField(
        max_length=50
    )  # lugar_llegada = models.CharField(max_length=50)
    precio = models.DecimalField(
        max_digits=8, decimal_places=2
    )  # precio DECIMAL(8,2) NOT NULL
    codigo_ruta = models.CharField(
        max_length=20, unique=True
    )  # codigo_ruta VARCHAR(20) NOT NULL,CONSTRAINT uq_rutas_codigo UNIQUE (codigo_ruta)

    # en django el default es que no puede quedar vacio entonces no se pone nada para el not null por que es el default,  si queremos que pueda quedar null ahi si se tiene que poner como null=True

    class Meta:  # esto ers para dar instrucciones de comportamiento no son campos
        db_table = "rutas"  # para ponerle el nombre a la tabla

        models.CheckConstraint(
            condition=models.Q(
                precio__gte=0
            ),  # MODELS.Q se usa para poner condiciones, dentro se escribe el 'campo__condicion' en este caso gte significa greater than or equal
            name="chk_rutas_precio_positivo",  # el nombre que se le va a poner a la regla en Mysql
        )

    def __str__(self):  # funciona como un tostring no afecta en nada a la base de datos
        return f"{self.lugar_salida} -> {self.lugar_llegada} ({self.codigo_ruta})"


class Bus(models.Model):
    placa = models.CharField(
        max_length=10, primary_key=True
    )  # aqui como no es una id normal entonces si se pone
    modelo = models.CharField(max_length=50)
    capacidad = models.IntegerField()
    estado = models.CharField(max_length=20, default="Activo")

    class Meta:
        db_table = "buses"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(
                    capacidad__gt=0
                ),  # gt= greater than es como poner capacidad > 0
                name="chk_buses_capacidad_positiva",
            )
        ]

    def __str__(self):
        return f"{self.placa} - {self.modelo}"


class Horario(models.Model):
    ruta = models.ForeignKey(  # para poner las FK se llama a la clase directamente
        Ruta,
        on_delete=models.PROTECT,  # si tiene horarios asociados no lo deja y salta error
        db_column="id_ruta",
    )
    hora_salida = models.TimeField()

    class Meta:
        db_table = "horarios"

    def __str__(self):
        return f"{self.ruta.codigo_ruta} - {self.hora_salida}"
