from django.db import models
from django.contrib.auth.models import User
from smart_selects.db_fields import ChainedForeignKey
# Create your models here.
class ConfiguracoesSite(models.Model):
    notificar_email    = models.BooleanField(default=True,verbose_name='Desativar notificação por email')
    notificar_whatsapp = models.BooleanField(default=True,verbose_name='Desativar notificação por whatsapp')
    def __str__(self):
        return 'Configurações'
class Token_redefinicao(models.Model):
    token = models.CharField(max_length=64,verbose_name='Token')
    usado = models.BooleanField(default=False,verbose_name='Usado?')
    user  = models.OneToOneField(User,on_delete=models.CASCADE,verbose_name='Usuário do token')
    def __str__(self):
        return f'{self.user.first_name}-{self.usado}'
class Estado(models.Model):
    nome  = models.CharField(max_length=30,verbose_name='Nome do estado')
    sigla = models.CharField(max_length=2,verbose_name='Sigla do estado')
    def __str__(self):
        return f'{self.nome}'
class Cidade(models.Model):
    nome   = models.CharField(max_length=60,verbose_name='Nome da cidade')
    estado = models.ForeignKey(Estado,on_delete=models.CASCADE,verbose_name='Estado da cidade')
    def __str__(self):
        return f'{self.nome}({self.estado.sigla})'

class Unidade(models.Model):
    status_choices=[
        ('Ativo','Ativo'),
        ('Inativo','Inativo'),
        ('Em construção','Em construção'),
    ]
    nome        = models.CharField(max_length=250,verbose_name='Nome da unidade')
    sigla       = models.CharField(max_length=20,verbose_name='Sigla da unidade')
    cnpj        = models.CharField(max_length=20,verbose_name='CNPJ')
    responsavel = models.CharField(max_length=250,verbose_name='Responsável pela unidade')
    contato     = models.CharField(max_length=60,verbose_name='Contato da unidade')
    estado      = models.ForeignKey(Estado,on_delete=models.SET_NULL,null=True,verbose_name='Estado')
    cidade      = ChainedForeignKey(Cidade,on_delete=models.SET_NULL,null=True,
        chained_field="estado",
        chained_model_field="estado",
        show_all=False,
        auto_choose=True,
        sort=True)
    cep        = models.CharField(max_length=10,verbose_name='CEP')
    bairro     = models.CharField(max_length=60,verbose_name='Bairro')
    endereco   = models.CharField(max_length=250,verbose_name='Endereço')
    complemento= models.CharField(max_length=250,verbose_name='Complemento')
    status     = models.CharField(max_length=250,verbose_name='Status da unidade',choices=status_choices,default='Ativo')
    def __str__(self):
        return f'{self.sigla}-{self.cnpj}'
    
class Perfil(models.Model):
    user = models.OneToOneField(User,on_delete=models.CASCADE)
    foto = models.ImageField(upload_to='img_users/',verbose_name='Foto de usuário',blank=True)
    
    def __str__(self):
        return f'{self.user.get_full_name()}'
    
class Usuario(models.Model):
    perfil    = models.OneToOneField(Perfil, on_delete=models.CASCADE)
    pelotao   = models.CharField(max_length=10,verbose_name='Pelotão')
    matricula = models.CharField(max_length=20,verbose_name='Matrícula')
    cpf       = models.CharField(max_length=14,verbose_name='CPF',help_text='Formato: xxx.xxx.xxx-xx')
    rg        = models.CharField(max_length=13,verbose_name='RG',help_text='Formato: xx.xxx.xxx-xx')
    telefone  = models.CharField(max_length=15,verbose_name='Telefone',help_text='Apenas números com DDD')
    #unidade  = models.ForeignKey(Unidade,on_delete=models.PROTECT,verbose_name='Unidade vinculada')

    def __str__(self):
        return f'{self.perfil.user.first_name}-{self.matricula}'
    def delete(self, *args, **kwargs):
        self.perfil.foto.delete()
        self.perfil.user.delete()
        super().delete(*args, **kwargs)


class Documento(models.Model):
    documento=models.FileField(verbose_name='Documento',upload_to='documentos/%Y/%m/')
    def __str__(self):
        return f'{self.documento.name}'
    def delete(self, *args, **kwargs):
        self.documento.delete()
        super().delete(*args, **kwargs)

class Audiencia(models.Model):
    SITUACOES_CHOICES=[
        ('Pendente','Pendente'),
        ('Realizada','Realizada'),
        ('Cancelada','Cancelada'),
        ('Remarcada','Remarcada'),
    ]
    numero_do_processo = models.CharField(max_length=100,verbose_name='Número de processo da audiência')
    data_do_processo   = models.DateTimeField(verbose_name='Data e horário da audiência')
    data_do_processo_antiga   = models.DateTimeField(verbose_name='Data e horário da audiência antiga',null=True)
    local              = models.CharField(max_length=250,verbose_name='Local da audiência',default='Fórum Bernardino de Souza')
    #descricao         = models.TextField(verbose_name='Descrição da audiencia',blank=True)
    documento          = models.ManyToManyField(Documento,related_name='audiencias',blank=True)
    situacao=models.CharField(max_length=15,verbose_name='Situação da audiência',choices=SITUACOES_CHOICES,default='Pendente')
    interessados       = models.ManyToManyField(Usuario,verbose_name='Interessados do processo de audiência',related_name='audiencias',blank=True,
                                                through='Audiencia_Usuario',
                                                through_fields=('audiencia','usuario'))
    
    def __str__(self):
        return f'{self.numero_do_processo}'
    def delete(self, *args, **kwargs):
        for documento in self.documento.all():
            documento.delete()
        super().delete(*args, **kwargs)
class Audiencia_Usuario(models.Model):
    audiencia= models.ForeignKey(Audiencia,on_delete=models.CASCADE,verbose_name='Audiência vinculada ao usuário',related_name='audiencia_usuarios')
    usuario= models.ForeignKey(Usuario,on_delete=models.CASCADE,verbose_name='Usuário vinculada a audiência',related_name='audiencia_usuarios')
    confirmar_recebimento=models.BooleanField(default=False,verbose_name='Confirmar recebimento')

    def __str__(self):
        return f'{self.usuario}{self.audiencia}{self.confirmar_recebimento}'

class Evento(models.Model):
    numero_do_processo= models.CharField(max_length=100,verbose_name='Número de processo do evento')
    nome = models.CharField(max_length=100,verbose_name='Nome do evento')
    data_do_evento = models.DateTimeField(verbose_name='Data e horário do evento')
    local = models.CharField(max_length=250,verbose_name='Local do evento')
    #descricao=models.TextField(verbose_name='Descrição do evento',blank=True)
    documento=models.ManyToManyField(Documento,related_name='eventos',blank=True)
    interessados     = models.ManyToManyField(Usuario,verbose_name='Interessados do evento',related_name='eventos',blank=True,
                                              through='Evento_Usuario',
                                                through_fields=('evento','usuario'))
    
    def __str__(self):
        return f'{self.numero_do_processo}'
    def delete(self, *args, **kwargs):
        for documento in self.documento.all():
            documento.delete()
        super().delete(*args, **kwargs)

class Evento_Usuario(models.Model):
    evento= models.ForeignKey(Evento,on_delete=models.CASCADE,verbose_name='Evento vinculado ao usuário',related_name='evento_usuarios')
    usuario= models.ForeignKey(Usuario,on_delete=models.CASCADE,verbose_name='Usuário vinculado ao evento',related_name='evento_usuarios')
    confirmar_recebimento=models.BooleanField(default=False,verbose_name='Confirmar recebimento')

    def __str__(self):
        return f'{self.usuario}{self.evento}{self.confirmar_recebimento}'
    
class Armamento(models.Model):
    status=[
        ('Ativa','Ativa'),
        ('Inativa','Inativa'),
        ('Em manutenção','Em manutenção'),
    ]
    numero_de_registro = models.CharField(max_length=100,verbose_name='Número de registro da arma')
    tipo_de_arma       = models.CharField(max_length=100,verbose_name='Tipo da arma',help_text='por exemplo: pistola, rifle, espingarda, etc.')
    status_da_arma     = models.CharField(max_length=20,choices=status,default='Ativa')
    usuario_atual      = models.ForeignKey(Usuario,on_delete=models.SET_NULL,null=True,blank=True,verbose_name='Usuário atual')
    
    def __str__(self):
        return f'{self.numero_de_registro}:{self.status_da_arma}'
