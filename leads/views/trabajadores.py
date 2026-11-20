"""CRUD de trabajadores, con cargos base y coherencia responsable-sede."""

from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Count, Q
from ..models import Trabajador, Cargo, Sede, Persona, Telefonos
from ..forms.trabajadores import TrabajadorForm
from ..decoradores import rol_requerido


def asegurar_cargos_basicos():
    for nombre in ['Asesor', 'Coach', 'Gerente Sede', 'Calidad', 'Gerente General']:
        Cargo.objects.get_or_create(nombre_cargo=nombre, defaults={'descripcion_cargo': f'Rol operativo de {nombre}'})


@rol_requerido('Gerente General')
def listar_trabajadores(request):
    asegurar_cargos_basicos()
    q = request.GET.get('q', '').strip()
    trabajadores = Trabajador.objects.select_related('id_persona', 'id_sede', 'id_cargo').order_by('id_persona__nombres')
    if q:
        trabajadores = trabajadores.filter(
            Q(id_persona__nombres__icontains=q) |
            Q(id_persona__apellidos__icontains=q) |
            Q(id_persona__numero_documento_persona__icontains=q)
        )
    por_cargo = list(Cargo.objects.annotate(n=Count('trabajador')).values('nombre_cargo', 'n').order_by('-n'))
    return render(request, 'leads/listar_trabajadores.html', {
        'trabajadores': trabajadores, 'f_q': q,
        'total_trabajadores': Trabajador.objects.count(),
        'total_sedes': Sede.objects.count(),
        'por_cargo': por_cargo,
    })


def _sincronizar_responsable(trabajador):
    """Garantiza que un responsable solo dirija la sede donde trabaja.

    Lo desvincula como responsable de cualquier otra sede distinta a la suya.
    """
    qs = Sede.objects.filter(id_responsable=trabajador.id_persona)
    if trabajador.id_sede_id:
        qs = qs.exclude(pk=trabajador.id_sede_id)
    qs.update(id_responsable=None)


@rol_requerido('Gerente General')
def crear_editar_trabajador(request, id_trabajador=None):
    asegurar_cargos_basicos()
    trabajador = get_object_or_404(Trabajador, id_trabajador=id_trabajador) if id_trabajador else None
    sede_ctx = request.GET.get('sede', '') or request.POST.get('sede_ctx', '')
    como_resp = request.GET.get('como_responsable', '') or request.POST.get('como_resp_ctx', '')

    if request.method == 'POST':
        form = TrabajadorForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            dup = (trabajador is None) and Persona.objects.filter(
                numero_documento_persona=cd['numero_documento']).exists()
            if dup:
                form.add_error('numero_documento', 'Ya existe una persona con ese documento.')
            else:
                if trabajador:
                    p = trabajador.id_persona
                    p.nombres = cd['nombres']
                    p.apellidos = cd['apellidos']
                    p.numero_documento_persona = cd['numero_documento']
                    p.correo_persona = cd['correo']
                    p.save()
                    trabajador.id_cargo = cd['id_cargo']
                    trabajador.id_sede = cd['id_sede']
                    trabajador.save()
                else:
                    p = Persona.objects.create(
                        nombres=cd['nombres'], apellidos=cd['apellidos'],
                        numero_documento_persona=cd['numero_documento'], correo_persona=cd['correo'])
                    trabajador = Trabajador.objects.create(
                        id_persona=p, id_cargo=cd['id_cargo'], id_sede=cd['id_sede'])
                    if cd['telefono']:
                        Telefonos.objects.get_or_create(
                            numero_telefono=cd['telefono'], tipo_telefono='Principal',
                            defaults={'id_persona': p})

                # Coherencia responsable <-> sede
                _sincronizar_responsable(trabajador)

                # Flujo anidado: creado como responsable de una sede
                if como_resp and sede_ctx:
                    sede = Sede.objects.filter(id_sede=sede_ctx).first()
                    if sede:
                        sede.id_responsable = trabajador.id_persona
                        sede.save()
                        return redirect('editar_sede', id_sede=sede.id_sede)
                return redirect('listar_trabajadores')
    else:
        inicial = {}
        if trabajador:
            p = trabajador.id_persona
            inicial = {
                'nombres': p.nombres, 'apellidos': p.apellidos,
                'numero_documento': p.numero_documento_persona, 'correo': p.correo_persona,
                'id_cargo': trabajador.id_cargo_id, 'id_sede': trabajador.id_sede_id,
            }
        elif sede_ctx:
            inicial = {'id_sede': sede_ctx}
        form = TrabajadorForm(initial=inicial)

    return render(request, 'leads/form_trabajador.html', {
        'form': form, 'es_edicion': bool(id_trabajador),
        'sede_ctx': sede_ctx, 'como_resp': como_resp,
    })
