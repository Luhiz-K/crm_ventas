from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from ..forms.captura_inicial import CapturaTelefonoForm
from ..models import Telefonos, Leads, Persona
from ..utils import trabajador_actual, enmascarar


def _persona_por_telefono(numero):
    tel = Telefonos.objects.select_related('id_persona').filter(numero_telefono=numero).first()
    if tel:
        return tel.id_persona
    lead = Leads.objects.select_related('id_persona').filter(telefono_marcado=numero).first()
    return lead.id_persona if lead else None


def _continuar(request, numero, observacion, tipo, documento, reusar):
    request.session['borrador_lead'] = {
        'telefono': numero, 'tipo_documento': tipo, 'documento': documento,
        'observaciones': observacion or '', 'reusar': reusar,
        'persona': None, 'plataformas': None, 'acuerdo': None, 'motivo': None,
    }
    return redirect('wizard_lead', paso=1)


def iniciar_captura_lead(request):
    if request.method == 'POST':
        form = CapturaTelefonoForm(request.POST)
        if form.is_valid():
            numero = form.cleaned_data['numero_marcado']
            observacion = form.cleaned_data['observacion']
            tipo = form.cleaned_data['tipo_documento']
            documento = form.cleaned_data['numero_documento']

            # --- La LLAVE es el DOCUMENTO ---
            persona_doc = Persona.objects.filter(numero_documento_persona=documento).first()
            if persona_doc:
                mi_trab = trabajador_actual(request)
                activos = Leads.objects.filter(id_persona=persona_doc, estado_venta='VENDIDO')
                if activos.exists():
                    propio = activos.filter(id_trabajador=mi_trab).first() if mi_trab else None
                    if propio:
                        return redirect('editar_lead', id_lead=propio.id_lead)
                    messages.warning(request, 'Este cliente ya fue registrado (vendido) por otro asesor. No puedes crearlo.')
                    return redirect('captura_inicial')
                # LEAD / FINALIZADO -> libre -> reutilizamos la persona existente
                return _continuar(request, numero, observacion, tipo, documento, reusar=persona_doc.id_persona)

            # Documento nuevo -> persona nueva
            return _continuar(request, numero, observacion, tipo, documento, reusar=None)
    else:
        form = CapturaTelefonoForm()

    return render(request, 'leads/captura_inicial.html', {'form': form})


def verificar_telefono(request):
    numero = request.GET.get('numero', '').strip()
    if not numero.isdigit() or len(numero) != 10:
        return JsonResponse({'valido': False})
    persona = _persona_por_telefono(numero)
    if not persona:
        return JsonResponse({'valido': True, 'existe': False})
    nombre_full = f"{persona.nombres} {persona.apellidos}"
    return JsonResponse({'valido': True, 'existe': True, 'nombre': enmascarar(nombre_full)})


def verificar_documento(request):
    doc = request.GET.get('doc', '').strip()
    if not doc:
        return JsonResponse({'permitir': False})
    persona = Persona.objects.filter(numero_documento_persona=doc).first()
    if not persona:
        return JsonResponse({'existe': False, 'permitir': True, 'mensaje': 'Documento nuevo. Puedes continuar.'})
    mi_trab = trabajador_actual(request)
    activos = Leads.objects.filter(id_persona=persona, estado_venta='VENDIDO').select_related(
        'id_trabajador', 'id_trabajador__id_persona')
    if activos.exists():
        propio = activos.filter(id_trabajador=mi_trab).first() if mi_trab else None
        if propio:
            return JsonResponse({'existe': True, 'permitir': True, 'es_propio': True,
                                 'editar_url': f'/leads/leads/editar/{propio.id_lead}/',
                                 'mensaje': 'Ya tienes este cliente (vendido activo).'})
        otro = activos.first()
        ini = (otro.id_trabajador.id_persona.nombres[:1].upper()
               if otro.id_trabajador and otro.id_trabajador.id_persona else '?')
        return JsonResponse({'existe': True, 'permitir': False,
                             'mensaje': f'Este cliente ya fue registrado (vendido) por {ini}.'})
    return JsonResponse({'existe': True, 'permitir': True,
                         'mensaje': 'El cliente existe pero está libre (LEAD/finalizado). Puedes continuar.'})
