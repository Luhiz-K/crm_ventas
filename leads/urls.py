from django.urls import path
from .views.panel_control import panel_control
from .views.captura_inicial import iniciar_captura_lead, verificar_telefono, verificar_documento
from .views.wizard import wizard_lead, iniciar_edicion_lead
# --- Flujos viejos apartados: reemplazados por el wizard ---
# from .views.registro_persona_nueva import registro_persona_nueva
# from .views.registro_plataformas import registro_plataformas
# from .views.crear_acuerdo import crear_acuerdo_pago
from .views.ciudades import listar_ciudades, crear_editar_ciudad
from .views.sedes import listar_sedes, crear_editar_sede
from .views.trabajadores import listar_trabajadores, crear_editar_trabajador
from .views.servicios import listar_servicios, crear_editar_servicio
from .views.motivos import listar_motivos, crear_editar_motivo
from .views.buros import listar_buros, crear_editar_buro
from .views.leads import listar_leads, detalle_lead
from .views.editar_lead import editar_lead, registrar_pago, eliminar_pago
from .views.ver_lead import ver_lead
from .views.ciudades import eliminar_ciudad
# --- APIs apartadas por ahora (se reactivarán con la app / IA externa) ---
# from .views.api_ciudades import ciudad_api_list, ciudad_api_detail
# from .views.api_auth import login_usuario
# from .views.api_perfil import api_perfil_cliente
from .views.auth_web import login_web, logout_web

urlpatterns = [
    path('', panel_control, name='panel_control'),
    path('login/', login_web, name='login'),
    path('logout/', logout_web, name='logout'),
    path('nuevo/', iniciar_captura_lead, name='captura_inicial'),
    path('nuevo/paso/<int:paso>/', wizard_lead, name='wizard_lead'),
    # path('registro-persona/', registro_persona_nueva, name='registro_persona_nueva'),
    # path('plataformas/<int:id_lead>/', registro_plataformas, name='registro_plataformas'),
    # path('crear-acuerdo/<int:id_lead>/', crear_acuerdo_pago, name='crear_acuerdo_pago'),
    path('ciudades/', listar_ciudades, name='listar_ciudades'),
    path('ciudades/nueva/', crear_editar_ciudad, name='crear_ciudad'),
    path('ciudades/editar/<int:id_ciudad>/', crear_editar_ciudad, name='editar_ciudad'),
    path('sedes/', listar_sedes, name='listar_sedes'),
    path('sedes/nueva/', crear_editar_sede, name='crear_sede'),
    path('sedes/editar/<int:id_sede>/', crear_editar_sede, name='editar_sede'),
    path('trabajadores/', listar_trabajadores, name='listar_trabajadores'),
    path('trabajadores/nueva/', crear_editar_trabajador, name='crear_trabajador'),
    path('trabajadores/editar/<int:id_trabajador>/', crear_editar_trabajador, name='editar_trabajador'),
    path('productos/', listar_servicios, name='listar_servicios'),
    path('productos/nuevo/', crear_editar_servicio, name='crear_servicio'),
    path('productos/editar/<int:id_servicio>/', crear_editar_servicio, name='editar_servicio'),
    path('motivos/', listar_motivos, name='listar_motivos'),
    path('motivos/nuevo/', crear_editar_motivo, name='crear_motivo'),
    path('motivos/editar/<int:id_contrato>/', crear_editar_motivo, name='editar_motivo'),
    path('buros/', listar_buros, name='listar_buros'),
    path('buros/nuevo/', crear_editar_buro, name='crear_buro'),
    path('buros/editar/<int:id_buro>/', crear_editar_buro, name='editar_buro'),
    path('leads-historial/', listar_leads, name='listar_leads'),
    path('leads/editar/<int:id_lead>/', editar_lead, name='editar_lead'),
    path('leads/ver/<int:id_lead>/', ver_lead, name='ver_lead'),
    path('leads/editar/<int:id_lead>/iniciar/', iniciar_edicion_lead, name='iniciar_edicion'),
    path('leads/pago/<int:id_fecha_pago>/', registrar_pago, name='registrar_pago'),
    path('leads/pago/eliminar/<int:id_pago>/', eliminar_pago, name='eliminar_pago'),
    path('leads/detalle/<int:id_lead>/', detalle_lead, name='detalle_lead'),
    path('leads/verificar-telefono/', verificar_telefono, name='verificar_telefono'),
    path('leads/verificar-documento/', verificar_documento, name='verificar_documento'),
    path('ciudades/eliminar/<int:id_ciudad>/', eliminar_ciudad, name='eliminar_ciudad'),
    # path('api/ciudades/', ciudad_api_list, name='api_ciudades_list'),
    # path('api/ciudades/<int:pk>/', ciudad_api_detail, name='api_ciudades_detail'),
    # path('api/auth/login/', login_usuario, name='api_login'),
    # path('api/perfil/', api_perfil_cliente, name='api_perfil_cliente'),
]
