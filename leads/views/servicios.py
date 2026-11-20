"""CRUD del catálogo de servicios y su banda de precios."""

from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Count, Sum
from ..models import Servicios
from ..forms.servicios import ServicioForm
from ..decoradores import rol_requerido


@rol_requerido('Gerente General')
def listar_servicios(request):
    q = request.GET.get('q', '').strip()
    estado = request.GET.get('estado', '').strip()
    servicios = Servicios.objects.annotate(
        veces=Count('acuerdopagodetalle'),
        ingresos=Sum('acuerdopagodetalle__valor_cobrado'),
    ).order_by('nombre_servicio')
    if q:
        servicios = servicios.filter(nombre_servicio__icontains=q)
    if estado:
        servicios = servicios.filter(estado=estado)

    top = list(
        Servicios.objects.annotate(n=Count('acuerdopagodetalle'))
        .values('nombre_servicio', 'n').order_by('-n')[:8]
    )
    return render(request, 'leads/listar_servicios.html', {
        'servicios': servicios, 'f_q': q, 'f_estado': estado,
        'total': Servicios.objects.count(),
        'activos': Servicios.objects.filter(estado='ACTIVO').count(),
        'top': top,
    })


@rol_requerido('Gerente General')
def crear_editar_servicio(request, id_servicio=None):
    servicio = get_object_or_404(Servicios, id_servicio=id_servicio) if id_servicio else None
    if request.method == 'POST':
        form = ServicioForm(request.POST, instance=servicio)
        if form.is_valid():
            obj = form.save(commit=False)
            if not obj.estado:
                obj.estado = 'ACTIVO'
            obj.save()
            return redirect('listar_servicios')
    else:
        form = ServicioForm(instance=servicio)
    return render(request, 'leads/form_servicio.html', {'form': form, 'es_edicion': bool(id_servicio)})
