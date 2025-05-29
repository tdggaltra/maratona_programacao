
# challenges/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # Visualizar desafio específico
    path('<int:pk>/', views.challenge_detail, name='challenge-detail'),
    
    # Submeter solução (método tradicional - mantém compatibilidade)
    path('<int:challenge_id>/submit/', views.submit_solution, name='submit-solution'),
    
    # Submeter solução via AJAX (método moderno)
    path('<int:pk>/submit/', views.submit_solution_ajax, name='submit-solution-ajax'),
    
    # Ver resultado de uma submissão específica
    path('submission/<int:submission_id>/', views.submission_result, name='submission-result'),
    
    # URLs adicionais úteis (opcionais)
    path('submissions/', views.user_submissions, name='user-submissions'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
]

