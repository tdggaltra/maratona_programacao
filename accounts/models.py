# accounts/models.py
from django.db import models
from django.contrib.auth.models import User
from challenges.models import Challenge, BrazilState

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    completed_challenges = models.ManyToManyField(Challenge, blank=True, related_name='completed_by')
    current_state = models.ForeignKey(BrazilState, on_delete=models.SET_NULL, null=True, blank=True)
    total_points = models.IntegerField(default=0)
    
    def __str__(self):
        return f"Perfil de {self.user.username}"
    
    def unlock_next_state(self):
        """Desbloqueia o próximo estado se o usuário completou o desafio atual"""
        if self.current_state:
            next_order = self.current_state.order + 1
            try:
                next_state = BrazilState.objects.get(order=next_order)
                self.current_state = next_state
                self.save()
                return True
            except BrazilState.DoesNotExist:
                return False
        return False
