"""CRUD del catálogo de motivos de contrato, con métricas de uso."""

from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Count, Sum
from ..models import MotivoContrato, Leads
from ..forms.motivos import MotivoContratoForm
from ..decoradores import rol_requerido


@rol_requerido('Gerente General')
def listar_motivos(request):
    q = request.GET.get('q', '').strip()
    motivos = MotivoContrato.objects.annotate(
        n_leads=Count('leads', distinct=True),
        ingresos=Sum('leads__id_acuerdo_pago__valor_total_acuerdo_pago'),
    ).order_by('motivo_contrato')
    if q:
        motivos = motivos.filter(motivo_contrato__icontains=q)

    top = list(
        MotivoContrato.objects.annotate(
            ing=Sum('leads__id_acuerdo_pago__valor_total_acuerdo_pago')
        ).values('motivo_contrato', 'ing').order_by('-ing')[:8]
    )
    return render(request, 'leads/listar_motivos.html', {
        'motivos': motivos, 'f_q': q,
        'total': MotivoContrato.objects.count(),
        'total_leads': Leads.objects.count(),
        'top': top,
    })


@rol_requerido('Gerente General')
def crear_editar_motivo(request, id_contrato=None):
    motivo = get_object_or_404(MotivoContrato, id_contrato=id_contrato) if id_contrato else None
    if request.method == 'POST':
        form = MotivoContratoForm(request.POST, instance=motivo)
        if form.is_valid():
            form.save()
            return redirect('listar_motivos')
    else:
        form = MotivoContratoForm(instance=motivo)
    return render(request, 'leads/form_motivo.html', {'form': form, 'es_edicion': bool(id_contrato)})
