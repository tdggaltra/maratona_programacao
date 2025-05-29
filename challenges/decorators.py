# challenges/decorators.py
from functools import wraps
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from .models import Challenge, BrazilState
from accounts.models import UserProfile

def challenge_access_required(view_func):
    """
    Decorator que verifica se o usuário tem acesso ao desafio
    - Usuário deve estar logado
    - Desafio deve estar no estado atual ou anterior do usuário
    """
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        # Pega o ID do desafio (assumindo que está nos kwargs)
        challenge_id = kwargs.get('pk') or kwargs.get('challenge_id')
        
        if not challenge_id:
            messages.error(request, 'Desafio não encontrado.')
            return redirect('home')
        
        challenge = get_object_or_404(Challenge, pk=challenge_id)
        
        # Obtém o perfil do usuário
        try:
            profile = request.user.profile
        except UserProfile.DoesNotExist:
            # Se não tem perfil, cria um
            initial_state = BrazilState.objects.filter(order=1).first()
            profile = UserProfile.objects.create(
                user=request.user,
                current_state=initial_state
            )
        
        # Verifica se o usuário tem acesso a este desafio
        if not profile.current_state:
            messages.error(request, 'Você precisa ter um estado inicial definido.')
            return redirect('home')
        
        # Usuário pode acessar se:
        # 1. É o desafio do estado atual
        # 2. É um desafio de estado anterior (já desbloqueado)
        challenge_state_order = challenge.state.order
        current_state_order = profile.current_state.order
        
        if challenge_state_order > current_state_order:
            messages.warning(request, f'Você precisa completar os desafios anteriores para acessar {challenge.state.name}.')
            return redirect('home')
        
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view

def state_access_required(view_func):
    """
    Decorator que verifica se o usuário tem acesso ao estado
    """
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        # Pega o ID do estado
        state_id = kwargs.get('state_id') or kwargs.get('pk')
        
        if not state_id:
            messages.error(request, 'Estado não encontrado.')
            return redirect('home')
        
        state = get_object_or_404(BrazilState, pk=state_id)
        
        # Obtém o perfil do usuário
        try:
            profile = request.user.profile
        except UserProfile.DoesNotExist:
            initial_state = BrazilState.objects.filter(order=1).first()
            profile = UserProfile.objects.create(
                user=request.user,
                current_state=initial_state
            )
        
        # Verifica acesso ao estado
        if not profile.current_state:
            messages.error(request, 'Você precisa ter um estado inicial definido.')
            return redirect('home')
        
        state_order = state.order
        current_state_order = profile.current_state.order
        
        if state_order > current_state_order:
            messages.warning(request, f'Você ainda não desbloqueou {state.name}.')
            return redirect('home')
        
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view