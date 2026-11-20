from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Count
from ..models import Buro
from ..forms.buros import BuroForm
from ..decoradores import rol_requerido


@rol_requerido('Gerente General')
def listar_buros(request):
    q = request.GET.get('q', '').strip()
    buros = Buro.objects.annotate(
        n_reportes=Count('reportegrafico', distinct=True),
        n_accesos=Count('usuarioreporte', distinct=True),
    ).order_by('nombre_buro')
    if q:
        buros = buros.filter(nombre_buro__icontains=q)
    return render(request, 'leads/listar_buros.html', {
        'buros': buros, 'f_q': q,
        'total': Buro.objects.count(),
        'activos': Buro.objects.filter(estado='ACTIVO').count(),
    })


@rol_requerido('Gerente General')
def crear_editar_buro(request, id_buro=None):
    buro = get_object_or_404(Buro, id_buro=id_buro) if id_buro else None
    if request.method == 'POST':
        form = BuroForm(request.POST, instance=buro)
        if form.is_valid():
            form.save()
            return redirect('listar_buros')
    else:
        form = BuroForm(instance=buro)
    return render(request, 'leads/form_buro.html', {'form': form, 'es_edicion': bool(id_buro)})
