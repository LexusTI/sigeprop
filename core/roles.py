from rolepermissions.roles import AbstractUserRole


class Master(AbstractUserRole):
    available_permissions = {
        'ver_perfil': True,
        'cadastrar': True,'editar':True,'ver': True,'deletar': True,
        'cadastrar_usuario': True,'editar_usuario':True,'ver_usuario': True,'deletar_usuario': True,'atv_inatv_usuario': True,
        'cadastrar_audiencia': True,'editar_audiencia':True,'ver_audiencia': True,'deletar_audiencia': True,
        'cadastrar_evento': True,'editar_evento':True,'ver_evento': True,'deletar_evento': True,
        'cadastrar_armamento': True,'editar_armamento':True,'ver_armamento': True,'deletar_armamento': True,
        'editar_perfil':True
    }
class Administrador(AbstractUserRole):
    available_permissions = {
        'ver_perfil': True,
        'cadastrar': True,'editar':True,'ver': True,'deletar': True,
        'cadastrar_usuario': True,'editar_usuario':True,'ver_usuario': True,'atv_inatv_usuario': True,
        'cadastrar_audiencia': True,'editar_audiencia':True,'ver_audiencia': True,'deletar_audiencia': True,
        'cadastrar_evento': True,'editar_evento':True,'ver_evento': True,'deletar_evento': True,
        'cadastrar_armamento': True,'editar_armamento':True,'ver_armamento': True,'deletar_armamento': True,
        'editar_perfil':True
    }

class Comum(AbstractUserRole):
    available_permissions = {
        'ver': True,
        'ver_perfil': True,
        'ver_audiencia': True,
        'ver_evento': True,
        'editar_perfil':True
    }
