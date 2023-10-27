from django.contrib import admin
from .models import ConfiguracoesSite,Estado,Cidade,Unidade,Perfil,Usuario,Audiencia,Audiencia_Usuario,Evento,Armamento
# Register your models here.

@admin.register(ConfiguracoesSite)
class ConfiguracoesAdmin(admin.ModelAdmin):
    list_display = ("__str__",'notificar_email','notificar_whatsapp')
    list_filter = ()
    list_editable = ('notificar_email','notificar_whatsapp')
    list_display_links = ()
    search_fields = ()

@admin.register(Estado)
class EstadoAdmin(admin.ModelAdmin):
    list_display = ("__str__",'nome','sigla')
    list_filter = ()
    list_editable = ('nome','sigla')
    list_display_links = ()
    search_fields = ()

@admin.register(Cidade)
class CidadeAdmin(admin.ModelAdmin):
    list_display = ("__str__",'nome','estado')
    list_filter = ('estado',)
    list_editable = ('nome',)
    list_display_links = ()
    search_fields = ()

@admin.register(Unidade)
class UnidadeAdmin(admin.ModelAdmin):
    list_display = ("__str__",'sigla','estado','status')
    list_filter = ()
    list_editable = ('status',)
    list_display_links = ()
    search_fields = ()

@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ("__str__",'perfil','pelotao','matricula','cpf','rg','telefone')
    list_filter = ('pelotao',)
    list_editable = ('pelotao','matricula','cpf','rg','telefone')
    list_display_links = ()
    search_fields = ('perfil__user__first_name',)

@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ("__str__",'foto')
    list_filter = ()
    list_editable = ()
    list_display_links = ()
    search_fields = ('user__first_name',)

@admin.register(Audiencia)
class AudienciaAdmin(admin.ModelAdmin):
    list_display = ("__str__",'data_do_processo','local')
    list_filter = ('local','data_do_processo')
    list_editable = ('local',)
    list_display_links = ()
    search_fields = ('numero_do_processo','local','data_do_processo','interessados__perfil__user__first_name')

@admin.register(Audiencia_Usuario)
class AudienciaAdmin(admin.ModelAdmin):
    list_display = ("__str__",'usuario','audiencia')
    list_filter = ('usuario',)
    list_editable = ()
    list_display_links = ()
    search_fields = ('usuario__perfil__user__first_name','audiencia')

@admin.register(Evento)
class EventoAdmin(admin.ModelAdmin):
    list_display = ("__str__",'nome','numero_do_processo','local')
    list_filter = ('local','numero_do_processo','data_do_evento')
    list_editable = ('local','nome')
    list_display_links = ()
    search_fields = ('numero_do_processo','local','data_do_processo','interessados__perfil__user__first_name')

@admin.register(Armamento)
class ArmamentoAdmin(admin.ModelAdmin):
    list_display = ("__str__",'numero_de_registro','tipo_de_arma','status_da_arma','usuario_atual')
    list_filter = ('tipo_de_arma','status_da_arma','usuario_atual')
    list_editable = ('status_da_arma',)
    list_display_links = ()
    search_fields = ('numero_de_registro','tipo_de_arma')