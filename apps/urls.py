from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from . import views

urlpatterns = [
    #path("precad_est_cid/",views.cdt_estados_cidades,),
    #Autenticar
    path("accounts/login/",views.logar,name='login'),
    path('accounts/recuperacao/',views.recuperar_senha,name='recuperar_senha'),
    path('RedefinirSenha/<str:user_email>',views.redefinir_senha,name='redefinir_senha'),
    path("sair/",views.sair,name='sair'),
    #Home
    path("", views.home,name='home'),
    #Usuario
    path("home/usuarios/", views.listar_usuarios,name='listar_usuario'),
    path("ver/perfil/<int:id>",views.ver_perfil,name='perfil'),
    path("cadastrar/Usuario/",views.cdt_usuario,name='cdt_usuario'),
    path("editar/Usuario/<int:id>",views.edt_usuario,name='edt_usuario'),
    path("ver/Usuario/<int:id>",views.ver_usuario,name='ver_usuario'),
    path("deletar/Usuario/<int:id>",views.del_usuario,name='del_usuario'),
    path("atv_inatv/Usuario/<int:id>",views.atv_inatv_usuario,name='atv_inatv_usuario'),
    #Audiencias
    path("home/audiencias/", views.listar_audiencias,name='listar_audiencia'),
    path("cadastrar/AudienciaJudicial/",views.cdt_audiencia_judicial,name='cdt_audiencia'),
    path("editar/AudienciaJudicial/<int:id>",views.edt_audiencia_judicial,name='edt_audiencia'),
    path("ver/Audiencia/<int:id>",views.ver_audiencia,name='ver_audiencia'),
    path("deletar/Audiencia/<int:id>",views.del_audiencia,name='del_audiencia'),
    path("cancelar/Audiencia/<int:id>",views.cancelar_audiencia_judicial,name='cancelar_audiencia'),
    path("remarcar/Audiencia/<int:id>",views.remarcar_audiencia_judicial,name='remarcar_audiencia'),
    #Armamento
    path("home/armamentos/", views.listar_armamentos,name='listar_armamento'),
    path("cadastrar/Armamento/",views.cdt_armamento,name='cdt_armamento'),
    path("editar/Armamento/<int:id>",views.edt_armamento,name='edt_armamento'),
    path("ver/Armamento/<int:id>",views.ver_armamento,name='ver_armamento'),
    path("deletar/Armamento/<int:id>",views.del_armamento,name='del_armamento'),
    #Eventos
    path("home/eventos/", views.listar_eventos,name='listar_evento'),
    path("cadastrar/Evento/",views.cdt_evento,name='cdt_evento'),
    path("editar/Evento/<int:id>",views.edt_evento,name='edt_evento'),
    path("ver/Evento/<int:id>",views.ver_evento,name='ver_evento'),
    path("deletar/Evento/<int:id>",views.del_evento,name='del_evento'),
    #Notificar mais de um
    path("home/NotificarAudienciaEmail/<int:id>", views.notificar_audiencia_email,name='notificar_audiencia_email'),
    path("home/NotificarAudienciaWhatsapp/<int:id>", views.notificar_audiencia_whatsapp,name='notificar_audiencia_whatsapp'),
    #Notificar audiencia apenas um
    path("home/NotificarAudienciaEmail/<int:audiencia_id>/<int:usuario_id>", views.ntf_audiencia_email_individual,name='ntf_audiencia_email_individual'),
    path("home/NotificarAudienciaWhatsapp/<int:audiencia_id>/<int:usuario_id>", views.ntf_audiencia_whatsapp_individual,name='ntf_audiencia_whatsapp_individual'),
    #Notificar Evento apenas um
    path("home/NotificarEventoEmail/<int:evento_id>/<int:usuario_id>", views.ntf_evento_email_individual,name='ntf_evento_email_individual'),
    path("home/NotificarEventoWhatsapp/<int:evento_id>/<int:usuario_id>", views.ntf_evento_whatsapp_individual,name='ntf_evento_whatsapp_individual'),
]