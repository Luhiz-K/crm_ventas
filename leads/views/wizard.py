"""Asistente de captura y edición de leads (wizard de 4 pasos).

Gestiona el flujo Persona -> Plataformas -> Plan de pago -> Resumen sobre un
borrador en sesión y persiste todo en una sola transacción. Incluye el modo
edición, con restricciones según el rol del usuario.
"""

import os
import uuid
from datetime import date
from decimal import Decimal, InvalidOperation
from django.conf import settings
from django.contrib import messages
from django.core.files import File
from django.db import transaction
from django.utils import timezone
from django.shortcuts import render, redirect
from ..forms.wizard import WizardPersonaForm
from ..models import (Persona, Ciudad, Buro, Servicios, Telefonos, Leads,
                      UsuarioReporte, AcuerdoPago, AcuerdoPagoDetalle, CuotaEstado,
                      PagoRealizado, ReporteGrafico, Observaciones, MotivoContrato)
from ..utils import trabajador_actual

TMP_REPORTES = 'tmp_wizard_reportes'

# Roles con edición total del lead (ampliable añadiendo roles al conjunto).
ROLES_EDICION_TOTAL = {'Gerente General'}


def _edicion_total(request):
    return request.session.get('rol', '') in ROLES_EDICION_TOTAL

PASOS = [
    (1, 'Persona', 'bi-person-vcard'),
    (2, 'Plataformas', 'bi-file-earmark-bar-graph'),
    (3, 'Plan de pago', 'bi-cash-coin'),
    (4, 'Resumen', 'bi-check2-circle'),
]

PERSONA_FIELDS = [
    'nombres', 'apellidos', 'fecha_expedicion_persona', 'fecha_nacimiento_persona',
    'genero_persona', 'correo_persona', 'direccion_persona', 'complemento_persona',
    'barrio_persona', 'id_ciudad', 'telefono_adicional_1', 'telefono_adicional_2', 'telefono_adicional_3',
]


def _persona_form(request, borrador, bound):
    if bound:
        form = WizardPersonaForm(request.POST)
    else:
        inicial = dict(borrador.get('persona') or {})
        if not inicial and borrador.get('reusar'):
            p = Persona.objects.filter(id_persona=borrador['reusar']).first()
            if p:
                inicial = {
                    'nombres': p.nombres, 'apellidos': p.apellidos,
                    'fecha_expedicion_persona': p.fecha_expedicion_persona,
                    'fecha_nacimiento_persona': p.fecha_nacimiento_persona,
                    'genero_persona': p.genero_persona, 'correo_persona': p.correo_persona,
                    'direccion_persona': p.direccion_persona, 'complemento_persona': p.complemento_persona,
                    'barrio_persona': p.barrio_persona, 'id_ciudad': p.id_ciudad_id,
                }
        form = WizardPersonaForm(initial=inicial)
    # En edición, el asesor NO puede cambiar nombres/apellidos (solo el Gerente)
    if borrador.get('editando') and not _edicion_total(request):
        for f in ('nombres', 'apellidos'):
            form.fields[f].widget.attrs['readonly'] = True
            form.fields[f].widget.attrs['class'] = (form.fields[f].widget.attrs.get('class', '') + ' bg-light').strip()
    return form


def _identificadores(borrador):
    """Construye los ítems del encabezado del lead según el avance del borrador."""
    items = [
        {'label': 'Teléfono', 'valor': borrador.get('telefono', ''), 'lock': False},
        {'label': 'Tipo doc.', 'valor': borrador.get('tipo_documento', ''), 'lock': False},
        {'label': 'Documento', 'valor': borrador.get('documento', ''), 'lock': True},
    ]
    p = borrador.get('persona') or {}
    if p:
        nombre = f"{p.get('nombres', '')} {p.get('apellidos', '')}".strip()
        if nombre:
            items.append({'label': 'Cliente', 'valor': nombre, 'lock': False})
        if p.get('correo_persona'):
            items.append({'label': 'Correo', 'valor': p['correo_persona'], 'lock': False})
        ciudad = ''
        if p.get('id_ciudad'):
            c = Ciudad.objects.filter(id_ciudad=p['id_ciudad']).first()
            ciudad = c.ciudad if c else ''
        partes = [p.get('direccion_persona'), p.get('complemento_persona'),
                  p.get('barrio_persona'), ciudad]
        direccion = ', '.join(x for x in partes if x)
        if direccion:
            items.append({'label': 'Dirección', 'valor': direccion, 'lock': False})
    # Puntos de extensión: servicio+valor (borrador['acuerdo']) y motivo (borrador['motivo']).
    return items


def _recolectar_plataformas(request):
    """Lee las filas de accesos del POST (arreglos paralelos) y descarta vacías.
    El buró viene como id en 'plat_buro'; guardamos id (ancla) y nombre (para mostrar)."""
    buros_ids = request.POST.getlist('plat_buro')
    usuarios = request.POST.getlist('plat_usuario')
    passwords = request.POST.getlist('plat_password')
    descs = request.POST.getlist('plat_desc')
    # mapa id->nombre solo de los burós referenciados
    referenciados = [b for b in buros_ids if b]
    nombres = {}
    if referenciados:
        nombres = {str(b.id_buro): b.nombre_buro
                   for b in Buro.objects.filter(id_buro__in=referenciados)}
    filas = []
    for i in range(len(buros_ids)):
        bid = buros_ids[i].strip()
        usr = (usuarios[i] if i < len(usuarios) else '').strip()
        pas = passwords[i] if i < len(passwords) else ''
        des = (descs[i] if i < len(descs) else '').strip()
        if not (bid or usr or pas or des):
            continue
        filas.append({'buro_id': bid, 'plataforma': nombres.get(bid, ''),
                      'usuario': usr, 'password': pas, 'descripcion': des})
    return filas


def _base_media():
    return settings.MEDIA_ROOT or os.path.join(settings.BASE_DIR, 'media')


def _guardar_reportes_temp(request, borrador):
    """Guarda los archivos subidos en una carpeta temporal y registra su referencia."""
    reportes = borrador.get('reportes') or []
    etiqueta = request.POST.get('reporte_etiqueta', '').strip()
    buro_id = request.POST.get('reporte_buro', '').strip()
    buro_nombre = ''
    if buro_id:
        b = Buro.objects.filter(id_buro=buro_id).first()
        buro_nombre = b.nombre_buro if b else ''
    carpeta = os.path.join(_base_media(), TMP_REPORTES)
    os.makedirs(carpeta, exist_ok=True)
    for f in request.FILES.getlist('reporte_archivo'):
        ext = os.path.splitext(f.name)[1].lower()
        if ext not in ('.pdf', '.png', '.jpg', '.jpeg'):
            continue  # validación básica de tipo
        nombre_tmp = uuid.uuid4().hex + ext
        with open(os.path.join(carpeta, nombre_tmp), 'wb') as out:
            for chunk in f.chunks():
                out.write(chunk)
        reportes.append({'nombre': f.name, 'tmp': nombre_tmp, 'etiqueta': etiqueta,
                         'buro_id': buro_id, 'buro_nombre': buro_nombre})
    return reportes


def _quitar_reporte_temp(borrador, idx):
    reportes = borrador.get('reportes') or []
    if 0 <= idx < len(reportes):
        r = reportes.pop(idx)
        ruta = os.path.join(_base_media(), TMP_REPORTES, r.get('tmp', ''))
        try:
            if r.get('tmp') and os.path.exists(ruta):
                os.remove(ruta)
        except OSError:
            pass
    return reportes


def _to_dec(s):
    try:
        return Decimal(str(s).replace(',', '').strip())
    except (InvalidOperation, AttributeError):
        return None


def _servicios_catalogo():
    cat = []
    for s in Servicios.objects.filter(estado='ACTIVO').order_by('nombre_servicio'):
        cat.append({
            'id': s.id_servicio, 'nombre': s.nombre_servicio,
            'min': str(s.precio_minimo), 'max': str(s.precio_maximo),
            'ideal': str(s.precio_ideal) if s.precio_ideal is not None else '',
        })
    return cat


def _recolectar_acuerdo(request):
    serv_ids = request.POST.getlist('serv_id')
    serv_vals = request.POST.getlist('serv_valor')
    referenciados = [s for s in serv_ids if s]
    nombres = {}
    if referenciados:
        nombres = {str(s.id_servicio): s.nombre_servicio
                   for s in Servicios.objects.filter(id_servicio__in=referenciados)}
    servicios = []
    total = Decimal('0')
    for i in range(len(serv_ids)):
        sid = serv_ids[i].strip()
        val = (serv_vals[i] if i < len(serv_vals) else '').strip()
        if not (sid or val):
            continue
        servicios.append({'servicio_id': sid, 'nombre': nombres.get(sid, ''), 'valor': val})
        d = _to_dec(val)
        if d is not None:
            total += d
    cuota_ids = request.POST.getlist('cuota_id')
    cuota_bloq = request.POST.getlist('cuota_bloqueada')
    cuota_fechas = request.POST.getlist('cuota_fecha')
    cuota_vals = request.POST.getlist('cuota_valor')
    cuotas = []
    for i in range(len(cuota_vals)):
        fec = (cuota_fechas[i] if i < len(cuota_fechas) else '').strip()
        val = (cuota_vals[i] if i < len(cuota_vals) else '').strip()
        if not (fec or val):
            continue
        cuotas.append({
            'id': (cuota_ids[i] if i < len(cuota_ids) else '').strip(),
            'bloqueada': (cuota_bloq[i] == '1') if i < len(cuota_bloq) else False,
            'fecha': fec, 'valor': val,
        })
    return {'servicios': servicios, 'cuotas': cuotas, 'total': str(total)}


def _validar_acuerdo(acuerdo):
    errores = []
    servicios = [s for s in (acuerdo.get('servicios') or []) if s.get('servicio_id')]
    if not servicios:
        errores.append('Agrega al menos un servicio.')
    ids = [s['servicio_id'] for s in servicios]
    catalogo = {str(s.id_servicio): s for s in Servicios.objects.filter(id_servicio__in=ids)} if ids else {}
    total = Decimal('0')
    for s in servicios:
        d = _to_dec(s.get('valor'))
        cat = catalogo.get(s['servicio_id'])
        if d is None:
            errores.append(f"El servicio '{s.get('nombre') or s['servicio_id']}' necesita un valor.")
            continue
        total += d
        if cat and (d < cat.precio_minimo or d > cat.precio_maximo):
            errores.append(f"'{cat.nombre_servicio}': ${d} está fuera del rango permitido (${cat.precio_minimo} – ${cat.precio_maximo}).")
    cuotas = [c for c in (acuerdo.get('cuotas') or []) if c.get('valor') or c.get('fecha')]
    if not cuotas:
        errores.append('Agrega al menos una cuota.')
    suma = Decimal('0')
    for c in cuotas:
        d = _to_dec(c.get('valor'))
        if d is None:
            errores.append('Hay una cuota sin valor.')
        else:
            suma += d
        if not c.get('fecha'):
            errores.append('Hay una cuota sin fecha de pago.')
    if not errores and suma != total:
        dif = total - suma
        errores.append(f"Las cuotas suman ${suma} pero el total de servicios es ${total}. Diferencia: ${dif}. Deben coincidir exactamente.")
    return errores


def _render(request, paso, borrador, form, errores=None):
    return render(request, 'leads/wizard_v2.html', {
        'paso': paso, 'pasos': PASOS, 'total_pasos': len(PASOS),
        'observaciones': borrador.get('observaciones', ''),
        'identificadores': _identificadores(borrador),
        'plataformas': borrador.get('plataformas') or [{}],  # siempre al menos 1 fila para escribir
        'reportes': borrador.get('reportes') or [],
        'buros': Buro.objects.filter(estado='ACTIVO').order_by('nombre_buro'),
        'servicios_cat': _servicios_catalogo() if paso == 3 else [],
        'acuerdo_servicios': (borrador.get('acuerdo') or {}).get('servicios') or [{}],
        'acuerdo_cuotas': (borrador.get('acuerdo') or {}).get('cuotas') or [{}],
        'acuerdo_total': (borrador.get('acuerdo') or {}).get('total', '0'),
        'acuerdo': borrador.get('acuerdo') or {},
        'motivos': MotivoContrato.objects.order_by('motivo_contrato') if paso == 4 else [],
        'motivo_sel': borrador.get('motivo'),
        'persona_data': borrador.get('persona') or {},
        'editando': borrador.get('editando'),
        'es_gerente': _edicion_total(request),
        'bloquear_accesos': bool(borrador.get('editando')) and not _edicion_total(request),
        'bloquear_servicios': bool(borrador.get('editando')) and not _edicion_total(request),
        'errores': errores,
        # Compatibilidad: por si el template quedara rezagado (hardlink)
        'telefono': borrador.get('telefono', ''),
        'tipo_documento': borrador.get('tipo_documento', ''),
        'documento': borrador.get('documento', ''),
        'form': form,
    })


def _fecha(s):
    try:
        return date.fromisoformat(s) if s else None
    except (ValueError, TypeError):
        return None


def _crear_o_reusar_persona(borrador):
    p = borrador.get('persona') or {}
    cid = p.get('id_ciudad')
    datos = {
        'nombres': p.get('nombres', ''),
        'apellidos': p.get('apellidos', ''),
        'correo_persona': p.get('correo_persona') or None,
        'direccion_persona': p.get('direccion_persona') or None,
        'complemento_persona': p.get('complemento_persona') or None,
        'barrio_persona': p.get('barrio_persona') or None,
        'genero_persona': p.get('genero_persona') or None,
        'fecha_expedicion_persona': _fecha(p.get('fecha_expedicion_persona')),
        'fecha_nacimiento_persona': _fecha(p.get('fecha_nacimiento_persona')),
        'id_ciudad_id': int(cid) if cid else None,
    }
    if borrador.get('reusar'):
        persona = Persona.objects.get(id_persona=borrador['reusar'])
        for k, v in datos.items():
            setattr(persona, k, v)
        persona.save()
        return persona
    persona = Persona(
        numero_documento_persona=borrador.get('documento'),
        tipo_documento_persona=borrador.get('tipo_documento') or None,
        **datos)
    persona.save()
    return persona


def _crear_telefonos(persona, borrador):
    principal = (borrador.get('telefono') or '').strip()
    if principal:
        tipo = 'Principal'
        if Telefonos.objects.filter(numero_telefono=principal, tipo_telefono='Principal').exclude(id_persona=persona).exists():
            tipo = 'Adicional'
        Telefonos.objects.get_or_create(
            numero_telefono=principal, id_persona=persona,
            defaults={'tipo_telefono': tipo})
    p = borrador.get('persona') or {}
    for k in ('telefono_adicional_1', 'telefono_adicional_2', 'telefono_adicional_3'):
        num = (p.get(k) or '').strip()
        if num:
            Telefonos.objects.get_or_create(
                numero_telefono=num, id_persona=persona,
                defaults={'tipo_telefono': 'Adicional'})


def _crear_acuerdo_db(borrador):
    ac = borrador.get('acuerdo') or {}
    total = _to_dec(ac.get('total')) or Decimal('0')
    acuerdo = AcuerdoPago.objects.create(
        valor_total_acuerdo_pago=total,
        observaciones_acuerdo_pago='Acuerdo generado desde el asistente de captura.')
    for s in ac.get('servicios') or []:
        sid = s.get('servicio_id')
        val = _to_dec(s.get('valor'))
        if sid and val is not None:
            AcuerdoPagoDetalle.objects.create(
                id_acuerdo_pago=acuerdo, id_servicio_id=int(sid), valor_cobrado=val)
    for c in ac.get('cuotas') or []:
        val = _to_dec(c.get('valor'))
        fec = _fecha(c.get('fecha'))
        if val is not None and fec:
            CuotaEstado.objects.create(
                id_acuerdo_pago=acuerdo, valor_fecha_pago=val,
                fecha_pago=fec, estado_pago='PENDIENTE')
    return acuerdo


def _crear_accesos(lead, borrador):
    for pl in borrador.get('plataformas') or []:
        if not (pl.get('buro_id') or pl.get('usuario') or pl.get('password')):
            continue
        UsuarioReporte.objects.create(
            id_lead=lead,
            id_buro_id=int(pl['buro_id']) if pl.get('buro_id') else None,
            usuario_reporte=pl.get('usuario') or None,
            password_reporte=pl.get('password') or None,
            plataforma_reporte=pl.get('plataforma') or None,
            descripcion_reporte=pl.get('descripcion') or None)


def _mover_reportes(lead, borrador):
    reportes = borrador.get('reportes') or []
    doc = (borrador.get('documento') or 'doc').strip()
    tel = (borrador.get('telefono') or 'tel').strip()
    carpeta = os.path.join(_base_media(), TMP_REPORTES)
    for idx, r in enumerate(reportes, start=1):
        tmp = r.get('tmp')
        if not tmp:
            continue
        origen = os.path.join(carpeta, tmp)
        if not os.path.exists(origen):
            continue
        ext = os.path.splitext(tmp)[1].lower()
        buro = (r.get('buro_nombre') or 'otro').replace(' ', '')
        nombre_final = f"{doc}_{tel}_{buro}_{idx}{ext}"
        rg = ReporteGrafico(
            id_lead=lead,
            id_buro_id=int(r['buro_id']) if r.get('buro_id') else None,
            tipo_reporte_grafico=(r.get('etiqueta') or '')[:50])
        with open(origen, 'rb') as fh:
            rg.documento_reporte_grafico.save(nombre_final, File(fh), save=False)
        rg.save()
        try:
            os.remove(origen)
        except OSError:
            pass


def _guardar_observaciones(lead, asesor, borrador):
    texto = (borrador.get('observaciones') or '').strip()
    if texto:
        Observaciones.objects.create(
            id_lead=lead, id_trabajador=asesor,
            observacion=texto, fecha_registro=timezone.now())


def _validar_guardado(borrador, asesor):
    errores = []
    if not asesor:
        errores.append('No se pudo identificar tu usuario trabajador. Inicia sesión de nuevo.')
    if not (borrador.get('persona') or {}).get('nombres'):
        errores.append('Faltan los datos de la persona (vuelve al paso 1).')
    errores += _validar_acuerdo(borrador.get('acuerdo') or {})
    if not borrador.get('motivo'):
        errores.append('Selecciona el motivo del contrato.')
    return errores


def _guardar_todo(borrador, asesor):
    with transaction.atomic():
        doc = borrador.get('documento')
        persona_doc = Persona.objects.filter(numero_documento_persona=doc).first() if doc else None
        if persona_doc and not borrador.get('reusar'):
            raise Exception('El documento ya fue registrado por otro proceso.')
        if persona_doc:
            otro_vendido = Leads.objects.filter(
                id_persona=persona_doc, estado_venta='VENDIDO'
            ).exclude(id_trabajador=asesor).exists()
            if otro_vendido:
                raise Exception('Este cliente ya fue vendido por otro asesor.')
        persona = _crear_o_reusar_persona(borrador)
        _crear_telefonos(persona, borrador)
        acuerdo = _crear_acuerdo_db(borrador)
        motivo = MotivoContrato.objects.filter(id_contrato=borrador.get('motivo')).first()
        lead = Leads.objects.create(
            id_persona=persona, id_trabajador=asesor,
            id_contrato=motivo, id_acuerdo_pago=acuerdo,
            estado_lead='NUEVO', estado_venta='LEAD',
            telefono_marcado=borrador.get('telefono'))
        _crear_accesos(lead, borrador)
        _mover_reportes(lead, borrador)
        _guardar_observaciones(lead, asesor, borrador)
    return lead


def iniciar_edicion_lead(request, id_lead):
    """Carga un lead existente en el borrador y abre el wizard en modo edición."""
    from django.shortcuts import get_object_or_404
    lead = get_object_or_404(Leads, id_lead=id_lead)
    persona = lead.id_persona
    acuerdo = lead.id_acuerdo_pago
    principal = lead.telefono_marcado or ''

    adicionales = []
    persona_data = {}
    if persona:
        adicionales = list(Telefonos.objects.filter(id_persona=persona)
                           .exclude(numero_telefono=principal)
                           .values_list('numero_telefono', flat=True))
        persona_data = {
            'nombres': persona.nombres, 'apellidos': persona.apellidos,
            'fecha_expedicion_persona': str(persona.fecha_expedicion_persona or ''),
            'fecha_nacimiento_persona': str(persona.fecha_nacimiento_persona or ''),
            'genero_persona': persona.genero_persona or '',
            'correo_persona': persona.correo_persona or '',
            'direccion_persona': persona.direccion_persona or '',
            'complemento_persona': persona.complemento_persona or '',
            'barrio_persona': persona.barrio_persona or '',
            'id_ciudad': str(persona.id_ciudad_id or ''),
            'telefono_adicional_1': adicionales[0] if len(adicionales) > 0 else '',
            'telefono_adicional_2': adicionales[1] if len(adicionales) > 1 else '',
            'telefono_adicional_3': adicionales[2] if len(adicionales) > 2 else '',
        }

    plataformas = []
    for a in UsuarioReporte.objects.filter(id_lead=lead).select_related('id_buro'):
        plataformas.append({
            'buro_id': str(a.id_buro_id or ''),
            'plataforma': a.id_buro.nombre_buro if a.id_buro else (a.plataforma_reporte or ''),
            'usuario': a.usuario_reporte or '', 'password': a.password_reporte or '',
            'descripcion': a.descripcion_reporte or '',
        })

    servicios, cuotas, total = [], [], '0'
    if acuerdo:
        for d in AcuerdoPagoDetalle.objects.filter(id_acuerdo_pago=acuerdo).select_related('id_servicio'):
            servicios.append({'servicio_id': str(d.id_servicio_id),
                              'nombre': d.id_servicio.nombre_servicio, 'valor': str(d.valor_cobrado)})
        for c in CuotaEstado.objects.filter(id_acuerdo_pago=acuerdo).order_by('fecha_pago'):
            bloqueada = PagoRealizado.objects.filter(id_cuota=c).exists()
            cuotas.append({'id': c.id_fecha_pago, 'fecha': str(c.fecha_pago),
                           'valor': str(c.valor_fecha_pago), 'bloqueada': bloqueada})
        total = str(acuerdo.valor_total_acuerdo_pago)

    request.session['borrador_lead'] = {
        'editando': lead.id_lead,
        'telefono': principal,
        'tipo_documento': persona.tipo_documento_persona or '' if persona else '',
        'documento': persona.numero_documento_persona or '' if persona else '',
        'observaciones': '', 'reusar': persona.id_persona if persona else None,
        'persona': persona_data, 'plataformas': plataformas, 'reportes': [],
        'acuerdo': {'servicios': servicios, 'cuotas': cuotas, 'total': total},
        'motivo': str(lead.id_contrato_id or ''),
    }
    return redirect('wizard_lead', paso=1)


def _actualizar_acuerdo(lead, borrador):
    """Edición del plan: reemplaza servicios y recalcula total; conserva las cuotas
    que ya tienen pagos y recrea solo las no pagadas (y las nuevas)."""
    acuerdo = lead.id_acuerdo_pago
    if not acuerdo:
        return
    ac = borrador.get('acuerdo') or {}
    # Servicios: reemplazo total
    AcuerdoPagoDetalle.objects.filter(id_acuerdo_pago=acuerdo).delete()
    total = Decimal('0')
    for s in ac.get('servicios') or []:
        sid = s.get('servicio_id')
        val = _to_dec(s.get('valor'))
        if sid and val is not None:
            AcuerdoPagoDetalle.objects.create(id_acuerdo_pago=acuerdo, id_servicio_id=int(sid), valor_cobrado=val)
            total += val
    acuerdo.valor_total_acuerdo_pago = total
    acuerdo.save()
    # Cuotas: conservar las que tienen pagos; borrar y recrear las demás
    for c in CuotaEstado.objects.filter(id_acuerdo_pago=acuerdo):
        if not PagoRealizado.objects.filter(id_cuota=c).exists():
            c.delete()
    for cu in ac.get('cuotas') or []:
        if cu.get('bloqueada'):
            continue  # ya existe en BD con sus pagos, no se toca
        val = _to_dec(cu.get('valor'))
        fec = _fecha(cu.get('fecha'))
        if val is not None and fec:
            estado = 'EN MORA' if fec < date.today() else 'PENDIENTE'
            CuotaEstado.objects.create(id_acuerdo_pago=acuerdo, valor_fecha_pago=val,
                                       fecha_pago=fec, estado_pago=estado)


def _actualizar_todo(request, borrador, asesor):
    """Modo edición (2a): actualiza persona, teléfonos, motivo y accesos.
    Servicios/cuotas/reportes existentes se preservan (su edición fina va en 2b)."""
    es_gerente = _edicion_total(request)
    with transaction.atomic():
        lead = Leads.objects.select_related('id_persona').get(id_lead=borrador['editando'])
        persona = lead.id_persona
        p = borrador.get('persona') or {}
        if es_gerente:
            persona.nombres = p.get('nombres', persona.nombres)
            persona.apellidos = p.get('apellidos', persona.apellidos)
        # Campos libres para ambos perfiles
        persona.correo_persona = p.get('correo_persona') or None
        persona.direccion_persona = p.get('direccion_persona') or None
        persona.complemento_persona = p.get('complemento_persona') or None
        persona.barrio_persona = p.get('barrio_persona') or None
        persona.genero_persona = p.get('genero_persona') or None
        persona.fecha_expedicion_persona = _fecha(p.get('fecha_expedicion_persona'))
        persona.fecha_nacimiento_persona = _fecha(p.get('fecha_nacimiento_persona'))
        cid = p.get('id_ciudad')
        persona.id_ciudad_id = int(cid) if cid else None
        persona.save()

        # Teléfonos adicionales: se reemplazan (el principal no se toca)
        Telefonos.objects.filter(id_persona=persona).exclude(numero_telefono=lead.telefono_marcado).delete()
        for k in ('telefono_adicional_1', 'telefono_adicional_2', 'telefono_adicional_3'):
            num = (p.get(k) or '').strip()
            if num and num != lead.telefono_marcado:
                Telefonos.objects.get_or_create(numero_telefono=num, id_persona=persona,
                                                defaults={'tipo_telefono': 'Adicional'})

        # Motivo
        lead.id_contrato = MotivoContrato.objects.filter(id_contrato=borrador.get('motivo')).first()
        lead.save()

        # Plan de pago (servicios + cuotas, conservando cuotas con pagos)
        _actualizar_acuerdo(lead, borrador)

        # Accesos: se reemplazan (el asesor no puede borrar, así que su borrador trae todos)
        UsuarioReporte.objects.filter(id_lead=lead).delete()
        _crear_accesos(lead, borrador)

        # Reportes nuevos subidos en esta edición (los existentes se conservan)
        _mover_reportes(lead, borrador)

        # Nota de bitácora si escribió algo
        _guardar_observaciones(lead, asesor, borrador)
    return lead


def wizard_lead(request, paso=1):
    borrador = request.session.get('borrador_lead')
    if not borrador:
        return redirect('captura_inicial')

    paso = max(1, min(int(paso), len(PASOS)))

    if request.method == 'POST':
        accion = request.POST.get('accion', 'siguiente')
        borrador['observaciones'] = request.POST.get('observaciones', borrador.get('observaciones', ''))

        # Paso 2: subir / quitar reportes NO navega, re-renderiza el mismo paso
        quitar_idx = request.POST.get('quitar_idx')
        if paso == 2 and (accion == 'subir_reporte' or quitar_idx is not None):
            borrador['plataformas'] = _recolectar_plataformas(request)  # no perder accesos ya escritos
            if accion == 'subir_reporte':
                borrador['reportes'] = _guardar_reportes_temp(request, borrador)
            elif quitar_idx is not None:
                try:
                    idx = int(quitar_idx)
                except ValueError:
                    idx = -1
                borrador['reportes'] = _quitar_reporte_temp(borrador, idx)
            request.session['borrador_lead'] = borrador
            return _render(request, 2, borrador, None)

        if paso == 1 and accion == 'siguiente':
            form = _persona_form(request, borrador, bound=True)
            if form.is_valid():
                borrador['persona'] = {f: request.POST.get(f, '') for f in PERSONA_FIELDS}
                request.session['borrador_lead'] = borrador
                return redirect('wizard_lead', paso=2)
            request.session['borrador_lead'] = borrador
            return _render(request, paso, borrador, form)

        if paso == 1:
            borrador['persona'] = {f: request.POST.get(f, '') for f in PERSONA_FIELDS}
        elif paso == 2:
            borrador['plataformas'] = _recolectar_plataformas(request)
        elif paso == 3:
            borrador['acuerdo'] = _recolectar_acuerdo(request)
            if accion == 'siguiente':
                errores = _validar_acuerdo(borrador['acuerdo'])
                if errores:
                    request.session['borrador_lead'] = borrador
                    return _render(request, 3, borrador, None, errores=errores)
        elif paso == 4:
            borrador['motivo'] = request.POST.get('motivo_id', borrador.get('motivo'))
            if accion == 'guardar':
                asesor = trabajador_actual(request)
                errores = _validar_guardado(borrador, asesor)
                if errores:
                    request.session['borrador_lead'] = borrador
                    return _render(request, 4, borrador, None, errores=errores)
                era_edicion = bool(borrador.get('editando'))
                try:
                    if era_edicion:
                        lead = _actualizar_todo(request, borrador, asesor)
                    else:
                        lead = _guardar_todo(borrador, asesor)
                except Exception as e:
                    request.session['borrador_lead'] = borrador
                    return _render(request, 4, borrador, None, errores=[f'No se pudo guardar: {e}'])
                request.session.pop('borrador_lead', None)
                messages.success(request, f'Lead #{lead.id_lead} {"actualizado" if era_edicion else "creado"} correctamente.')
                return redirect('ver_lead', id_lead=lead.id_lead)
        request.session['borrador_lead'] = borrador
        destino = paso + 1 if accion == 'siguiente' else paso - 1
        return redirect('wizard_lead', paso=max(1, min(destino, len(PASOS))))

    form = _persona_form(request, borrador, bound=False) if paso == 1 else None
    return _render(request, paso, borrador, form)
