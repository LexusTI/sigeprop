from .models import Perfil,Usuario,Audiencia,Evento,Armamento
from django import forms
from django.contrib.auth.models import User
class UserForm(forms.Form):
    nome = forms.CharField(label="Nome", max_length=50)
    sobrenome = forms.CharField(label="Sobrenome", max_length=150)
    email = forms.EmailField(label="E-mail")
    senha= forms.CharField(label='Senha',widget=forms.PasswordInput,help_text='A senha deverá ter no mínimo 8 caracteres. Deverá ter números e letras.')

class PerfilForm(forms.Form):
    foto= forms.ImageField(label='Foto',required=False)

class UsuarioForm(forms.Form):
    pelotao = forms.CharField(max_length=10,label='Pelotão')
    matricula = forms.CharField(max_length=20,label='Matrícula')
    cpf = forms.CharField(max_length=14,label='CPF',help_text='Formato: xxx.xxx.xxx-xx')
    rg = forms.CharField(max_length=13,label='RG',help_text='Formato: xx.xxx.xxx-xx')
    telefone= forms.CharField(max_length=20,label='Telefone',help_text='Apenas números com DDD')


class NotificarForm(forms.Form):
    notificar_email=forms.BooleanField(required=False,initial=True,label='Notificar interessados por e-mail')
    notificar_whatsapp=forms.BooleanField(required=False,initial=True,label='Notificar interessados por WhatsApp')

class UserModelForm(forms.ModelForm):
    class Meta:
        model=User
        fields=['first_name','last_name','email']

class PerfilModelForm(forms.ModelForm):
    class Meta:
        model=Perfil
        fields='__all__'
        exclude=['user']

class UsuarioModelForm(forms.ModelForm):
    class Meta:
        model=Usuario
        fields='__all__'
        exclude=['perfil']

class AudienciaModelForm(forms.ModelForm):
    class Meta:
        model=Audiencia
        fields='__all__'
        exclude=['documento','data_do_processo_antiga']
        widgets={
            'data_do_processo':forms.DateTimeInput(format='%Y-%m-%d %H:%M',attrs={'type':'datetime-local'}),
            'data_do_processo_antiga':forms.DateTimeInput(format='%Y-%m-%d %H:%M',attrs={'type':'datetime-local'}),
        }

class EventoModelForm(forms.ModelForm):
    class Meta:
        model=Evento
        fields='__all__'
        exclude=['documento']
        widgets={
            'data_do_evento':forms.DateTimeInput(format='%Y-%m-%d %H:%M',attrs={'type':'datetime-local'})
        }

class ArmamentoModelForm(forms.ModelForm):
    class Meta:
        model=Armamento
        fields='__all__'