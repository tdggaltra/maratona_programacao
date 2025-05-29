# accounts/views.py - Versão com logout customizado
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.db import IntegrityError
from .models import UserProfile
from challenges.models import BrazilState

def register(request):
    """Registra um novo usuário"""
    if request.user.is_authenticated:
        # Se o usuário já está logado, redireciona para home
        return redirect('home')
    
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                # Faz login automático após registro
                login(request, user)
                messages.success(request, f'Bem-vindo(a), {user.username}! Sua conta foi criada com sucesso.')
                return redirect('home')
            except IntegrityError:
                messages.error(request, 'Erro ao criar conta. Tente novamente.')
        else:
            messages.error(request, 'Por favor, corrija os erros abaixo.')
    else:
        form = UserCreationForm()
    
    return render(request, 'accounts/register.html', {'form': form})

@login_required
def profile(request):
    """Exibe o perfil do usuário com estatísticas"""
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        # Se o perfil não existe, cria um novo
        initial_state = BrazilState.objects.filter(order=1).first()
        profile = UserProfile.objects.create(
            user=request.user,
            current_state=initial_state
        )
    
    # Estatísticas do usuário
    submissions = request.user.submissions.all()
    completed_challenges = profile.completed_challenges.all()
    total_submissions = submissions.count()
    accepted_submissions = submissions.filter(status='accepted').count()
    
    # Calcula taxa de sucesso
    success_rate = 0
    if total_submissions > 0:
        success_rate = round((accepted_submissions / total_submissions) * 100, 1)
    
    # Estados disponíveis vs estados do Brasil
    total_states = BrazilState.objects.count()
    current_state_order = profile.current_state.order if profile.current_state else 0
    states_unlocked = current_state_order
    progress_percentage = round((states_unlocked / total_states) * 100, 1) if total_states > 0 else 0
    
    context = {
        'profile': profile,
        'submissions': submissions[:10],  # Últimas 10 submissões
        'completed_challenges': completed_challenges,
        'total_submissions': total_submissions,
        'accepted_submissions': accepted_submissions,
        'success_rate': success_rate,
        'states_unlocked': states_unlocked,
        'total_states': total_states,
        'progress_percentage': progress_percentage,
    }
    return render(request, 'accounts/profile.html', context)

def logout_view(request):
    """Logout customizado que aceita GET e POST"""
    if request.method == 'POST':
        # Logout via POST (mais seguro)
        logout(request)
        messages.success(request, 'Logout realizado com sucesso!')
        return redirect('about')
    
    elif request.method == 'GET':
        # Logout via GET (para compatibilidade)
        if request.user.is_authenticated:
            logout(request)
            messages.success(request, 'Logout realizado com sucesso!')
        return redirect('about')
    
    # Se por algum motivo chegou aqui
    return redirect('home')

# accounts/views.py - ADICIONE esta função ao final do arquivo

from django.contrib.auth import logout
from django.shortcuts import redirect
from django.contrib import messages

def custom_logout(request):
    """
    View de logout customizada que aceita GET e POST
    """
    if request.user.is_authenticated:
        username = request.user.username
        logout(request)
        messages.success(request, f'Até logo, {username}! Logout realizado com sucesso.')
    
    return redirect('about')  # ou redirect('home') se preferir
