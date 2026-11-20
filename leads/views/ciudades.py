"""CRUD del catálogo de ciudades, con conteo de trabajadores y clientes."""

from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Count, Q
from ..models import Ciudad, Persona, Trabajador
from ..forms.ciudades import CiudadForm
from ..decoradores import rol_requerido

# Un trabajador = persona CON registro en 'trabajador'. Un cliente = persona SIN ese registro.
ES_TRABAJADOR = Q(persona__trabajador__isnull=False)
ES_CLIENTE = Q(persona__trabajador__isnull=True)


@rol_requerido('Gerente General')
def listar_ciudades(request):
    q = request.GET.get('q', '').strip()
    ciudades = Ciudad.objects.annotate(
        n_trabajadores=Count('persona', filter=ES_TRABAJADOR, distinct=True),
        n_clientes=Count('persona', filter=ES_CLIENTE, distinct=True),
    ).order_by('ciudad')
    if q:
        ciudades = ciudades.filter(ciudad__icontains=q)

    por_ciudad = list(
        Ciudad.objects.annotate(
            trab=Count('persona', filter=ES_TRABAJADOR, distinct=True),
            cli=Count('persona', filter=ES_CLIENTE, distinct=True),
        ).values('ciudad', 'trab', 'cli').order_by('-cli')[:8]
    )

    contexto = {
        'ciudades': ciudades,
        'f_q': q,
        'total_ciudades': Ciudad.objects.count(),
        'total_trabajadores': Trabajador.objects.count(),
        'total_clientes': Persona.objects.filter(trabajador__isnull=True).count(),
        'por_ciudad': por_ciudad,
    }
    return render(request, 'leads/listar_ciudades.html', contexto)


@rol_requerido('Gerente General')
def crear_editar_ciudad(request, id_ciudad=None):
    ciudad_instancia = get_object_or_404(Ciudad, id_ciudad=id_ciudad) if id_ciudad else None

    if request.method == 'POST':
        form = CiudadForm(request.POST, instance=ciudad_instancia)
        if form.is_valid():
            form.save()
            return redirect('listar_ciudades')
    else:
        form = CiudadForm(instance=ciudad_instancia)

    return render(request, 'leads/form_ciudad.html', {
        'form': form,
        'es_edicion': True if id_ciudad else False
    })


@rol_requerido('Gerente General')
def eliminar_ciudad(request, id_ciudad):
    ciudad = get_object_or_404(Ciudad, id_ciudad=id_ciudad)

    if request.method == 'POST':
        ciudad.delete()
        return redirect('listar_ciudades')

    return render(request, 'leads/eliminar_ciudad.html', {'ciudad': ciudad})
