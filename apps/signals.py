from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.conf import settings
import os

from .models import Perfil

@receiver(pre_save, sender=Perfil)
def replace_perfil_foto(sender, instance, **kwargs):
    if instance.pk:  # Verifica se o objeto já existe no banco de dados (edição)
        try:
            old_instance = Perfil.objects.get(pk=instance.pk)
            if old_instance.foto != instance.foto:
                # Remove a foto antiga do armazenamento
                if old_instance.foto:
                    old_logo_path = os.path.join(settings.MEDIA_ROOT, str(old_instance.foto))
                    if os.path.isfile(old_logo_path):
                        os.remove(old_logo_path)
        except Perfil.DoesNotExist:
            pass