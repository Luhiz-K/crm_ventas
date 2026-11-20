"""Modelos de datos del CRM DeuDoor.

Define las tablas del dominio: personas y usuarios, estructura organizacional
(sedes, trabajadores, roles y cargos), leads y su trazabilidad (observaciones,
documentos, reportes) y el esquema de cobro (acuerdos de pago, servicios
contratados, cuotas y abonos realizados).
"""

from django.db import models


class AcuerdoPago(models.Model):
    """Acuerdo de pago de un lead: monto total pactado y observaciones."""
    id_acuerdo_pago = models.AutoField(primary_key=True)
    valor_total_acuerdo_pago = models.DecimalField(max_digits=15, decimal_places=2)
    observaciones_acuerdo_pago = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'acuerdo_pago'


class Cargo(models.Model):
    """Catálogo de cargos que puede ocupar un trabajador."""
    id_cargo = models.AutoField(primary_key=True)
    nombre_cargo = models.CharField(unique=True, max_length=100)
    descripcion_cargo = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'cargo'


class Ciudad(models.Model):
    """Catálogo de ciudades usado en direcciones de personas."""
    id_ciudad = models.AutoField(primary_key=True)
    ciudad = models.CharField(unique=True, max_length=100)

    def __str__(self):
        return self.ciudad

    class Meta:
        db_table = 'ciudad'


class CuotaEstado(models.Model):
    """Cuota de un acuerdo de pago: valor pactado, fecha de vencimiento y estado.

    El estado (PENDIENTE/EN MORA/PAGO PARCIAL/PAGADA/SOBREPAGO) se recalcula a
    partir de la suma de los PagoRealizado asociados a la cuota.
    """
    id_fecha_pago = models.AutoField(primary_key=True)
    id_acuerdo_pago = models.ForeignKey(AcuerdoPago, models.DO_NOTHING, db_column='id_acuerdo_pago')
    valor_fecha_pago = models.DecimalField(max_digits=15, decimal_places=2)
    fecha_pago = models.DateField()
    estado_pago = models.CharField(max_length=25, blank=True, null=True)

    class Meta:
        db_table = 'cuotas_estados'


class PagoRealizado(models.Model):
    """Abono real aplicado a una cuota. Una cuota puede recibir varios abonos."""
    id_pago = models.AutoField(primary_key=True)
    id_cuota = models.ForeignKey(CuotaEstado, models.CASCADE, db_column='id_cuota')
    valor_pago = models.DecimalField(max_digits=15, decimal_places=2)
    fecha_pago = models.DateField()
    id_trabajador = models.ForeignKey('Trabajador', models.DO_NOTHING, db_column='id_trabajador', null=True, blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'pagos_realizados'


class MotivoContrato(models.Model):
    """Catálogo de motivos por los que se genera un contrato/lead."""
    id_contrato = models.AutoField(primary_key=True)
    motivo_contrato = models.CharField(unique=True, max_length=200)

    class Meta:
        db_table = 'motivo_contrato'


class Persona(models.Model):
    """Datos personales de un individuo (cliente, trabajador o responsable)."""
    id_persona = models.AutoField(primary_key=True)
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    tipo_documento_persona = models.CharField(max_length=5, blank=True, null=True)
    numero_documento_persona = models.CharField(unique=True, max_length=20, blank=True, null=True)
    fecha_expedicion_persona = models.DateField(blank=True, null=True)
    fecha_nacimiento_persona = models.DateField(blank=True, null=True)
    genero_persona = models.CharField(max_length=20, blank=True, null=True)
    correo_persona = models.CharField(max_length=100, blank=True, null=True)
    direccion_persona = models.CharField(max_length=150, blank=True, null=True)
    complemento_persona = models.CharField(max_length=100, blank=True, null=True)
    barrio_persona = models.CharField(max_length=100, blank=True, null=True)
    id_ciudad = models.ForeignKey(Ciudad, models.DO_NOTHING, db_column='id_ciudad', blank=True, null=True)

    class Meta:
        db_table = 'persona'


class Sede(models.Model):
    """Sede u oficina a la que pertenecen los trabajadores."""
    id_sede = models.AutoField(primary_key=True)
    nombre_sede = models.CharField(max_length=100)
    direccion_sede = models.CharField(max_length=150, blank=True, null=True)
    id_responsable = models.ForeignKey(Persona, models.DO_NOTHING, db_column='id_responsable', blank=True, null=True)
    correo_sede = models.CharField(max_length=100, blank=True, null=True)
    telefono_sede = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        db_table = 'sede'


class Trabajador(models.Model):
    """Empleado del sistema: vincula una persona con su sede y su cargo."""
    id_trabajador = models.AutoField(primary_key=True)
    id_persona = models.OneToOneField(Persona, models.DO_NOTHING, db_column='id_persona')
    id_sede = models.ForeignKey(Sede, models.DO_NOTHING, db_column='id_sede', blank=True, null=True)
    id_cargo = models.ForeignKey(Cargo, models.DO_NOTHING, db_column='id_cargo', blank=True, null=True)

    class Meta:
        db_table = 'trabajador'


class Leads(models.Model):
    """Lead (prospecto/cliente) gestionado por un trabajador.

    Centraliza al cliente, el trabajador responsable, el motivo del contrato y
    el acuerdo de pago. 'estado_lead' refleja la etapa de gestión y
    'estado_venta' el ciclo comercial (LEAD / VENDIDO / FINALIZADO).
    """
    id_lead = models.AutoField(primary_key=True)
    id_persona = models.ForeignKey(Persona, models.DO_NOTHING, db_column='id_persona', null=True, blank=True)
    id_trabajador = models.ForeignKey(Trabajador, models.DO_NOTHING, db_column='id_trabajador')
    id_contrato = models.ForeignKey(MotivoContrato, models.DO_NOTHING, db_column='id_contrato', null=True, blank=True)
    id_acuerdo_pago = models.ForeignKey(AcuerdoPago, models.DO_NOTHING, db_column='id_acuerdo_pago', null=True, blank=True)
    estado_lead = models.CharField(max_length=20, default='NUEVO')
    estado_venta = models.CharField(max_length=20, default='LEAD')  # LEAD / VENDIDO / FINALIZADO
    telefono_marcado = models.CharField(max_length=20, null=True, blank=True)
    fecha_creacion = models.DateField(auto_now_add=True, null=True)
    hora_creacion = models.TimeField(auto_now_add=True, null=True)

    class Meta:
        db_table = 'leads'


class Observaciones(models.Model):
    """Anotación de la bitácora de un lead, registrada por un trabajador."""
    id_observaciones = models.AutoField(primary_key=True)
    id_lead = models.ForeignKey(Leads, models.DO_NOTHING, db_column='id_lead')
    id_trabajador = models.ForeignKey(Trabajador, models.DO_NOTHING, db_column='id_trabajador', blank=True, null=True)
    observacion = models.TextField()
    motivo_finalizacion_llamada = models.CharField(max_length=200, blank=True, null=True)
    estado_llamada = models.CharField(max_length=50, blank=True, null=True)
    fecha_registro = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'observaciones'


class Buro(models.Model):
    """Buró de crédito contra el que se consultan reportes (ACTIVO / INACTIVO)."""
    id_buro = models.AutoField(primary_key=True)
    nombre_buro = models.CharField(unique=True, max_length=100)
    estado = models.CharField(max_length=20, default='ACTIVO')  # ACTIVO / INACTIVO

    class Meta:
        db_table = 'buro'

    def __str__(self):
        return self.nombre_buro


class ReporteGrafico(models.Model):
    """Archivo de reporte (imagen/PDF) de un buró, asociado a un lead."""
    id_reporte_grafico = models.AutoField(primary_key=True)
    id_lead = models.ForeignKey(Leads, models.DO_NOTHING, db_column='id_lead')
    id_buro = models.ForeignKey(Buro, models.DO_NOTHING, db_column='id_buro', null=True, blank=True)
    documento_reporte_grafico = models.FileField(upload_to='reportes_plataformas/', max_length=255, blank=True, null=True)
    tipo_reporte_grafico = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        db_table = 'reporte_grafico'


class Rol(models.Model):
    """Catálogo de roles que determinan los permisos de un usuario."""
    id_rol = models.AutoField(primary_key=True)
    nombre_rol = models.CharField(unique=True, max_length=100)
    descripcion_rol = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'rol'


class Telefonos(models.Model):
    """Teléfono de contacto asociado a una persona."""
    id_telefono = models.AutoField(primary_key=True)
    numero_telefono = models.CharField(max_length=20)
    tipo_telefono = models.CharField(max_length=20, blank=True, null=True)
    id_persona = models.ForeignKey(Persona, models.DO_NOTHING, db_column='id_persona')

    class Meta:
        db_table = 'telefonos'


class Usuario(models.Model):
    """Cuenta de acceso al sistema: credenciales y rol de una persona."""
    id_usuario = models.AutoField(primary_key=True)
    id_persona = models.ForeignKey(Persona, models.DO_NOTHING, db_column='id_persona')
    id_rol = models.ForeignKey(Rol, models.DO_NOTHING, db_column='id_rol')
    username = models.CharField(unique=True, max_length=50)
    password_hash = models.CharField(max_length=255)
    estado_usuario = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        db_table = 'usuario'


class UsuarioReporte(models.Model):
    """Credenciales de acceso a la plataforma de un buró para un lead."""
    id_reporte = models.AutoField(primary_key=True)
    id_lead = models.ForeignKey(Leads, models.DO_NOTHING, db_column='id_lead')
    id_buro = models.ForeignKey(Buro, models.DO_NOTHING, db_column='id_buro', null=True, blank=True)
    usuario_reporte = models.CharField(max_length=100, blank=True, null=True)
    password_reporte = models.CharField(max_length=100, blank=True, null=True)
    plataforma_reporte = models.CharField(max_length=100, blank=True, null=True)
    descripcion_reporte = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'usuario_reporte'


class DocumentosLead(models.Model):
    """Documento adjunto a un lead (cédula, contrato, reporte, u otro)."""
    id_documento = models.AutoField(primary_key=True)
    id_lead = models.ForeignKey(Leads, on_delete=models.CASCADE, db_column='id_lead')
    TIPO_DOC_CHOICES = [
        ('CEDULA', 'Documento de Identidad'),
        ('CONTRATO', 'Contrato Firmado'),
        ('REPORTE', 'Reporte de Crédito'),
        ('OTRO', 'Otro Documento')
    ]
    tipo_documento = models.CharField(max_length=50, choices=TIPO_DOC_CHOICES)
    archivo = models.FileField(upload_to='documentos_clientes/')
    descripcion = models.TextField(blank=True, null=True)
    fecha_subida = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'documentos_lead'


class Servicios(models.Model):
    """Catálogo de servicios con su banda de precios (mínimo, ideal, máximo)."""
    id_servicio = models.AutoField(primary_key=True)
    nombre_servicio = models.CharField(max_length=150)
    precio_minimo = models.DecimalField(max_digits=15, decimal_places=2)
    precio_maximo = models.DecimalField(max_digits=15, decimal_places=2)
    precio_ideal = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    estado = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        db_table = 'servicios'

    def __str__(self):
        return f"{self.nombre_servicio} (${self.precio_minimo} - ${self.precio_maximo})"


class AcuerdoPagoDetalle(models.Model):
    """Servicio concreto contratado dentro de un acuerdo y su valor cobrado."""
    id_detalle = models.AutoField(primary_key=True)
    id_acuerdo_pago = models.ForeignKey(AcuerdoPago, models.DO_NOTHING, db_column='id_acuerdo_pago')
    id_servicio = models.ForeignKey(Servicios, models.DO_NOTHING, db_column='id_servicio')
    valor_cobrado = models.DecimalField(max_digits=15, decimal_places=2)

    class Meta:
        db_table = 'acuerdo_pago_detalle'
