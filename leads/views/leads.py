"""Listado de leads y detalle en JSON para el panel de vista rápida.

Incluye el alcance por rol (el Gerente ve todos; el asesor solo los suyos),
filtros, métricas, paginación ajustable y el endpoint de detalle del preview.
"""

from datetime import date
from django.shortcuts import render
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum
from ..models import Leads, Usuario, Trabajador, AcuerdoPagoDetalle, CuotaEstado, PagoRealizado, Telefonos, Observaciones
from ..utils import es_sistema_operativo


def _leads_segun_rol(request):
    """Queryset base segun el rol: Gerente General ve todos; el resto, solo los suyos."""
    base = Leads.objects.select_related(
        'id_persona', 'id_trabajador', 'id_trabajador__id_persona', 'id_trabajador__id_sede'
    )
    if request.session.get('rol') == 'Gerente General':
        return base
    try:
        usuario = Usuario.objects.get(id_usuario=request.session.get('id_usuario'))
        trabajador = Trabajador.objects.filter(id_persona=usuario.id_persona).first()
    except Usuario.DoesNotExist:
        trabajador = None
    return base.filter(id_trabajador=trabajador) if trabajador else base.none()


def listar_leads(request):
    base_rol = _leads_segun_rol(request)

    # ---- Filtros ----
    q = request.GET.get('q', '').strip()
    estado = request.GET.get('estado', '').strip()
    estado_venta = request.GET.get('estado_venta', '').strip()
    rango = request.GET.get('rango', '').strip()
    fecha = request.GET.get('fecha', '').strip()

    leads = base_rol
    if q:
        filtro = (
            Q(id_persona__nombres__icontains=q) |
            Q(id_persona__apellidos__icontains=q) |
            Q(id_persona__numero_documento_persona__icontains=q) |
            Q(telefono_marcado__icontains=q)
        )
        if q.isdigit():
            filtro |= Q(id_lead=int(q))
        leads = leads.filter(filtro)
    if estado:
        leads = leads.filter(estado_lead=estado)
    if estado_venta:
        leads = leads.filter(estado_venta=estado_venta)
    if rango == 'hoy':
        leads = leads.filter(fecha_creacion=date.today())
    elif fecha:
        leads = leads.filter(fecha_creacion=fecha)

    # ---- Metricas: una version GENERAL (todo el alcance) y otra FILTRADA (lo que se ve) ----
    def _resumen(qs):
        return {
            'total': qs.count(),
            'por_estado': list(qs.order_by().values('estado_lead').annotate(n=Count('id_lead')).order_by('-n')),
        }
    general = _resumen(base_rol)
    filtrado = _resumen(leads)
    hoy = base_rol.filter(fecha_creacion=date.today()).count()
    estados = list(base_rol.order_by().values_list('estado_lead', flat=True).distinct())
    estados_venta = list(base_rol.order_by().values_list('estado_venta', flat=True).distinct())

    # ---- Paginacion con tamano ajustable (persistente en sesion) ----
    per_page_param = request.GET.get('per_page')
    if per_page_param in ('20', '50', '100'):
        request.session['leads_per_page'] = int(per_page_param)
    per_page = request.session.get('leads_per_page', 20)
    page_obj = Paginator(
        leads.order_by('-fecha_creacion', '-hora_creacion'), per_page
    ).get_page(request.GET.get('page'))
    # querystring base para los enlaces de paginacion (conserva filtros, quita page)
    params = request.GET.copy()
    params.pop('page', None)

    contexto = {
        'leads': page_obj,
        'page_obj': page_obj,
        'per_page': per_page,
        'qs_base': params.urlencode(),
        'puede_crear': es_sistema_operativo(),
        'hoy': hoy,
        'total_general': general['total'],
        'total_filtrado': filtrado['total'],
        'porestado_general': general['por_estado'],
        'porestado_filtrado': filtrado['por_estado'],
        'estados': estados,
        'estados_venta': estados_venta,
        'f_q': q, 'f_estado': estado, 'f_estado_venta': estado_venta,
        'f_rango': rango, 'f_fecha': fecha,
    }
    return render(request, 'leads/listar_leads.html', contexto)


def detalle_lead(request, id_lead):
    """Devuelve en JSON el detalle de un lead, respetando el alcance por rol."""
    base = _leads_segun_rol(request)
    lead = base.select_related('id_acuerdo_pago').filter(id_lead=id_lead).first()
    if not lead:
        return JsonResponse({'error': 'No encontrado o sin permiso'}, status=404)

    persona = lead.id_persona
    trab = lead.id_trabajador
    sede = trab.id_sede.nombre_sede if trab and trab.id_sede else '—'
    asesor = (f"{trab.id_persona.nombres} {trab.id_persona.apellidos}"
              if trab and trab.id_persona else '—')

    telefonos_extra = []
    if persona:
        for t in Telefonos.objects.filter(id_persona=persona).exclude(numero_telefono=lead.telefono_marcado):
            telefonos_extra.append(t.numero_telefono)

    servicios, valor_total = [], None
    proximo, en_mora, monto_mora = None, False, 0.0

    if lead.id_acuerdo_pago:
        valor_total = float(lead.id_acuerdo_pago.valor_total_acuerdo_pago)
        for det in AcuerdoPagoDetalle.objects.filter(
                id_acuerdo_pago=lead.id_acuerdo_pago).select_related('id_servicio'):
            servicios.append({'nombre': det.id_servicio.nombre_servicio,
                              'valor': float(det.valor_cobrado)})
        hoy = date.today()
        for c in CuotaEstado.objects.filter(id_acuerdo_pago=lead.id_acuerdo_pago).order_by('fecha_pago'):
            abonado = float(PagoRealizado.objects.filter(id_cuota=c).aggregate(s=Sum('valor_pago'))['s'] or 0)
            saldo = float(c.valor_fecha_pago) - abonado
            if saldo > 0:
                if proximo is None:
                    proximo = {'fecha': str(c.fecha_pago), 'valor': float(c.valor_fecha_pago)}
                if c.fecha_pago and c.fecha_pago < hoy:
                    en_mora = True
                    monto_mora += saldo

    # ---- Notas de bitacora (mas reciente primero) para el recuadro del preview ----
    notas = []
    for o in Observaciones.objects.filter(id_lead=lead).select_related(
            'id_trabajador__id_persona').order_by('-fecha_registro')[:50]:
        if o.id_trabajador and o.id_trabajador.id_persona:
            autor = f"{o.id_trabajador.id_persona.nombres} {o.id_trabajador.id_persona.apellidos}"
        else:
            autor = 'Sistema'
        notas.append({
            'texto': o.observacion,
            'autor': autor,
            'fecha': o.fecha_registro.strftime('%Y-%m-%d %H:%M') if o.fecha_registro else '',
        })

    return JsonResponse({
        'id': lead.id_lead,
        'nombre': f"{persona.nombres} {persona.apellidos}" if persona else '—',
        'documento': (persona.numero_documento_persona if persona else '') or '—',
        'telefono': lead.telefono_marcado or '—',
        'telefonos_adicionales': telefonos_extra,
        'estado': lead.estado_lead,
        'estado_venta': lead.estado_venta,
        'fecha': f"{lead.fecha_creacion} {lead.hora_creacion or ''}".strip(),
        'sede': sede,
        'asesor': asesor,
        'servicios': servicios,
        'valor_total': valor_total,
        'proximo': proximo,
        'en_mora': en_mora,
        'monto_mora': round(monto_mora, 2),
        'notas': notas,
    })
