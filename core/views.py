# core/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required  # Adicione esta linha
from challenges.models import BrazilState, Challenge
from accounts.models import UserProfile

@login_required
def home(request):
    """Página inicial com o mapa do Brasil"""
    states = BrazilState.objects.all().order_by('order')
    
    # Obtém o perfil do usuário ou cria um se não existir
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    # Se é um perfil novo, define o estado inicial
    if created or not profile.current_state:
        initial_state = BrazilState.objects.filter(order=1).first()
        profile.current_state = initial_state
        profile.save()
    
    # Prepara os dados dos estados para o mapa
    states_data = []
    for state in states:
        # Estado está disponível se é o atual ou se o usuário já completou desafios anteriores
        is_available = (state == profile.current_state) or (state.order < profile.current_state.order)
        # Estado está completo se o usuário já passou dele
        is_completed = state.order < profile.current_state.order
        # Estado é o atual
        is_current = state == profile.current_state
        
        try:
            challenge = state.challenge
            states_data.append({
                'id': state.id,
                'name': state.name,
                'abbreviation': state.abbreviation,
                'map_x_position': state.map_x_position,
                'map_y_position': state.map_y_position,
                'is_available': is_available,
                'is_completed': is_completed,
                'is_current': is_current,
                'order': state.order,
                'challenge_id': challenge.id,
                'challenge_title': challenge.title,
                'difficulty': challenge.difficulty,
            })
        except Challenge.DoesNotExist:
            # Estado sem desafio associado
            states_data.append({
                'id': state.id,
                'name': state.name,
                'abbreviation': state.abbreviation,
                'map_x_position': state.map_x_position,
                'map_y_position': state.map_y_position,
                'is_available': is_available,
                'is_completed': is_completed,
                'is_current': is_current,
                'order': state.order,
                'challenge_id': None,
                'challenge_title': 'Desafio não disponível',
                'difficulty': 'unknown',
            })
    
    context = {
        'states_data': states_data,
        'current_state': profile.current_state,
        'completed_challenges': profile.completed_challenges.count(),
        'total_points': profile.total_points,
    }
    
    return render(request, 'core/home.html', context)

def about(request):
    """Página sobre a maratona"""
    return render(request, 'core/about.html')