# challenges/views.py
# MANTÉM SUA IMPLEMENTAÇÃO + MELHORIAS NECESSÁRIAS

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST  # IMPORTANTE para AJAX
from .models import Challenge, Submission, BrazilState
from accounts.models import UserProfile
from .java_executor import evaluate_java_submission  # SEU IMPORT JAVA
import json  # IMPORTANTE para AJAX
import subprocess
import tempfile
import os
import time
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Challenge, Submission, BrazilState
from accounts.models import UserProfile
from .java_executor import evaluate_java_submission  # SUA IMPORTAÇÃO JAVA
import json
import subprocess
import tempfile
import os
import time

# SUA VIEW ORIGINAL + pequenas melhorias
@login_required
def challenge_detail(request, pk):
    challenge = get_object_or_404(Challenge, pk=pk)
    
    # Melhoria: tratamento de perfil inexistente
    try:
        profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        # Se não tem perfil, cria um
        initial_state = BrazilState.objects.filter(order=1).first()
        profile = UserProfile.objects.create(
            user=request.user,
            current_state=initial_state
        )
    
    if challenge.state.order > profile.current_state.order:
        messages.error(request, "Você precisa completar os desafios anteriores primeiro!")
        return redirect('home')
    
    submissions = Submission.objects.filter(user=request.user, challenge=challenge).order_by('-submitted_at')
    
    # Melhoria: adiciona informação se já completou
    is_completed = profile.completed_challenges.filter(id=challenge.id).exists()
    
    context = {
        'challenge': challenge,
        'submissions': submissions,
        'is_completed': is_completed,  # NOVO
        'profile': profile,  # NOVO
    }
    
    return render(request, 'challenges/challenge_detail.html', context)

# SUA VIEW ORIGINAL + suporte AJAX
@login_required
def submit_solution(request, challenge_id):
    challenge = get_object_or_404(Challenge, pk=challenge_id)
    
    if request.method == 'POST':
        # Melhoria: suporte tanto para form tradicional quanto AJAX
        if request.content_type == 'application/json':
            # Submissão via AJAX (novo)
            try:
                data = json.loads(request.body)
                code = data.get('code', '').strip()
                
                if not code:
                    return JsonResponse({
                        'success': False,
                        'error': 'Código não pode estar vazio'
                    })
            except:
                return JsonResponse({
                    'success': False,
                    'error': 'Dados inválidos'
                })
        else:
            # Submissão via form tradicional (seu método original)
            code = request.POST.get('code')
        
        submission = Submission.objects.create(
            challenge=challenge,
            user=request.user,
            code=code,
            language=challenge.language,
            status='pending'
        )
        
        # SUA FUNÇÃO ORIGINAL - sem alterações
        result = evaluate_submission(submission)
        
        if result['status'] == 'accepted':
            profile = UserProfile.objects.get(user=request.user)
            
            # Melhoria: só adiciona pontos se ainda não completou
            if not profile.completed_challenges.filter(id=challenge.id).exists():
                profile.completed_challenges.add(challenge)
                profile.total_points += challenge.points
                profile.save()
                profile.unlock_next_state()
                
                # Resposta diferente para AJAX vs form
                if request.content_type == 'application/json':
                    return JsonResponse({
                        'success': True,
                        'status': 'accepted',
                        'message': 'Parabéns! Seu código foi aceito!',
                        'points_earned': challenge.points,
                        'next_unlocked': True,
                    })
                else:
                    messages.success(request, "Parabéns! Seu código foi aceito!")
            else:
                if request.content_type == 'application/json':
                    return JsonResponse({
                        'success': True,
                        'status': 'accepted',
                        'message': 'Código aceito! (já completado anteriormente)',
                        'points_earned': 0,
                        'next_unlocked': False,
                    })
                else:
                    messages.info(request, "Código aceito! (já completado anteriormente)")
        else:
            if request.content_type == 'application/json':
                return JsonResponse({
                    'success': True,
                    'status': result['status'],
                    'message': result.get('message', 'Erro na execução'),
                })
            else:
                messages.error(request, f"Submissão rejeitada: {result['message']}")
        
        # Redirecionamento tradicional
        if request.content_type != 'application/json':
            return redirect('submission-result', submission_id=submission.id)
    
    return redirect('challenge-detail', pk=challenge_id)

# Melhoria: nova URL para submissão AJAX
@login_required
@require_POST
def submit_solution_ajax(request, pk):
    """Nova view específica para submissões AJAX"""
    return submit_solution(request, pk)

# SUA VIEW ORIGINAL - sem alterações
@login_required
def submission_result(request, submission_id):
    submission = get_object_or_404(Submission, pk=submission_id, user=request.user)
    
    context = {
        'submission': submission,
        'challenge': submission.challenge,
    }
    
    return render(request, 'challenges/results.html', context)

# SUA FUNÇÃO ORIGINAL - MANTIDA EXATAMENTE COMO ESTAVA
def evaluate_submission(submission):
    """
    Função que avalia uma submissão.
    MANTÉM SUA IMPLEMENTAÇÃO ORIGINAL com suporte Java
    """
    challenge = submission.challenge
    language = submission.language
    code = submission.code
    
    # Status inicial
    submission.status = 'running'
    submission.save()
    
    try:
        # SUA CONDIÇÃO JAVA ORIGINAL - mantida
        if language.name.lower() == 'java':
            return evaluate_java_submission(submission)
        
        # SUA LÓGICA ORIGINAL para outras linguagens - mantida
        else:
            return evaluate_other_languages_existing(submission)
            
    except Exception as e:
        submission.status = 'runtime_error'
        submission.error_message = str(e)
        submission.save()
        return {'status': 'runtime_error', 'message': f'Erro de execução: {str(e)}'}

# SUA FUNÇÃO ORIGINAL - MANTIDA COMPLETAMENTE
def evaluate_other_languages_existing(submission):
    """
    Implementação melhorada para Python, C, C++
    """
    challenge = submission.challenge
    language = submission.language
    code = submission.code
    
    try:
        # Verifica cada caso de teste
        all_passed = True
        start_time = time.time()
        
        for test_case in challenge.test_cases:
            test_input = test_case.get('input', '')
            expected_output = test_case.get('output', '').strip()
            
            # Cria arquivo temporário
            with tempfile.NamedTemporaryFile(suffix=f'.{language.extension}', delete=False) as temp_file:
                temp_file.write(code.encode('utf-8'))  # Especifica encoding
                temp_file_path = temp_file.name
            
            # Execute o código baseado na linguagem
            if language.name.lower() == 'python':
                proc = subprocess.Popen(
                    ['python3', temp_file_path],  # Usa python3 explicitamente
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
            elif language.name.lower() == 'c':
                # Compila o código C
                compile_proc = subprocess.run(
                    ['gcc', temp_file_path, '-o', f'{temp_file_path}.out', '-std=c11', '-Wall'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if compile_proc.returncode != 0:
                    submission.status = 'compilation_error'
                    error_msg = compile_proc.stderr.strip() or "Erro de compilação desconhecido"
                    submission.error_message = error_msg
                    submission.save()
                    
                    # Limpa arquivo temporário
                    if os.path.exists(temp_file_path):
                        os.unlink(temp_file_path)
                    
                    return {
                        'status': 'compilation_error', 
                        'message': f'Erro de compilação C: {error_msg}'
                    }
                
                proc = subprocess.Popen(
                    [f'{temp_file_path}.out'],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
            elif language.name.lower() in ['c++', 'cpp']:
                # Compila o código C++ com flags melhoradas
                compile_proc = subprocess.run(
                    [
                        'g++', 
                        temp_file_path, 
                        '-o', f'{temp_file_path}.out',
                        '-std=c++17',  # Padrão C++17
                        '-Wall',       # Avisos importantes
                        '-Wextra',     # Avisos extras
                        '-O2'          # Otimização
                    ],
                    capture_output=True,
                    text=True,
                    timeout=10  # 10 segundos para compilar
                )
                
                if compile_proc.returncode != 0:
                    submission.status = 'compilation_error'
                    
                    # Captura a mensagem de erro detalhada
                    error_msg = compile_proc.stderr.strip()
                    if not error_msg:
                        error_msg = "Erro de compilação desconhecido"
                    
                    # Tenta melhorar a mensagem de erro
                    if "error:" in error_msg.lower():
                        # Pega apenas as linhas com 'error:'
                        error_lines = [line for line in error_msg.split('\n') if 'error:' in line.lower()]
                        if error_lines:
                            error_msg = '\n'.join(error_lines[:3])  # Máximo 3 linhas de erro
                    
                    submission.error_message = error_msg
                    submission.save()
                    
                    # Limpa arquivo temporário
                    if os.path.exists(temp_file_path):
                        os.unlink(temp_file_path)
                    
                    return {
                        'status': 'compilation_error', 
                        'message': f'Erro de compilação C++: {error_msg}'
                    }
                
                proc = subprocess.Popen(
                    [f'{temp_file_path}.out'],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
            
            # Executa o programa
            try:
                stdout, stderr = proc.communicate(
                    input=test_input, 
                    timeout=challenge.time_limit / 1000
                )
            except subprocess.TimeoutExpired:
                proc.kill()
                submission.status = 'time_limit'
                submission.save()
                
                # Limpa arquivos temporários
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                if language.name.lower() in ['c', 'c++', 'cpp']:
                    if os.path.exists(f'{temp_file_path}.out'):
                        os.unlink(f'{temp_file_path}.out')
                
                return {'status': 'time_limit', 'message': 'Tempo limite excedido'}
            
            # Verifica se houve erro de execução
            if proc.returncode != 0:
                submission.status = 'runtime_error'
                error_msg = stderr.strip() if stderr.strip() else "Erro de execução desconhecido"
                submission.error_message = error_msg
                submission.save()
                
                # Limpa arquivos temporários
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                if language.name.lower() in ['c', 'c++', 'cpp']:
                    if os.path.exists(f'{temp_file_path}.out'):
                        os.unlink(f'{temp_file_path}.out')
                
                return {'status': 'runtime_error', 'message': f'Erro de execução: {error_msg}'}
            
            # Limpa arquivos temporários
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
            if language.name.lower() in ['c', 'c++', 'cpp']:
                if os.path.exists(f'{temp_file_path}.out'):
                    os.unlink(f'{temp_file_path}.out')
            
            # Verifica se a saída está correta
            actual_output = stdout.strip()
            
            if actual_output != expected_output:
                all_passed = False
                submission.status = 'wrong_answer'
                submission.save()
                
                # Debug: mostra diferença entre saídas
                debug_msg = f"Esperado: '{expected_output}', Obtido: '{actual_output}'"
                return {'status': 'wrong_answer', 'message': f'Resposta incorreta. {debug_msg}'}
        
        execution_time = (time.time() - start_time) * 1000
        
        if all_passed:
            submission.status = 'accepted'
            submission.execution_time = execution_time
            submission.save()
            return {'status': 'accepted', 'message': 'Todos os testes passaram'}
        else:
            submission.status = 'wrong_answer'
            submission.execution_time = execution_time
            submission.save()
            return {'status': 'wrong_answer', 'message': 'Resposta incorreta'}
    
    except Exception as e:
        submission.status = 'runtime_error'
        submission.error_message = str(e)
        submission.save()
        return {'status': 'runtime_error', 'message': f'Erro de execução: {str(e)}'}
    

    
# ADICIONE ESTAS FUNÇÕES ao final do seu challenges/views.py

# Função para submissão AJAX (que faltava)
@login_required
@require_POST  
def submit_solution_ajax(request, pk):
    """Nova view específica para submissões AJAX"""
    challenge = get_object_or_404(Challenge, pk=pk)
    
    try:
        # Pega dados do JSON
        data = json.loads(request.body)
        code = data.get('code', '').strip()
        
        if not code:
            return JsonResponse({
                'success': False,
                'error': 'Código não pode estar vazio'
            })
        
        # Cria submissão
        submission = Submission.objects.create(
            challenge=challenge,
            user=request.user,
            code=code,
            language=challenge.language,
            status='pending'
        )
        
        # Avalia usando sua função original
        result = evaluate_submission(submission)
        
        # Se aceito, marca como completado
        if result['status'] == 'accepted':
            try:
                profile = UserProfile.objects.get(user=request.user)
            except UserProfile.DoesNotExist:
                initial_state = BrazilState.objects.filter(order=1).first()
                profile = UserProfile.objects.create(
                    user=request.user,
                    current_state=initial_state
                )
            
            # Só adiciona pontos se ainda não completou
            if not profile.completed_challenges.filter(id=challenge.id).exists():
                profile.completed_challenges.add(challenge)
                profile.total_points += challenge.points
                profile.save()
                
                # Tenta desbloquear próximo estado
                next_unlocked = profile.unlock_next_state()
                
                return JsonResponse({
                    'success': True,
                    'status': 'accepted',
                    'message': 'Parabéns! Solução aceita!',
                    'points_earned': challenge.points,
                    'next_unlocked': next_unlocked,
                })
            else:
                return JsonResponse({
                    'success': True,
                    'status': 'accepted',
                    'message': 'Solução aceita! (já completado anteriormente)',
                    'points_earned': 0,
                    'next_unlocked': False,
                })
        else:
            return JsonResponse({
                'success': True,
                'status': result['status'],
                'message': result.get('message', 'Erro na execução'),
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erro interno: {str(e)}'
        })

# Função para listar submissões do usuário (opcional)
@login_required
def user_submissions(request):
    """Lista todas as submissões do usuário"""
    submissions = Submission.objects.filter(user=request.user).order_by('-submitted_at')
    
    context = {
        'submissions': submissions,
    }
    
    return render(request, 'challenges/user_submissions.html', context)

# Função para leaderboard (opcional)
@login_required
def leaderboard(request):
    """Exibe ranking dos usuários"""
    # Pega os top usuários por pontos
    try:
        profiles = UserProfile.objects.select_related('user').order_by('-total_points')[:50]
        
        # Encontra posição do usuário atual
        user_position = None
        user_profile = request.user.profile
        for i, profile in enumerate(profiles, 1):
            if profile.user == request.user:
                user_position = i
                break
                
        context = {
            'profiles': profiles,
            'user_position': user_position,
            'user_profile': user_profile,
        }
    except:
        context = {
            'profiles': [],
            'user_position': None,
            'user_profile': None,
        }
    
    return render(request, 'challenges/leaderboard.html', context)

@login_required
@require_POST  
def submit_solution_ajax(request, pk):
    """View específica para submissões AJAX com detecção de conclusão"""
    challenge = get_object_or_404(Challenge, pk=pk)
    
    try:
        # Pega dados do JSON
        data = json.loads(request.body)
        code = data.get('code', '').strip()
        
        if not code:
            return JsonResponse({
                'success': False,
                'error': 'Código não pode estar vazio'
            })
        
        # Cria submissão
        submission = Submission.objects.create(
            challenge=challenge,
            user=request.user,
            code=code,
            language=challenge.language,
            status='pending'
        )
        
        # Avalia usando sua função original
        result = evaluate_submission(submission)
        
        # Se aceito, marca como completado
        if result['status'] == 'accepted':
            try:
                profile = UserProfile.objects.get(user=request.user)
            except UserProfile.DoesNotExist:
                initial_state = BrazilState.objects.filter(order=1).first()
                profile = UserProfile.objects.create(
                    user=request.user,
                    current_state=initial_state
                )
            
            # Só adiciona pontos se ainda não completou
            if not profile.completed_challenges.filter(id=challenge.id).exists():
                profile.completed_challenges.add(challenge)
                profile.total_points += challenge.points
                profile.save()
                
                # Tenta desbloquear próximo estado
                next_unlocked = profile.unlock_next_state()
                
                # NOVO: Verificar se completou TODOS os desafios
                total_challenges = Challenge.objects.count()
                completed_challenges = profile.completed_challenges.count()
                all_completed = (completed_challenges == total_challenges)
                
                # NOVO: Verificar se é o último estado (Brasília/DF)
                is_final_state = challenge.state.abbreviation == 'DF'
                
                return JsonResponse({
                    'success': True,
                    'status': 'accepted',
                    'message': 'Parabéns! Solução aceita!',
                    'points_earned': challenge.points,
                    'next_unlocked': next_unlocked,
                    'all_completed': all_completed,  # NOVO
                    'is_final_state': is_final_state,  # NOVO
                    'total_points': profile.total_points,  # NOVO
                    'completed_count': completed_challenges,  # NOVO
                })
            else:
                return JsonResponse({
                    'success': True,
                    'status': 'accepted',
                    'message': 'Solução aceita! (já completado anteriormente)',
                    'points_earned': 0,
                    'next_unlocked': False,
                    'all_completed': False,
                    'is_final_state': False,
                })
        else:
            return JsonResponse({
                'success': True,
                'status': result['status'],
                'message': result.get('message', 'Erro na execução'),
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erro interno: {str(e)}'
        })

# Adicione esta view ao seu challenges/views.py

@login_required
def congratulations(request):
    """Tela de parabéns por completar todos os desafios"""
    try:
        profile = UserProfile.objects.get(user=request.user)
        
        # Verificar se realmente completou todos
        total_challenges = Challenge.objects.count()
        completed_challenges = profile.completed_challenges.count()
        
        if completed_challenges < total_challenges:
            messages.warning(request, "Você ainda não completou todos os desafios!")
            return redirect('home')
        
        # Estatísticas para mostrar na tela
        total_points = profile.total_points
        completion_percentage = 100
        
        # Desafios por região
        states_stats = []
        for state in BrazilState.objects.all().order_by('order'):
            try:
                challenge = state.challenge
                is_completed = profile.completed_challenges.filter(id=challenge.id).exists()
                states_stats.append({
                    'state': state,
                    'challenge': challenge,
                    'completed': is_completed
                })
            except:
                pass
        
        context = {
            'profile': profile,
            'total_points': total_points,
            'completed_challenges': completed_challenges,
            'total_challenges': total_challenges,
            'completion_percentage': completion_percentage,
            'states_stats': states_stats,
        }
        
        return render(request, 'challenges/congratulations.html', context)
        
    except UserProfile.DoesNotExist:
        messages.error(request, "Perfil não encontrado!")
        return redirect('home')
    