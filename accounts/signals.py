# accounts/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile
from challenges.models import BrazilState

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Cria automaticamente um UserProfile quando um novo usuário é criado
    """
    if created:
        # Pega o primeiro estado (order=1) como estado inicial
        initial_state = BrazilState.objects.filter(order=1).first()
        UserProfile.objects.create(
            user=instance,
            current_state=initial_state
        )

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Salva o perfil do usuário quando o usuário é salvo
    """
    try:
        instance.profile.save()
    except UserProfile.DoesNotExist:
        # Se o perfil não existe, cria um novo
        initial_state = BrazilState.objects.filter(order=1).first()
        UserProfile.objects.create(
            user=instance,
            current_state=initial_state
        )