from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Count
from ..models import Sede, Trabajador
from ..forms.sedes import SedeForm
from ..decoradores import rol_requerido


@rol_requerido('Gerente General')
def listar_sedes(request):
    q = request.GET.get('q', '').strip()
    sedes = Sede.objects.select_related('id_responsable').annotate(
        n_trab=Count('trabajador')
    ).order_by('nombre_sede')
    if q:
        sedes = sedes.filter(nombre_sede__icontains=q)

    por_sede = list(
        Sede.objects.annotate(n=Count('trabajador')).values('nombre_sede', 'n').order_by('-n')[:8]
    )
    return render(request, 'leads/listar_sedes.html', {
        'sedes': sedes, 'f_q': q,
        'total_sedes': Sede.objects.count(),
        'total_trabajadores': Trabajador.objects.count(),
        'por_sede': por_sede,
    })


@rol_requerido('Gerente General')
def crear_editar_sede(request, id_sede=None):
    sede = get_object_or_404(Sede, id_sede=id_sede) if id_sede else None

    if request.method == 'POST':
        form = SedeForm(request.POST, instance=sede)
        if form.is_valid():
            obj = form.save(commit=False)
            trab = form.cleaned_data.get('responsable_trab')
            obj.id_responsable = trab.id_persona if trab else None
            obj.save()

            if trab:
                # El responsable debe trabajar en la sede que dirige:
                # 1) soltarlo como responsable de cualquier otra sede
                Sede.objects.filter(id_responsable=trab.id_persona).exclude(pk=obj.pk).update(id_responsable=None)
                # 2) asignarle esta sede como su lugar de trabajo
                if trab.id_sede_id != obj.pk:
                    trab.id_sede = obj
                    trab.save()

            return redirect('listar_sedes')
    else:
        inicial = {}
        if sede and sede.id_responsable:
            t = Trabajador.objects.filter(id_persona=sede.id_responsable).first()
            if t:
                inicial['responsable_trab'] = t.pk
        form = SedeForm(instance=sede, initial=inicial)

    return render(request, 'leads/form_sede.html', {'form': form, 'es_edicion': bool(id_sede), 'sede': sede})
