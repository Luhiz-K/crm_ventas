from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from ..models import (Leads, Telefonos, UsuarioReporte, ReporteGrafico,
                      AcuerdoPagoDetalle, CuotaEstado, PagoRealizado, Observaciones)
from ..utils import trabajador_actual


def ver_lead(request, id_lead):
    lead = get_object_or_404(Leads, id_lead=id_lead)
    persona = lead.id_persona
    acuerdo = lead.id_acuerdo_pago

    # Agregar nota a la bitácora (única acción POST de esta vista)
    if request.method == 'POST':
        nueva = request.POST.get('nueva_observacion', '').strip()
        if nueva:
            Observaciones.objects.create(
                id_lead=lead, id_trabajador=trabajador_actual(request),
                observacion=nueva, fecha_registro=timezone.now())
        return redirect('ver_lead', id_lead=lead.id_lead)

    telefonos = Telefonos.objects.filter(id_persona=persona) if persona else []
    accesos = UsuarioReporte.objects.filter(id_lead=lead).select_related('id_buro')
    reportes = ReporteGrafico.objects.filter(id_lead=lead).select_related('id_buro')
    detalles = AcuerdoPagoDetalle.objects.filter(id_acuerdo_pago=acuerdo).select_related('id_servicio') if acuerdo else []
    historial_obs = Observaciones.objects.filter(id_lead=lead).select_related('id_trabajador__id_persona').order_by('-fecha_registro')

    # Plan de pagos: cada cuota con sus abonos, lo abonado y el saldo
    plan = []
    total_pagado = Decimal('0')
    if acuerdo:
        for c in CuotaEstado.objects.filter(id_acuerdo_pago=acuerdo).order_by('fecha_pago'):
            pagos = list(PagoRealizado.objects.filter(id_cuota=c)
                         .select_related('id_trabajador__id_persona')
                         .order_by('fecha_pago', 'fecha_registro'))
            abonado = sum((p.valor_pago for p in pagos), Decimal('0'))
            total_pagado += abonado
            plan.append({'cuota': c, 'pagos': pagos, 'abonado': abonado,
                         'saldo': c.valor_fecha_pago - abonado})
    deuda_pendiente = (acuerdo.valor_total_acuerdo_pago - total_pagado) if acuerdo else Decimal('0')

    return render(request, 'leads/ver_lead.html', {
        'lead': lead, 'persona': persona, 'acuerdo': acuerdo,
        'telefonos': telefonos, 'accesos': accesos, 'reportes': reportes,
        'detalles': detalles, 'plan': plan,
        'historial_obs': historial_obs,
        'total_pagado': total_pagado, 'deuda_pendiente': deuda_pendiente,
        'es_gerente': request.session.get('rol') == 'Gerente General',
    })
