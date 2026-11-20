# borrar_todo.py — PROTOCOLO DE BORRADO
# Deja la base en 0 (borra todo lo transaccional y de catalogo salvo ROL y CARGO).
# Ejecutar:  python manage.py shell -c "exec(open('borrar_todo.py', encoding='utf-8').read())"

from django.db import connection, transaction
from leads.models import (
    FechasPago, AcuerdoPagoDetalle, AcuerdoPago, Observaciones, ReporteGrafico,
    UsuarioReporte, DocumentosLead, Leads, Telefonos, Usuario, Trabajador,
    Sede, Persona, Ciudad, Servicios, MotivoContrato
)

with transaction.atomic():
    # Borramos de HIJOS a PADRES para no romper llaves foraneas
    FechasPago.objects.all().delete()
    AcuerdoPagoDetalle.objects.all().delete()
    Observaciones.objects.all().delete()
    ReporteGrafico.objects.all().delete()
    UsuarioReporte.objects.all().delete()
    DocumentosLead.objects.all().delete()
    Leads.objects.all().delete()
    AcuerdoPago.objects.all().delete()
    Telefonos.objects.all().delete()
    Usuario.objects.all().delete()
    Trabajador.objects.all().delete()
    Sede.objects.all().delete()
    Servicios.objects.all().delete()
    MotivoContrato.objects.all().delete()
    Persona.objects.all().delete()
    Ciudad.objects.all().delete()

# Reseteamos los contadores (secuencias) para que los IDs vuelvan a empezar en 1
secuencias = {
    'ciudad': 'id_ciudad', 'persona': 'id_persona', 'sede': 'id_sede',
    'trabajador': 'id_trabajador', 'usuario': 'id_usuario', 'telefonos': 'id_telefono',
    'leads': 'id_lead', 'observaciones': 'id_observaciones', 'acuerdo_pago': 'id_acuerdo_pago',
    'acuerdo_pago_detalle': 'id_detalle', 'fechas_pago': 'id_fecha_pago',
    'reporte_grafico': 'id_reporte_grafico', 'usuario_reporte': 'id_reporte',
    'documentos_lead': 'id_documento', 'servicios': 'id_servicio', 'motivo_contrato': 'id_contrato',
}
with connection.cursor() as cur:
    for tabla, col in secuencias.items():
        cur.execute(f"SELECT setval(pg_get_serial_sequence('{tabla}', '{col}'), 1, false)")

print('BORRADO COMPLETO. La base quedo en 0 (se conservaron ROL y CARGO).')
