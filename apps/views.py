from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate,login,logout
    
from django.db.models import Q
from django.shortcuts import render,redirect,get_object_or_404

from django.core.paginator import Paginator
from django.core.mail import send_mail, EmailMessage
from django.core.validators import validate_email

from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.urls import reverse

from rolepermissions.decorators import has_permission_decorator
from rolepermissions.roles import assign_role,clear_roles
from hashlib import sha256
from datetime import date,datetime,timedelta

from .models import Cidade,Estado,Usuario,Perfil, Audiencia,Audiencia_Usuario,Documento,Token_redefinicao,ConfiguracoesSite,Evento,Armamento
from .forms import NotificarForm, UserModelForm,PerfilModelForm,UsuarioModelForm,AudienciaModelForm,EventoModelForm,ArmamentoModelForm


from . import verificacoes

from django.views.generic.list import ListView

@login_required(login_url='login')
@has_permission_decorator(permission_name='ver_audiencia')
def home(request):
    
    if request.user.is_superuser or not request.user.groups.first().name=='comum':
        audiencias= Audiencia.objects.all().order_by('data_do_processo')
        audiencias_proximas= Audiencia.objects.filter(Q(data_do_processo__gte=date.today())).order_by('data_do_processo')[:5]#limitada a 5
        eventos=Evento.objects.all().order_by('data_do_evento')
        eventos_proximos= Evento.objects.filter(Q(data_do_evento__gte=date.today())).order_by('data_do_evento')[:5]#limitada a 5
    else:
        audiencias=Audiencia.objects.filter(Q(interessados__perfil__user=request.user)).order_by('data_do_processo')
        audiencias_proximas= Audiencia.objects.filter(Q(interessados__perfil__user=request.user,data_do_processo__gte=date.today())).order_by('data_do_processo')[:5]
        eventos=Evento.objects.filter(Q(interessados__perfil__user=request.user)).order_by('data_do_evento')
        eventos_proximos= Evento.objects.filter(Q(interessados__perfil__user=request.user,data_do_evento__gte=date.today())).order_by('data_do_evento')[:5]#limitada a 5
    
    context={
        'audiencias':audiencias,
        'audiencias_proximas':audiencias_proximas,
        'eventos':eventos,
        'eventos_proximos':eventos_proximos,
    }
    return render(request,'home.html',context)

###########Autenticação#############################
def logar(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method=='POST':
        email = request.POST.get('email')
        senha = request.POST.get('senha')
        if len(email.strip())==0 | len(senha.strip())==0:
            messages.error(request,'Campos vazios')
            return redirect('login')
        try:
            validate_email(email)
        except:
            messages.error(request,'E-mail não é válido')
            return redirect('login')
        usuario = authenticate(username=email,password=senha)
        if not usuario:
            messages.error(request, 'Email ou senha incorretos.')
            return redirect('login')
        else:
            login(request, usuario)
            if usuario.is_superuser:
                return redirect('admin:index')
            else:
                return redirect('home')
    return render(request,'autenticacao/login.html')

def sair(request):
    logout(request)
    return redirect('login')

def recuperar_senha(request):
    if request.method=='POST':
        email= request.POST.get('email')
        try:
           user= get_object_or_404(User,email=email)
        except:
            messages.error(request, 'Usuário não encontrado!')
            return redirect('login')
        try:
            if ConfiguracoesSite.objects.filter(notificar_email=False):
                messages.warning(request,'Função de notificação por E-mail temporariamente desativada!')
            else:
                if Token_redefinicao.objects.filter(user=user).exists():
                    token_user=get_object_or_404(Token_redefinicao,user=user)
                    if token_user.usado:
                        token=sha256(f'{user.email.encode()}{str(date.today())}'.encode()).hexdigest()
                        token_user.token=token
                        token_user.usado=False
                        token_user.save()
                    else:
                        token=token_user.token  
                else:
                    token=sha256(f'{user.email.encode()}{str(date.today())}'.encode()).hexdigest()
                    Token_redefinicao.objects.create(
                        token=token,
                        user=user
                    )
                titulo='Recuperação de senha'
                html_conteudo=render_to_string('msgs_email/recuperacao_senha.html',{'nome':user.first_name,'token':token})
                mensagem=strip_tags(html_conteudo)
                send_mail(titulo,mensagem,settings.EMAIL_HOST_USER,recipient_list=[user.email])
                return render(request,'autenticacao/recuperacao_realizada.html')
        except:
            messages.error(request, 'Erro interno no sistema!')
            return redirect('login')

    return render(request,'autenticacao/recuperar_senha.html')

def redefinir_senha(request,user_email=''):
    try:
        if Token_redefinicao.objects.filter(token=user_email).exists():
            token_user=get_object_or_404(Token_redefinicao,token=user_email)
            user=token_user.user
            if token_user.usado:
                messages.error(request,'Token já usado!')
                return redirect('login')
        else:
            messages.error(request,'Token não existe!')
            return redirect('login')
    except:
        messages.error(request,'Erro interno no sistema!')
        return redirect('login')
    if request.method=='POST':
        senha= request.POST.get('senha')
        senha2= request.POST.get('confirmar-senha')
        if senha != senha2:
            messages.error(request, 'Senhas não são iguais')
            return render(request,'autenticacao/redefinir_senha.html',{'user_email':user_email})
        else:
            user.set_password(senha)
            user.save()
            if ConfiguracoesSite.objects.filter(notificar_email=False):
                messages.warning(request,'Função de notificação por E-mail temporariamente desativada!')
            else:
                titulo='Confirmação de recuperação de senha'
                html_conteudo=render_to_string('msgs_email/confirmacao_recuperacao.html',{'nome':user.first_name})
                mensagem=strip_tags(html_conteudo)
                send_mail(titulo,mensagem,settings.EMAIL_HOST_USER,recipient_list=[user.email])
                token_user=get_object_or_404(Token_redefinicao,user=user)
                token_user.usado=True
                token_user.save()
                messages.success(request,'Senha alterada com sucesso!')
                return redirect('login')
        
    return render(request,'autenticacao/redefinir_senha.html',{'user_email':user_email})



########################### USUÁRIO ################################
@login_required(login_url='login')
@has_permission_decorator(permission_name='ver_usuario')
def listar_usuarios(request):
    if request.GET.get('pesquisa_usuario'):
        pesquisa = request.GET.get('pesquisa_usuario')
        if pesquisa.lower()=='inativo':
            usuarios= Usuario.objects.filter(Q(perfil__user__is_active=False)).order_by('perfil__user__first_name')
        else:
            usuarios = Usuario.objects.filter(Q(perfil__user__first_name__icontains=pesquisa)
                                            | Q(perfil__user__last_name__icontains=pesquisa)
                                            | Q(pelotao__icontains=pesquisa) 
                                            | Q(matricula__icontains=pesquisa)
                                            | Q(cpf__icontains=pesquisa)
                                            | Q(rg__icontains=pesquisa)).order_by('perfil__user__first_name')
    else:
        usuarios = Usuario.objects.all().order_by('perfil__user__first_name')
    pagina=request.GET.get('page','1')
    mostrar=request.GET.get('mostrar','10')
    usuarios_lista=Paginator(usuarios,mostrar)
    try:
        usuarios=usuarios_lista.page(pagina)
    except:
        usuarios= usuarios_lista.page(1)
    return render(request,'listar/usuarios.html',{'usuarios':usuarios})

@login_required(login_url='login')
@has_permission_decorator(permission_name='ver_usuario')
def ver_usuario(request,id):
    try:
        usuario=get_object_or_404(Usuario,pk=id)
    except:
        messages.error(request,'Usuário não existe!')
        return redirect('listar_usuario')
    return render(request,'ver/usuario.html',{'usuario':usuario})

@login_required(login_url='login')
@has_permission_decorator(permission_name='cadastrar_usuario')
def cdt_usuario(request):
    if request.method=='POST':
        nome=request.POST.get('nome')
        sobrenome=request.POST.get('sobrenome')
        email=request.POST.get('email')
        senha=request.POST.get('senha')
        pelotao=request.POST.get('pelotao')
        matricula=request.POST.get('matricula')
        cpf=request.POST.get('cpf')
        rg=request.POST.get('rg')
        telefone=request.POST.get('telefone')
        foto=request.FILES.get('foto')
        tipo_usuario=request.POST.get('tipo_usuario')
        #VERIFICAÇÕES
        verificacao=verificacoes.verificar_campos_vazios(nome,sobrenome,email,senha,pelotao,matricula,cpf,rg,telefone)
        if verificacao!=False:
            messages.error(request,verificacao)
            return redirect('cdt_usuario')
        verificacao=verificacoes.verificar_senha(senha)
        if verificacao!=False:
            messages.error(request,verificacao)
            return redirect('cdt_usuario')
        try:
            validate_email(email)
        except:
            messages.error(request,'E-mail inválido')
            return redirect('cdt_usuario')
        if User.objects.filter(email=email).exists():
            messages.error(request,'E-mail já cadastrado')
            return redirect('cdt_usuario')
        #FIM DAS VERIFICAÇÕES
        try:
            user = User.objects.create_user(
            username=email,
            first_name=nome,
            last_name=sobrenome,
            email=email,
            password=senha
            )
            if tipo_usuario=='1':
                assign_role(user,'comum')
            elif tipo_usuario=='2':
                assign_role(user,'administrador')
            else:
                messages.error(request,'Tipo de usuário não existe!')
                return redirect('home')
            perfil = Perfil.objects.create(
                user=user,
                foto=foto
            )
            usuario= Usuario.objects.create(
                perfil=perfil,
                pelotao=pelotao,
                matricula=matricula,
                cpf=cpf,
                rg=rg,
                telefone=telefone
            )
            messages.success(request,f'{nome} cadastrado com sucesso!')
            return redirect('listar_usuario')
        except:
            if user:
                user.delete()
            messages.error(request,'Ocorreu algum erro no cadastro!')
            return redirect('home')
        
    return render(request, 'cadastrar/cadastrar_usuario.html')

@login_required(login_url='login')
@has_permission_decorator(permission_name='editar_usuario')
def edt_usuario(request,id):
    try:
        usuario=get_object_or_404(Usuario,pk=id)
    except:
        messages.error(request,'Usuário não existe!')
        return redirect('listar_usuario')
    context={
        'usuario':usuario
    }
    if request.method=='POST':
        nome=request.POST.get('nome')
        sobrenome=request.POST.get('sobrenome')
        email=request.POST.get('email')
        pelotao=request.POST.get('pelotao')
        matricula=request.POST.get('matricula')
        cpf=request.POST.get('cpf')
        rg=request.POST.get('rg')
        telefone=request.POST.get('telefone')
        foto=request.FILES.get('foto')
        tipo_usuario=request.POST.get('tipo_usuario')
        #VERIFICAÇÕES
        verificacao=verificacoes.verificar_campos_vazios(nome,sobrenome,email,pelotao,matricula,cpf,rg,telefone)
        if verificacao!=False:
            messages.error(request,verificacao)
            return redirect('edt_usuario',context)
        if usuario.perfil.user.email != email:
            if User.objects.exclude(email=usuario.perfil.user.email).filter(email=email):
                messages.error(request,'E-mail já cadastrado')
                return redirect('edt_usuario',context)
            try:
                validate_email(email)
            except:
                messages.error(request,'E-mail inválido')
                return redirect('edt_usuario',context)
        #FIM DAS VERIFICAÇÕES
        try:
            usuario.perfil.user.username=email
            usuario.perfil.user.first_name=nome
            usuario.perfil.user.last_name=sobrenome
            usuario.perfil.user.email=email
            if request.POST.get('foto-clear'):
                usuario.perfil.foto.delete()
            usuario.perfil.foto=foto
            usuario.pelotao=pelotao
            usuario.matricula=matricula
            usuario.cpf=cpf
            usuario.rg=rg
            usuario.telefone=telefone
            if tipo_usuario=='1':
                clear_roles(usuario.perfil.user)
                assign_role(usuario.perfil.user,'comum')
            elif tipo_usuario=='2':
                clear_roles(usuario.perfil.user)
                assign_role(usuario.perfil.user,'administrador')
            else:
                messages.error(request,'Tipo de usuário não existe!')
                return redirect('edt_usuario',context)
            usuario.perfil.user.save()
            usuario.perfil.save()
            usuario.save()
            messages.success(request,f'{nome} editado com sucesso!')
            return redirect('ver_usuario',usuario.id)
        except:
            messages.error(request,'Ocorreu algum erro na edição do usuário!')
            return redirect('edt_usuario',context)
    
    return render(request, 'editar/usuario.html',context)

@login_required(login_url='login')
@has_permission_decorator(permission_name='deletar_usuario')
def del_usuario(request,id):
    try:
        usuario=get_object_or_404(Usuario,pk=id)
        usuario.perfil.user.delete()
        messages.success(request,'Usuário deletado com sucesso')
        return redirect('listar_usuario')
    except:
        messages.error(request,'Erro ao inativar usuário!')
        return redirect('home')

@login_required(login_url='login')
@has_permission_decorator(permission_name='ver_perfil')
def ver_perfil(request,id):
    try:
        usuario=get_object_or_404(Usuario,pk=id)
    except:
        messages.error(request,'Usuário não existe!')
        return redirect('perfil')
    return render(request,'ver/perfil.html',{'usuario':usuario})
################### ATIVAR / DESATIVAR ##################################
@login_required(login_url='login')
@has_permission_decorator(permission_name='atv_inatv_usuario')
def atv_inatv_usuario(request,id):
    try:
        usuario=get_object_or_404(Usuario,pk=id)
        if usuario.perfil.user.is_active==True:
            usuario.perfil.user.is_active=False
            messages.success(request,'Usuário inativado')
        else:
            usuario.perfil.user.is_active=True
            messages.success(request,'Usuário ativado')
        usuario.perfil.user.save()
        return redirect('listar_usuario')
    except:
        messages.error(request,'Erro ao inativar usuário!')
        return redirect('home')
########################### AUDIENCIA ################################
@login_required(login_url='login')
@has_permission_decorator(permission_name='ver_audiencia')
def listar_audiencias(request):
    if request.GET.get('pesquisa_audiencia'):
        pesquisa = request.GET.get('pesquisa_audiencia')
        if request.user.is_superuser or not request.user.groups.first().name=='comum':
            audiencias = Audiencia.objects.filter(Q(numero_do_processo__icontains=pesquisa) | 
                                                  Q(interessados__perfil__user__first_name__icontains=pesquisa)).order_by('data_do_processo')
            audiencias_proximas= Audiencia.objects.filter(Q(data_do_processo__gte=date.today())).order_by('data_do_processo')[:5]#limitada a 5
        else:
            audiencias=Audiencia.objects.filter(Q(interessados__perfil__user=request.user,numero_do_processo__icontains=pesquisa)).order_by('data_do_processo')
            audiencias_proximas= Audiencia.objects.filter(Q(interessados__perfil__user=request.user,data_do_processo__gte=date.today())).order_by('data_do_processo')[:5]#limitada a 5 
    else:
        if request.user.is_superuser or not request.user.groups.first().name=='comum':
            audiencias= Audiencia.objects.all().order_by('data_do_processo')
            audiencias_proximas= Audiencia.objects.filter(Q(data_do_processo__gte=date.today())).order_by('data_do_processo')[:5]#limitada a 5
        else:
            audiencias=Audiencia.objects.filter(Q(interessados__perfil__user=request.user)).order_by('data_do_processo')
            audiencias_proximas= Audiencia.objects.filter(Q(interessados__perfil__user=request.user,data_do_processo__gte=date.today())).order_by('data_do_processo')[:5]#limitada a 5
                
  
    pagina=request.GET.get('page','1')
    mostrar=request.GET.get('mostrar','10')
    audiencias_lista=Paginator(audiencias,mostrar)
    try:
        audiencias=audiencias_lista.page(pagina)
    except:
        audiencias= audiencias_lista.page(1)
    
    context={
        'audiencias':audiencias,
        'audiencias_proximas':audiencias_proximas
    }
    return render(request,'listar/audiencias.html',context)

@login_required(login_url='login')
@has_permission_decorator(permission_name='ver_audiencia')
def ver_audiencia(request,id):
    try:
        audiencia=get_object_or_404(Audiencia,pk=id)
    except:
        messages.error(request,'Audiência não existe!')
        return redirect('listar_audiencia')
    if not request.user.is_staff:
        if request.user.groups.first().name=='comum':
            if not audiencia.interessados.filter(perfil__user=request.user).exists():
                return redirect('home')
    audiencia_usuarios=Audiencia_Usuario.objects.filter(audiencia=audiencia)
    context={
        'audiencia':audiencia,
        'audiencia_usuarios':audiencia_usuarios
    }
    return render(request,'ver/audiencia.html',context)


@login_required(login_url='login')
@has_permission_decorator(permission_name='cadastrar_audiencia')
def cdt_audiencia_judicial(request):
    if request.method=='POST':
        numero_do_processo= request.POST.get('numero_do_processo')
        documentos= request.FILES.getlist('documento')
        data_do_processo= request.POST.get('data_do_processo')
        local=request.POST.get('local')
        interessados=request.POST.getlist('interessados')
        #VERIFICAÇÕES
        verificacao=verificacoes.verificar_campos_vazios(numero_do_processo,data_do_processo,local)
        if verificacao!=False:
            messages.error(request,verificacao)
            return redirect('cdt_audiencia')
        try:
            datetime.strptime(data_do_processo,"%Y-%m-%dT%H:%M")
        except:
            messages.error(request,'Data inválida!')
            return redirect('cdt_audiencia')
        
        try:
            for interessado_id in interessados:
                get_object_or_404(Usuario,pk=interessado_id)
        except:
            messages.error(request,'Interessado inexistente!')
            return redirect('cdt_audiencia')
        #FIM DAS VERIFICAÇÕES
        notificar_whatsapp=request.POST.get('notificar_whatsapp')
        notificar_email=request.POST.get('notificar_email')

        try:
            audiencia=Audiencia.objects.create(
                numero_do_processo=numero_do_processo,
                data_do_processo=data_do_processo,
                local=local
            )
            try:
                for documento in documentos:
                    audiencia.documento.add(Documento.objects.create(documento=documento))
                    audiencia.save()
            except:
                messages.error(request,'Erro ao atribuir documentos à audiência')
            for interassado_id in interessados:
                audiencia.interessados.add(get_object_or_404(Usuario,pk=interassado_id))
                audiencia.save()
            if notificar_whatsapp=='on':
                notificar_audiencia_whatsapp(request,audiencia_id=audiencia.id)
            if notificar_email=='on':
                notificar_audiencia_email(request,audiencia_id=audiencia.id)
            messages.success(request,'Processo de audiência cadastrado com sucesso!')
            return redirect('listar_audiencia')
        except:
            if audiencia:
                    audiencia.delete()
            messages.error(request,'Ocorreu algum erro no cadastro!')
            return redirect('home')
    usuarios=Usuario.objects.all().order_by('perfil__user__first_name')
    context={
        'usuarios':usuarios
    }
    return render(request, 'cadastrar/cadastrar_audiencia_judicial.html',context)

@login_required(login_url='login')
@has_permission_decorator(permission_name='editar_audiencia')
def edt_audiencia_judicial(request,id):
    try:
        audiencia=get_object_or_404(Audiencia,pk=id)
    except:
        messages.error(request,'Audiência não existe!')
        return redirect('listar_audiencia')
    audiencia_form=AudienciaModelForm(request.POST or None, request.FILES or None,instance=audiencia)
    context={
        'audiencia':audiencia,
        'audiencia_form':audiencia_form,
    }
    if request.method=='POST':
        if audiencia_form.is_valid():
            try:
                pro_audiencia=audiencia_form.save()
                messages.success(request,'Processo de audiência editado com sucesso!')
                return redirect('ver_audiencia',pro_audiencia.id)
            except:
                if pro_audiencia:
                    pro_audiencia.delete()
                messages.error(request,'Ocorreu algum erro no cadastro!')
                return redirect('home')
    return render(request, 'editar/editar_audiencia_judicial.html',context)

@login_required(login_url='login')
@has_permission_decorator(permission_name='editar_audiencia')
def cancelar_audiencia_judicial(request,id):
    try:
        audiencia=get_object_or_404(Audiencia,pk=id)
    except:
        messages.error(request,'Audiência não existe!')
        return redirect('listar_audiencia')
    audiencia.situacao='Cancelada'
    audiencia.save()

    return redirect('ver_audiencia',audiencia.id)
@login_required(login_url='login')
@has_permission_decorator(permission_name='editar_audiencia')
def remarcar_audiencia_judicial(request,id):
    try:
        audiencia=get_object_or_404(Audiencia,pk=id)
    except:
        messages.error(request,'Audiência não existe!')
        return redirect('listar_audiencia')
    audiencia_form=AudienciaModelForm(request.POST or None, request.FILES or None,instance=audiencia)
    context={
        'audiencia':audiencia,
        'audiencia_form':audiencia_form,
    }
    return render(request, 'editar/editar_audiencia_judicial.html',context)
@login_required(login_url='login')
@has_permission_decorator(permission_name='deletar_audiencia')
def del_audiencia(request,id):
    try:
        audiencia=get_object_or_404(Audiencia,pk=id)
        audiencia.delete()
        messages.success(request,'Audiência deletada com sucesso')
        return redirect('listar_audiencia')
    except:
        messages.error(request,'Erro ao deletar audiência!')
        return redirect('home')
    
########################### EVENTO ################################
@login_required(login_url='login')
@has_permission_decorator(permission_name='ver_evento')
def listar_eventos(request):
    if request.GET.get('pesquisa_evento'):
        pesquisa = request.GET.get('pesquisa_evento')
        if request.user.is_superuser or not request.user.groups.first().name=='comum':
            eventos = Evento.objects.filter(Q(numero_do_processo__icontains=pesquisa) | 
                                            Q(nome__icontains=pesquisa) | 
                                            Q(interessados__perfil__user__first_name__icontains=pesquisa)).order_by('data_do_evento')
            eventos_proximos= Evento.objects.filter(Q(data_do_evento__gte=date.today())).order_by('data_do_evento')[:5]#limitada a 5
        else:
            eventos= Evento.objects.filter(Q(interessados__perfil__user=request.user,nome__icontains=pesquisa) | 
                                           Q(interessados__perfil__user=request.user,numero_do_processo__icontains=pesquisa)).order_by('data_do_evento')
            eventos_proximos= Evento.objects.filter(Q(interessados__perfil__user=request.user,data_do_evento__gte=date.today())).order_by('data_do_evento')[:5]#limitada a 5

        
    else:
        if request.user.is_superuser or not request.user.groups.first().name=='comum':
            eventos= Evento.objects.all().order_by('data_do_evento')
            eventos_proximos= Evento.objects.filter(Q(data_do_evento__gte=date.today())).order_by('data_do_evento')[:5]#limitada a 5
        else:
            eventos= Evento.objects.filter(Q(interessados__perfil__user=request.user)).order_by('data_do_evento')
            eventos_proximos= Evento.objects.filter(Q(interessados__perfil__user=request.user,data_do_evento__gte=date.today())).order_by('data_do_evento')[:5]#limitada a 5

    pagina=request.GET.get('page','1')
    mostrar=request.GET.get('mostrar','10')
    eventos_lista=Paginator(eventos,mostrar)
    try:
        eventos=eventos_lista.page(pagina)
    except:
        eventos= eventos_lista.page(1)
    
    context={
        'eventos':eventos,
        'eventos_proximos':eventos_proximos
    }
    return render(request,'listar/eventos.html',context)


@login_required(login_url='login')
@has_permission_decorator(permission_name='ver_evento')
def ver_evento(request,id):
    try:
        evento=get_object_or_404(Evento,pk=id)
    except:
        messages.error(request,'Evento não existe!')
        return redirect('listar_evento')
    if request.user.groups.first().name=='comum':
        if not evento.interessados.filter(perfil__user=request.user).exists():
            return redirect('home')
    return render(request,'ver/evento.html',{'evento':evento})

@login_required(login_url='login')
@has_permission_decorator(permission_name='cadastrar_evento')
def cdt_evento(request):
    evento_form=EventoModelForm(request.POST or None)
    usuarios=Usuario.objects.all().order_by('perfil__user__first_name')
    context={
        'usuarios':usuarios
    }
    if request.method=='POST':
        numero_do_processo= request.POST.get('numero_do_processo')
        nome= request.POST.get('nome')
        data_do_evento= request.POST.get('data_do_evento')
        local=request.POST.get('local')
        documentos= request.FILES.getlist('documento')
        interessados=request.POST.getlist('interessados')
        #VERIFICAÇÕES
        verificacao=verificacoes.verificar_campos_vazios(numero_do_processo,data_do_evento,local)
        if verificacao!=False:
            messages.error(request,verificacao)
            return redirect('cdt_evento')
        try:
            datetime.strptime(data_do_evento,"%Y-%m-%dT%H:%M")
        except:
            messages.error(request,'Data inválida!')
            return redirect('cdt_evento')
        
        try:
            for interessado_id in interessados:
                get_object_or_404(Usuario,pk=interessado_id)
        except:
            messages.error(request,'Interessado inexistente!')
            return redirect('cdt_audiencia')
        #FIM DAS VERIFICAÇÕES
        notificar_whatsapp=request.POST.get('notificar_whatsapp')
        notificar_email=request.POST.get('notificar_email')
        try:
            evento=Evento.objects.create(
                numero_do_processo=numero_do_processo,
                nome=nome,
                data_do_evento=data_do_evento,
                local=local
            )
            try:
                for documento in documentos:
                    evento.documento.add(Documento.objects.create(documento=documento))
                    evento.save()
            except:
                messages.error(request,'Erro ao atribuir documentos ao evento')
            for interassado_id in interessados:
                evento.interessados.add(get_object_or_404(Usuario,pk=interassado_id))
                evento.save()
            if notificar_whatsapp=='on':
                notificar_evento_whatsapp(request,evento_id=evento.id)
            if notificar_email=='on':
                notificar_evento_email(request,evento_id=evento.id)
            messages.success(request,'Evento cadastrado com sucesso!')
            return redirect('listar_evento')
        except:
            if evento:
                evento.delete()
            messages.error(request,'Ocorreu algum erro no cadastro!')
            return redirect('home')
    return render(request, 'cadastrar/cadastrar_evento.html',context)

@login_required(login_url='login')
@has_permission_decorator(permission_name='editar_evento')
def edt_evento(request,id):
    try:
        evento=get_object_or_404(Evento,pk=id)
    except:
        messages.error(request,'Evento não existe!')
        return redirect('listar_evento')
    evento_form=EventoModelForm(request.POST or None,instance=evento)
    context={
        'evento':evento,
        'evento_form':evento_form
    }
    if request.method=='POST':
        if evento_form.is_valid:
            evento_form.save()
            messages.success(request,'Evento editado com sucesso!')
            return redirect('listar_evento')
        else:
            messages.error(request,'Formulário inválido')
            render(request, 'editar/editar_evento.html',context)
    return render(request, 'editar/editar_evento.html',context)

@login_required(login_url='login')
@has_permission_decorator(permission_name='deletar_evento')
def del_evento(request,id):
    try:
        evento=get_object_or_404(Evento,pk=id)
        evento.delete()
        messages.success(request,'Evento deletado com sucesso')
        return redirect('listar_evento')
    except:
        messages.error(request,'Erro ao deletar evento!')
        return redirect('home')
########################### ARMAMENTO ################################
@login_required(login_url='login')
@has_permission_decorator(permission_name='ver_armamento')
def listar_armamentos(request):
    if request.GET.get('pesquisa_armamento'):
        pesquisa = request.GET.get('pesquisa_armamento')
        armamentos = Armamento.objects.filter(Q(numero_de_registro__icontains=pesquisa) | 
                                       Q(tipo_de_arma__icontains=pesquisa) |
                                       Q(status_da_arma__icontains=pesquisa) |
                                       Q(usuario_atual__perfil__user__first_name__icontains=pesquisa))
    else:
        armamentos= Armamento.objects.all()

    pagina=request.GET.get('page','1')
    mostrar=request.GET.get('mostrar','10')
    armamentos_lista=Paginator(armamentos,mostrar)
    try:
        armamentos=armamentos_lista.page(pagina)
    except:
        armamentos= armamentos_lista.page(1)
    
    context={
        'armamentos':armamentos
    }
    return render(request,'listar/armamentos.html',context)


@login_required(login_url='login')
@has_permission_decorator(permission_name='ver_armamento')
def ver_armamento(request,id):
    try:
        armamento=get_object_or_404(Armamento,pk=id)
    except:
        messages.error(request,'Esse armamento não existe!')
        return redirect('listar_armamento')
    return render(request,'ver/armamento.html',{'armamento':armamento})

@login_required(login_url='login')
@has_permission_decorator(permission_name='cadastrar_armamento')
def cdt_armamento(request):
   arma_form=ArmamentoModelForm(request.POST or None)
   context={
       'arma_form':arma_form
       }
   if request.method=='POST':
        if arma_form.is_valid:
            arma_form.save()
            messages.success(request,'Armamento salvo com sucesso!')
            return redirect('listar_armamento')
        else:
            messages.error(request,'Formulário inválido')
            render(request, 'cadastrar/cadastrar_armamento.html',context)
   return render(request, 'cadastrar/cadastrar_armamento.html',context)

@login_required(login_url='login')
@has_permission_decorator(permission_name='editar_armamento')
def edt_armamento(request,id):
    try:
        armamento=get_object_or_404(Armamento,pk=id)
    except:
        messages.error(request,'Armamento não existe!')
        return redirect('listar_armamento')
    arma_form=ArmamentoModelForm(request.POST or None,instance=armamento)
    context={
        'armamento':armamento,
        'arma_form':arma_form
        }
    if request.method=='POST':
        if arma_form.is_valid:
            arma_form.save()
            messages.success(request,'Armamento salvo com sucesso!')
            return redirect('listar_armamento')
        else:
            messages.error(request,'Formulário inválido')
            render(request, 'editar/editar_armamento.html',context)
    return render(request, 'editar/editar_armamento.html',context)

@login_required(login_url='login')
@has_permission_decorator(permission_name='deletar_armamento')
def del_armamento(request,id):
    try:
        armamento=get_object_or_404(Armamento,pk=id)
        armamento.delete()
        messages.success(request,'Armamento deletado com sucesso')
        return redirect('listar_armamento')
    except:
        messages.error(request,'Erro ao deletar armamento!')
        return redirect('home')
#################################################################################
""" try:
    audiencia=get_object_or_404(Audiencia,pk=id)
except:
    messages.error(request,'Audiência não existe!')
    return redirect('listar_audiencia')
usuarios=Usuario.objects.all().order_by('perfil__user__first_name')
context={
    'audiencia':audiencia,
    'usuarios':usuarios
}
if request.method=='POST':
    numero_do_processo= request.POST.get('numero_do_processo')
    documentos= request.FILES.getlist('documento')
    data_do_processo= request.POST.get('data_do_processo')
    local=request.POST.get('local')
    interessados=request.POST.getlist('interessados')
    #VERIFICAÇÕES
    verificacao=verificacoes.verificar_campos_vazios(numero_do_processo,data_do_processo,local)
    if verificacao!=False:
        messages.error(request,verificacao)
        return redirect('edt_audiencia',context)
    try:
        datetime.strptime(data_do_processo,"%Y-%m-%dT%H:%M")
    except:
        messages.error(request,'Data inválida!')
        return redirect('edt_audiencia',context)
    
    try:
        for interessado_id in interessados:
            get_object_or_404(Usuario,pk=interessado_id)
    except:
        messages.error(request,'Interessado inexistente!')
        return redirect('edt_audiencia',context)
    #FIM DAS VERIFICAÇÕES
    notificar_whatsapp=request.POST.get('notificar_whatsapp')
    notificar_email=request.POST.get('notificar_email')

    try:
        audiencia.numero_do_processo
        audiencia.data_do_processo
        audiencia.local
        try:
            audiencia.documento.clear()
            for documento in documentos:
                audiencia.documento.add(Documento.objects.create(documento=documento))
                audiencia.save()
        except:
            messages.error(request,'Erro ao atribuir documentos à audiência')
        
        audiencia.interessados.clear()
        for interassado_id in interessados:
            audiencia.interessados.add(get_object_or_404(Usuario,pk=interassado_id))
            audiencia.save()
        if notificar_whatsapp=='on':
            notificar_audiencia_whatsapp(request,audiencia_id=audiencia.id)
        if notificar_email=='on':
            notificar_audiencia_email(request,audiencia_id=audiencia.id)
        messages.success(request,'Processo de audiência cadastrado com sucesso!')
        return redirect('listar_audiencia')
    except:
        messages.error(request,'Ocorreu algum erro na edição da audiência!')
        return redirect('edt_audiencia',context)

return render(request, 'editar/editar_audiencia_judicial.html',context) """
###################### NOTIFICAR ####################################
def notificar_audiencia_email(request,audiencia_id):
    if not ConfiguracoesSite.objects.filter(notificar_email=False).exists():
        messages.warning(request,'Função de notificação por E-mail temporariamente desativada!')
    else:
        try:
            audiencia=get_object_or_404(Audiencia,pk=audiencia_id)
            for interessado in audiencia.interessados.all():
                titulo='Notificação de audiência judicial'
                html_conteudo=render_to_string('msgs_email/notificar_audiencia.html',{'interessado':interessado,'link_da_audiencia':request.build_absolute_uri(reverse('ver_audiencia',args=[audiencia.id])),'audiencia':audiencia})
                mensagem=strip_tags(html_conteudo)
                email = EmailMessage(
                    titulo,
                    mensagem,
                    settings.EMAIL_HOST_USER,
                    [interessado.perfil.user.email])
                for documento in audiencia.documento.all():
                    email.attach(documento.documento.name,documento.documento.read())
                email.send()
            messages.success(request,f'Interessados notificados com sucesso!')
        except:
            messages.error(request,'Ocorreu algum erro na notificação por e-mail para os interessados!')

def notificar_audiencia_whatsapp(request,audiencia_id):
    if not ConfiguracoesSite.objects.filter(notificar_whatsapp=False).exists():
        messages.warning(request,'Função de notificação por WhatsApp temporariamente desativada!')
    else:
        try:
            pro_audiencia=get_object_or_404(Audiencia,pk=audiencia_id)
            messages.success(request,f'Interessados do processo: {pro_audiencia.numero_do_processo} notificados com sucesso!')
        except:
            messages.error(request,'Ocorreu algum erro na notificação por Whatsapp para os interessados!')
##############
def notificar_evento_email(request,evento_id):
    if not ConfiguracoesSite.objects.filter(notificar_email=False).exists():
        messages.warning(request,'Função de notificação por E-mail temporariamente desativada!')
    else:
        try:
            evento=get_object_or_404(Evento,pk=evento_id)
            for interessado in evento.interessados.all():
                titulo='Notificação de evento'
                html_conteudo=render_to_string('msgs_email/notificar_evento.html',{'interessado':interessado,'evento':evento})
                mensagem=strip_tags(html_conteudo)
                email = EmailMessage(
                    titulo,
                    mensagem,
                    settings.EMAIL_HOST_USER,
                    [interessado.perfil.user.email])
                for documento in evento.documento.all():
                    email.attach(documento.documento.name,documento.documento.read())
                email.send()
            messages.success(request,f'Interessados notificados com sucesso!')
        except:
            messages.error(request,'Ocorreu algum erro na notificação por e-mail para os interessados!')

def notificar_evento_whatsapp(request,evento_id):
    if not ConfiguracoesSite.objects.filter(notificar_whatsapp=False).exists():
        messages.warning(request,'Função de notificação por WhatsApp temporariamente desativada!')
    else:
        try:
            evento=get_object_or_404(Evento,pk=evento_id)
            messages.success(request,f'Interessados do processo: {evento.numero_do_processo} notificados com sucesso!')
        except:
            messages.error(request,'Ocorreu algum erro na notificação por Whatsapp para os interessados!')
############## NOTIFICAR INDIVIDUAL
def ntf_audiencia_email_individual(request,audiencia_id,usuario_id):
    if not ConfiguracoesSite.objects.filter(notificar_email=False).exists():
        messages.warning(request,'Função de notificação por E-mail temporariamente desativada!')
    else:
        try:
            audiencia=get_object_or_404(Audiencia,pk=audiencia_id)
            usuario=get_object_or_404(Usuario,pk=usuario_id)
            if audiencia.situacao=='Pendente':
                titulo='Notificação de audiência judicial'
                html_conteudo=render_to_string('msgs_email/notificar_audiencia.html',{'interessado':usuario,'link_da_audiencia':request.build_absolute_uri(reverse('ver_audiencia',args=[audiencia.id])),'audiencia':audiencia})
            elif audiencia.situacao=='Cancelada':
                titulo='Audiência judicial cancelada'
                html_conteudo=render_to_string('msgs_email/notificar_audiencia_cancelada.html',{'interessado':usuario,'link_da_audiencia':request.build_absolute_uri(reverse('ver_audiencia',args=[audiencia.id])),'audiencia':audiencia})
            elif audiencia.situacao=='Remarcada':
                titulo='Audiência judicial remarcada'
                html_conteudo=render_to_string('msgs_email/notificar_audiencia_remarcada.html',{'interessado':usuario,'link_da_audiencia':request.build_absolute_uri(reverse('ver_audiencia',args=[audiencia.id])),'audiencia':audiencia})
            elif audiencia.situacao=='Realizada':
                titulo='Audiência judicial realizada'
                html_conteudo=render_to_string('msgs_email/notificar_audiencia_realizada.html',{'interessado':usuario,'link_da_audiencia':request.build_absolute_uri(reverse('ver_audiencia',args=[audiencia.id])),'audiencia':audiencia})
            else:
                messages.error(request,'Situação da audiência não encontrada')
                return redirect('ver_audiencia',audiencia_id)
            
            mensagem=strip_tags(html_conteudo)
            email = EmailMessage(
                titulo,
                mensagem,
                settings.EMAIL_HOST_USER,
                [usuario.perfil.user.email])
            if audiencia.situacao=='Pendente' or audiencia.situacao=='Remarcada':
                for documento in audiencia.documento.all():
                    email.attach(documento.documento.name,documento.documento.read())
            email.send()
            messages.success(request,f'Interessados do processo: {audiencia.numero_do_processo} notificados com sucesso!')
        except:
            messages.error(request,'Ocorreu algum erro na notificação por e-mail!')
    
    return redirect('ver_audiencia',audiencia_id)


def ntf_audiencia_whatsapp_individual(request,audiencia_id,usuario_id):
    if not ConfiguracoesSite.objects.filter(notificar_whatsapp=False).exists():
        messages.warning(request,'Função de notificação por WhatsApp temporariamente desativada!')
    else:
        try:
            audiencia=get_object_or_404(Audiencia,pk=audiencia_id)
            usuario=get_object_or_404(Usuario,pk=usuario_id)
            if audiencia.situacao=='Pendente':
                titulo='Notificação de audiência judicial'
                html_conteudo=render_to_string('msgs_email/notificar_audiencia.html',{'interessado':usuario,'link_da_audiencia':request.build_absolute_uri(reverse('ver_audiencia',args=[audiencia.id])),'audiencia':audiencia})
            elif audiencia.situacao=='Cancelada':
                titulo='Audiência judicial cancelada'
                html_conteudo=render_to_string('msgs_email/notificar_audiencia_cancelada.html',{'interessado':usuario,'link_da_audiencia':request.build_absolute_uri(reverse('ver_audiencia',args=[audiencia.id])),'audiencia':audiencia})
            elif audiencia.situacao=='Remarcada':
                titulo='Audiência judicial remarcada'
                html_conteudo=render_to_string('msgs_email/notificar_audiencia_remarcada.html',{'interessado':usuario,'link_da_audiencia':request.build_absolute_uri(reverse('ver_audiencia',args=[audiencia.id])),'audiencia':audiencia})
            elif audiencia.situacao=='Realizada':
                titulo='Audiência judicial realizada'
                html_conteudo=render_to_string('msgs_email/notificar_audiencia_realizada.html',{'interessado':usuario,'link_da_audiencia':request.build_absolute_uri(reverse('ver_audiencia',args=[audiencia.id])),'audiencia':audiencia})
            else:
                messages.error(request,'Situação da audiência não encontrada')
                return redirect('ver_audiencia',audiencia_id)
            mensagem=strip_tags(html_conteudo)
        except:
            messages.error(request,'Ocorreu algum erro na notificação para os interessados!')
        return redirect(f'http://wa.me/+55{usuario.telefone}?text={mensagem}')
    return redirect('ver_audiencia',audiencia_id)
#####
def ntf_evento_email_individual(request, evento_id, usuario_id):
    if not ConfiguracoesSite.objects.filter(notificar_email=False).exists():
        messages.warning(
            request, "Função de notificação por E-mail temporariamente desativada!"
        )
    else:
        try:
            evento = get_object_or_404(Evento, pk=evento_id)
            usuario = get_object_or_404(Usuario, pk=usuario_id)
            titulo = "Notificação de evento"
            html_conteudo = render_to_string(
                "msgs_email/notificar_evento.html",
                {"interessado": usuario, "evento": evento},
            )
            mensagem = strip_tags(html_conteudo)
            email = EmailMessage(
                titulo, mensagem, settings.EMAIL_HOST_USER, [usuario.perfil.user.email]
            )
            for documento in evento.documento.all():
                email.attach(documento.documento.name, documento.documento.read())
            email.send()
            messages.success(
                request,
                f"Interessados do processo: {evento.numero_do_processo} notificados com sucesso!",
            )
        except:
            messages.error(request, "Ocorreu algum erro na notificação por e-mail!")

    return redirect("ver_evento", evento_id)


def ntf_evento_whatsapp_individual(request, evento_id, usuario_id):
    if not ConfiguracoesSite.objects.filter(notificar_whatsapp=False).exists():
        messages.warning(
            request, "Função de notificação por WhatsApp temporariamente desativada!"
        )
    else:
        try:
            evento = get_object_or_404(Evento, pk=evento_id)
            usuario = get_object_or_404(Usuario, pk=usuario_id)
            html_conteudo = render_to_string(
                "msgs_email/notificar_evento.html",
                {"interessado": usuario, "evento": evento},
            )
            mensagem = strip_tags(html_conteudo)
        except:
            messages.error(
                request, "Ocorreu algum erro na notificação para os interessados!"
            )
        return redirect(f"http://wa.me/+55{usuario.telefone}?text={mensagem}")
    return redirect("ver_evento", evento_id)
#####
def cdt_estados_cidades(request):
    from .utils import estados
    for state in estados:
        if not Estado.objects.filter(nome=state['nome'],sigla=state['sigla']).exists():
            estado=Estado.objects.create(
                nome=state['nome'],
                sigla=state['sigla']
            )
        else:
            estado=get_object_or_404(Estado,nome=state['nome'],sigla=state['sigla'])
        for cidade in state['cidades']:
            if not Cidade.objects.filter(nome=cidade,estado=estado).exists():
                Cidade.objects.create(
                    nome=cidade,
                    estado=estado
                )
    return redirect('home')
