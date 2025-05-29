# challenges/models.py

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse

class ProgrammingLanguage(models.Model):
    name = models.CharField(max_length=50)
    extension = models.CharField(max_length=10)
    
    def __str__(self):
        return self.name
    
    class Meta:
        app_label = 'challenges'  # Adicione esta linha

class BrazilState(models.Model):
    name = models.CharField(max_length=50)
    abbreviation = models.CharField(max_length=2)
    # Coordenadas para posicionamento no mapa
    map_x_position = models.FloatField()
    map_y_position = models.FloatField()
    # Região do Brasil
    REGION_CHOICES = [
        ('norte', 'Norte'),
        ('nordeste', 'Nordeste'),
        ('centro-oeste', 'Centro-Oeste'),
        ('sudeste', 'Sudeste'),
        ('sul', 'Sul'),
    ]
    region = models.CharField(max_length=15, choices=REGION_CHOICES, default='norte')
    # Ordem de desbloqueio (1 para o estado inicial, etc.)
    order = models.IntegerField(unique=True)
    
    def __str__(self):
        return f"{self.name} ({self.abbreviation})"
    
    class Meta:
        ordering = ['order']

class Challenge(models.Model):
    DIFFICULTY_CHOICES = [
        ('easy', 'Fácil'),
        ('medium', 'Médio'),
        ('hard', 'Difícil'),
        ('expert', 'Especialista'),
        ('final', 'Desafio Final'),
    ]
    
    title = models.CharField(max_length=100)
    description = models.TextField()
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES)
    points = models.IntegerField()
    state = models.OneToOneField(BrazilState, on_delete=models.CASCADE, related_name='challenge')
    language = models.ForeignKey(ProgrammingLanguage, on_delete=models.CASCADE)
    input_description = models.TextField()
    output_description = models.TextField()
    example_input = models.TextField()
    example_output = models.TextField()
    test_cases = models.JSONField(default=list)  # Lista de dicionários com pares input/output
    time_limit = models.IntegerField(default=1000)  # Em milissegundos
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.title} - {self.state.name}"
    
    def get_absolute_url(self):
        return reverse('challenge-detail', kwargs={'pk': self.pk})

class Submission(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('running', 'Em Execução'),
        ('accepted', 'Aceito'),
        ('wrong_answer', 'Resposta Incorreta'),
        ('time_limit', 'Tempo Limite Excedido'),
        ('compilation_error', 'Erro de Compilação'),
        ('runtime_error', 'Erro de Execução'),
    ]
    
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE, related_name='submissions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submissions')
    code = models.TextField()
    language = models.ForeignKey(ProgrammingLanguage, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    execution_time = models.FloatField(null=True, blank=True)  # Em milissegundos
    error_message = models.TextField(blank=True, null=True)
    submitted_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.user.username} - {self.challenge.title} - {self.status}"
    
    class Meta:
        ordering = ['-submitted_at']
