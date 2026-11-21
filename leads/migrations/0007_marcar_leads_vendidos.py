from django.db import migrations


def marcar_vendidos(apps, schema_editor):
    """Marca como VENDIDO los leads existentes que ya tienen un plan de pago.

    Un lead se considera vendido cuando su acuerdo de pago tiene al menos un
    servicio contratado (AcuerdoPagoDetalle). Corrige los datos previos al
    cambio que escribe estado_venta segun el plan de pago.
    """
    Leads = apps.get_model('leads', 'Leads')
    AcuerdoPagoDetalle = apps.get_model('leads', 'AcuerdoPagoDetalle')
    acuerdos_con_servicio = set(
        AcuerdoPagoDetalle.objects.values_list('id_acuerdo_pago', flat=True)
    )
    if acuerdos_con_servicio:
        Leads.objects.filter(
            id_acuerdo_pago__in=acuerdos_con_servicio
        ).update(estado_venta='VENDIDO')


def revertir(apps, schema_editor):
    # No se revierte: no es posible distinguir cuales eran LEAD antes del cambio.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('leads', '0006_rename_cuotas_pagos'),
    ]

    operations = [
        migrations.RunPython(marcar_vendidos, revertir),
    ]
