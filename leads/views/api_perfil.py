import jwt
from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from ..models import Usuario, Leads, Telefonos, FechasPago, ReporteGrafico
from .api_auth import validar_token

@api_view(['GET', 'PUT', 'POST'])
@validar_token
def api_perfil_cliente(request):
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return Response({"error": "Token no proporcionado"}, status=status.HTTP_401_UNAUTHORIZED)
    
    token = auth_header.split(' ')[1]
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get('id_usuario')
        
        usuario_db = Usuario.objects.get(pk=user_id)
        persona = usuario_db.id_persona
        
        lead = Leads.objects.filter(id_persona=persona).first()
        estado_lead = lead.estado_lead if lead else "NUEVO"
        id_lead = lead.id_lead if lead else 0
        
        # Teléfonos
        tel_principal = ""
        tel_secundario = ""
        if persona:
            tels = Telefonos.objects.filter(id_persona=persona)
            for t in tels:
                if t.tipo_telefono and t.tipo_telefono.upper() == 'PRINCIPAL':
                    tel_principal = t.numero_telefono
                elif t.tipo_telefono and t.tipo_telefono.upper() == 'SECUNDARIO':
                    tel_secundario = t.numero_telefono

        # Plan de Pagos
        pagos_data = []
        if lead and lead.id_acuerdo_pago:
            fechas_pago = FechasPago.objects.filter(id_acuerdo_pago=lead.id_acuerdo_pago)
            for fp in fechas_pago:
                pagos_data.append({
                    "fecha": str(fp.fecha_pago),
                    "valor": str(fp.valor_fecha_pago),
                    "estado": fp.estado_pago or "PENDIENTE"
                })

        # Documentos reales desde ReporteGrafico (evidencias del lead)
        docs_data = []
        if lead:
            reportes = ReporteGrafico.objects.filter(id_lead=lead)
            for r in reportes:
                if r.documento_reporte_grafico:
                    docs_data.append({
                        "tipo": r.tipo_reporte_grafico or "Evidencia Adjunta",
                        "url": request.build_absolute_uri(r.documento_reporte_grafico.url)
                    })

        if request.method == 'GET':
            return Response({
                "id_lead": id_lead,
                "nombres": persona.nombres if persona else "",
                "apellidos": persona.apellidos if persona else "",
                "documento": persona.numero_documento_persona if persona else "",
                "direccion": persona.direccion_persona if persona else "",
                "correo": persona.correo_persona if persona else "",
                "estado_lead": estado_lead,
                "telefono_principal": tel_principal,
                "telefono_secundario": tel_secundario,
                "plan_pagos": pagos_data,
                "documentos": docs_data
            }, status=status.HTTP_200_OK)

        elif request.method == 'PUT':
            if persona:
                persona.direccion_persona = request.data.get('direccion', persona.direccion_persona)
                persona.save()
                
                nuevo_tel_sec = request.data.get('telefono_secundario', '')
                if nuevo_tel_sec:
                    tel_obj, created = Telefonos.objects.get_or_create(
                        id_persona=persona, 
                        tipo_telefono='SECUNDARIO',
                        defaults={'numero_telefono': nuevo_tel_sec}
                    )
                    if not created:
                        tel_obj.numero_telefono = nuevo_tel_sec
                        tel_obj.save()

            return Response({"mensaje": "Datos actualizados correctamente"}, status=status.HTTP_200_OK)

        elif request.method == 'POST':
            # Subir nuevo documento adicional por parte del cliente
            archivo = request.FILES.get('documento')
            tipo = request.data.get('tipo', 'DOCUMENTO CLIENTE')
            if lead and archivo:
                ReporteGrafico.objects.create(
                    id_lead=lead,
                    documento_reporte_grafico=archivo,
                    tipo_reporte_grafico=tipo
                )
                return Response({"mensaje": "Documento cargado con éxito"}, status=status.HTTP_201_CREATED)
            return Response({"error": "No se adjuntó ningún archivo"}, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)