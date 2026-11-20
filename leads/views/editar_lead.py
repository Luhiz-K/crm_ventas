"""Gestión de abonos de un lead y recálculo del estado de sus cuotas.

La edición integral del lead vive en el wizard; aquí quedan el registro y la
eliminación de abonos, más la redirección de la ruta antigua de edición.
"""

from datetime import date
from django.shortcuts import redirect, get_object_or_404
from django.db.models import Sum
from ..models import CuotaEstado, PagoRealizado
from ..utils import trabajador_actual


def editar_lead(request, id_lead):
    """Ruta heredada: redirige a la vista de detalle, que la reemplazó."""
    return redirect('ver_lead', id_lead=id_lead)


def _recalcular_estado_cuota(cuota):
    """Recalcula el estado de una cuota a partir de la suma de sus pagos realizados."""
    abonado = PagoRealizado.objects.filter(id_cuota=cuota).aggregate(s=Sum('valor_pago'))['s'] or 0
    valor = cuota.valor_fecha_pago
    if abonado <= 0:
        cuota.estado_pago = 'EN MORA' if (cuota.fecha_pago and cuota.fecha_pago < date.today()) else 'PENDIENTE'
    elif abonado < valor:
        cuota.estado_pago = 'PAGO PARCIAL'
    elif abonado == valor:
        cuota.estado_pago = 'PAGADA'
    else:
        cuota.estado_pago = 'SOBREPAGO'
    cuota.save()


def registrar_pago(request, id_fecha_pago):
    """Registra un NUEVO abono a una cuota (no sobrescribe) y recalcula su estado."""
    if request.method == 'POST':
        cuota = get_object_or_404(CuotaEstado, id_fecha_pago=id_fecha_pago)
        id_lead = request.POST.get('id_lead')
        valor = request.POST.get('valor_pago')
        fecha = request.POST.get('fecha_pago')
        try:
            valido = bool(valor and fecha and float(valor) > 0)
        except ValueError:
            valido = False
        if valido:
            PagoRealizado.objects.create(
                id_cuota=cuota, valor_pago=valor, fecha_pago=fecha,
                id_trabajador=trabajador_actual(request))
            _recalcular_estado_cuota(cuota)
        return redirect('ver_lead', id_lead=id_lead)
    return redirect('listar_leads')


def eliminar_pago(request, id_pago):
    """Solo el Gerente General puede eliminar un abono ya registrado."""
    if request.method == 'POST' and request.session.get('rol') == 'Gerente General':
        pago = get_object_or_404(PagoRealizado, id_pago=id_pago)
        cuota = pago.id_cuota
        id_lead = request.POST.get('id_lead')
        pago.delete()
        _recalcular_estado_cuota(cuota)
        return redirect('ver_lead', id_lead=id_lead)
    return redirect('listar_leads')
