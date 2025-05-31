# challenges/views.py - Versão Corrigida

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError
from .models import Challenge, Submission, BrazilState
from accounts.models import UserProfile
from .java_executor import evaluate_java_submission
import json
import subprocess
import tempfile
import os
import time
import logging
import traceback
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError
import traceback

# Configurar logging
logger = logging.getLogger(__name__)

@login_required
def challenge_detail(request, pk):
    challenge = get_object_or_404(Challenge, pk=pk)
    
    # Tratamento de perfil inexistente
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
    
    # Adiciona informação se já completou
    is_completed = profile.completed_challenges.filter(id=challenge.id).exists()
    
    context = {
        'challenge': challenge,
        'submissions': submissions,
        'is_completed': is_completed,
        'profile': profile,
    }
    
    return render(request, 'challenges/challenge_detail.html', context)

# CORREÇÃO PARA O ERRO "signal only works in main thread"

# ===== OPÇÃO 1: REMOVER TIMEOUT COM SIGNAL =====
# Substitua sua função submit_solution_ajax por esta versão SEM signal:

@login_required
@csrf_exempt
@require_POST  
def submit_solution_ajax(request, pk):
    """
    View AJAX corrigida com verificação SEMPRE
    """
    import traceback
    
    try:
        logger.info(f"[SUBMIT] Starting AJAX submit for challenge {pk} by user {request.user.username}")
        
        # 1. Verificar challenge
        challenge = get_object_or_404(Challenge, pk=pk)
        logger.info(f"[SUBMIT] Challenge found: {challenge.title}")
        
        # 2. Verificar dados JSON
        try:
            data = json.loads(request.body)
            code = data.get('code', '').strip()
            logger.info(f"[SUBMIT] Code validated - Length: {len(code)} chars")
        except Exception as e:
            logger.error(f"[SUBMIT] JSON error: {e}")
            return JsonResponse({
                'success': False,
                'error': f'Erro ao processar dados: {str(e)}'
            })
        
        if not code:
            return JsonResponse({
                'success': False,
                'error': 'Código não pode estar vazio'
            })
        
        # 3. Criar submissão
        try:
            logger.info(f"[SUBMIT] Creating submission...")
            submission = Submission.objects.create(
                challenge=challenge,
                user=request.user,
                code=code,
                language=challenge.language,
                status='pending'
            )
            logger.info(f"[SUBMIT] Submission created: {submission.id}")
        except Exception as e:
            logger.error(f"[SUBMIT] Error creating submission: {e}")
            return JsonResponse({
                'success': False,
                'error': f'Erro ao criar submissão: {str(e)}'
            })
        
        # 4. Avaliar submissão
        try:
            logger.info(f"[SUBMIT] Starting evaluation...")
            result = evaluate_submission_safe(submission)
            logger.info(f"[SUBMIT] Evaluation completed: {result.get('status')}")
            
        except Exception as e:
            logger.error(f"[SUBMIT] Error in evaluation: {e}")
            logger.error(f"[SUBMIT] Traceback: {traceback.format_exc()}")
            return JsonResponse({
                'success': False,
                'error': f'Erro na avaliação: {str(e)}'
            })
        
        # 5. Processar resultado aceito
        if result['status'] == 'accepted':
            try:
                logger.info(f"[SUBMIT] Processing accepted result...")
                
                # Buscar ou criar perfil
                try:
                    profile = UserProfile.objects.get(user=request.user)
                except UserProfile.DoesNotExist:
                    initial_state = BrazilState.objects.filter(order=1).first()
                    profile = UserProfile.objects.create(
                        user=request.user,
                        current_state=initial_state
                    )
                
                # Verificar se já completou
                already_completed = profile.completed_challenges.filter(id=challenge.id).exists()
                logger.info(f"[SUBMIT] Already completed: {already_completed}")
                
                # SEMPRE VERIFICAR CONCLUSÃO TOTAL (independente se já completou)
                total_challenges = Challenge.objects.count()
                completed_challenges = profile.completed_challenges.count()
                all_completed = (completed_challenges >= total_challenges)
                
                # LOGS DE DEBUG DETALHADOS
                logger.info(f"[DEBUG] ======== COMPLETION CHECK ========")
                logger.info(f"[DEBUG] Challenge completed: {challenge.title}")
                logger.info(f"[DEBUG] Challenge state: {challenge.state.name} ({challenge.state.abbreviation})")
                logger.info(f"[DEBUG] Total challenges in DB: {total_challenges}")
                logger.info(f"[DEBUG] User completed challenges: {completed_challenges}")
                logger.info(f"[DEBUG] All completed calculation: {completed_challenges} >= {total_challenges} = {all_completed}")
                logger.info(f"[DEBUG] Already completed this challenge: {already_completed}")
                logger.info(f"[DEBUG] ===================================")
                
                if not already_completed:
                    # Primeira vez completando - adicionar pontos
                    profile.completed_challenges.add(challenge)
                    profile.total_points += challenge.points
                    profile.save()
                    logger.info(f"[SUBMIT] Points added: {challenge.points}")
                    
                    # Tentar desbloquear próximo estado
                    try:
                        next_unlocked = profile.unlock_next_state()
                        logger.info(f"[SUBMIT] Next state unlocked: {next_unlocked}")
                    except Exception as e:
                        logger.warning(f"[SUBMIT] Error unlocking next state: {e}")
                        next_unlocked = False
                    
                    response_data = {
                        'success': True,
                        'status': 'accepted',
                        'message': 'Parabéns! Solução aceita!',
                        'points_earned': challenge.points,
                        'next_unlocked': next_unlocked,
                        'all_completed': all_completed,
                        'total_points': profile.total_points,
                        'completed_count': completed_challenges,
                        'total_count': total_challenges,
                        'challenge_state': challenge.state.abbreviation,
                    }
                else:
                    # Já foi completado - não dar pontos, mas ainda verificar conclusão
                    response_data = {
                        'success': True,
                        'status': 'accepted',
                        'message': 'Solução aceita! (já completado anteriormente)',
                        'points_earned': 0,
                        'next_unlocked': False,
                        'already_completed': True,
                        'all_completed': all_completed,  # IMPORTANTE: incluir sempre
                        'total_points': profile.total_points,
                        'completed_count': completed_challenges,
                        'total_count': total_challenges,
                    }
                
                # VERIFICAR SE DEVE REDIRECIONAR PARA PARABÉNS (SEMPRE)
                if all_completed:
                    logger.info(f"[DEBUG] ✅ ALL CHALLENGES COMPLETED! Adding redirect to congratulations!")
                    response_data.update({
                        'redirect_to': '/challenges/congratulations/',
                        'message': '🎉 PARABÉNS! Você completou todos os desafios do Brasil! 🇧🇷',
                        'show_congratulations': True,
                        'completion_type': 'full_completion'
                    })
                
                logger.info(f"[DEBUG] Final response data: {response_data}")
                return JsonResponse(response_data)
                    
            except Exception as e:
                logger.error(f"[SUBMIT] Error processing accepted result: {e}")
                logger.error(f"[SUBMIT] Traceback: {traceback.format_exc()}")
                return JsonResponse({
                    'success': False,
                    'error': f'Erro ao processar resultado: {str(e)}'
                })
        else:
            # Resultado não aceito
            logger.info(f"[SUBMIT] Solution not accepted: {result['status']}")
            return JsonResponse({
                'success': True,
                'status': result['status'],
                'message': result.get('message', 'Erro na execução'),
                'error_details': result.get('error_details'),
            })
            
    except Exception as e:
        logger.error(f"[SUBMIT] Critical error: {e}")
        logger.error(f"[SUBMIT] Full traceback: {traceback.format_exc()}")
        return JsonResponse({
            'success': False,
            'error': f'Erro interno: {str(e)}'
        })   


# ===== NOVA FUNÇÃO evaluate_submission_safe =====
# Adicione esta função no seu views.py:

def evaluate_submission_safe(submission):
    """
    Função de avaliação SEM uso de signal (que não funciona em threads)
    """
    try:
        challenge = submission.challenge
        language = submission.language
        
        # Validações básicas
        if not submission.code.strip():
            submission.status = 'compilation_error'
            submission.error_message = 'Código vazio'
            submission.save()
            return {'status': 'compilation_error', 'message': 'Código vazio'}
        
        if not challenge.test_cases:
            submission.status = 'runtime_error'
            submission.error_message = 'Nenhum caso de teste encontrado'
            submission.save()
            return {'status': 'runtime_error', 'message': 'Nenhum caso de teste encontrado'}
        
        # Status inicial
        submission.status = 'running'
        submission.save()
        
        logger.info(f"[EVAL] Starting evaluation for submission {submission.id} - Language: {language.name}")
        
        # CORREÇÃO: Usar timeout do subprocess ao invés de signal
        if language.name.lower() == 'java':
            return evaluate_java_submission_safe(submission)
        else:
            return evaluate_other_languages_safe(submission)
            
    except Exception as e:
        logger.error(f"[EVAL] Critical error in evaluate_submission_safe: {e}")
        submission.status = 'runtime_error'
        submission.error_message = f'Erro crítico: {str(e)}'
        submission.save()
        return {'status': 'runtime_error', 'message': f'Erro crítico: {str(e)}'}


# ===== FUNÇÃO JAVA CORRIGIDA =====
# Adicione esta função no seu views.py:

def evaluate_java_submission_safe(submission):
    """
    Avaliação Java SEM signal timeout
    """
    from .java_executor import JavaCodeExecutor
    
    try:
        challenge = submission.challenge
        
        # Criar executor com timeouts internos (sem signal)
        executor = JavaCodeExecutor(
            time_limit=challenge.time_limit,
            memory_limit=128
        )
        
        # Avaliar submissão
        result = executor.evaluate_submission(
            submission.code,
            challenge.test_cases
        )
        
        # Mapear status
        status_mapping = {
            'accepted': 'accepted',
            'compilation_error': 'compilation_error',
            'compilation_timeout': 'compilation_error',
            'runtime_error': 'runtime_error',
            'time_limit_exceeded': 'time_limit',
            'wrong_answer': 'wrong_answer',
            'evaluation_error': 'runtime_error',
            'test_error': 'runtime_error'
        }
        
        submission.status = status_mapping.get(result['status'], 'runtime_error')
        submission.execution_time = result.get('execution_time', 0)
        submission.error_message = result.get('message', '')
        
        if result.get('failed_test_case'):
            submission.error_message += f" (Falha no caso de teste {result['failed_test_case']})"
        
        submission.save()
        
        logger.info(f"[EVAL] Java evaluation completed: {submission.status}")
        return result
        
    except Exception as e:
        logger.error(f"[EVAL] Error in Java evaluation: {e}")
        submission.status = 'runtime_error'
        submission.error_message = f'Erro na avaliação Java: {str(e)}'
        submission.save()
        
        return {
            'status': 'runtime_error',
            'message': f'Erro na avaliação Java: {str(e)}'
        }


# ===== FUNÇÃO OUTRAS LINGUAGENS CORRIGIDA =====
# Adicione esta função no seu views.py:

def evaluate_other_languages_safe(submission):
    """
    Avaliação para Python, C, C++ SEM signal timeout
    """
    import subprocess
    import tempfile
    import os
    import time
    
    challenge = submission.challenge
    language = submission.language
    code = submission.code
    
    temp_files = []
    
    try:
        logger.info(f"[EVAL] Evaluating {language.name} code - {len(challenge.test_cases)} test cases")
        
        start_time = time.time()
        
        for i, test_case in enumerate(challenge.test_cases, 1):
            test_input = str(test_case.get('input', ''))
            expected_output = str(test_case.get('output', '')).strip()
            
            # Criar arquivo temporário
            with tempfile.NamedTemporaryFile(
                suffix=f'.{language.extension}', 
                delete=False,
                mode='w',
                encoding='utf-8'
            ) as temp_file:
                temp_file.write(code)
                temp_file_path = temp_file.name
                temp_files.append(temp_file_path)
            
            # Executar baseado na linguagem
            try:
                if language.name.lower() == 'python':
                    result = run_python_safe(temp_file_path, test_input, challenge.time_limit)
                elif language.name.lower() == 'c':
                    result = run_c_safe(temp_file_path, test_input, challenge.time_limit)
                elif language.name.lower() in ['c++', 'cpp']:
                    result = run_cpp_safe(temp_file_path, test_input, challenge.time_limit)
                else:
                    raise ValueError(f"Linguagem não suportada: {language.name}")
                
                # Verificar resultado
                if not result['success']:
                    submission.status = result['status']
                    submission.error_message = result['message']
                    submission.save()
                    return result
                
                # Comparar saída
                actual_output = result['output'].strip()
                
                if actual_output != expected_output:
                    submission.status = 'wrong_answer'
                    submission.save()
                    
                    return {
                        'status': 'wrong_answer', 
                        'message': f'Resposta incorreta no teste {i}',
                        'test_case': i,
                        'expected': expected_output,
                        'actual': actual_output
                    }
                
            except Exception as e:
                logger.error(f"[EVAL] Error in test case {i}: {e}")
                submission.status = 'runtime_error'
                submission.error_message = f'Erro no teste {i}: {str(e)}'
                submission.save()
                return {'status': 'runtime_error', 'message': f'Erro no teste {i}: {str(e)}'}
        
        # Todos os testes passaram
        execution_time = (time.time() - start_time) * 1000
        submission.status = 'accepted'
        submission.execution_time = execution_time
        submission.save()
        
        return {
            'status': 'accepted', 
            'message': f'Todos os {len(challenge.test_cases)} testes passaram',
            'execution_time': execution_time,
            'passed_tests': len(challenge.test_cases),
            'total_tests': len(challenge.test_cases)
        }
    
    except Exception as e:
        logger.error(f"[EVAL] Critical error in language evaluation: {e}")
        submission.status = 'runtime_error'
        submission.error_message = f'Erro crítico: {str(e)}'
        submission.save()
        return {'status': 'runtime_error', 'message': f'Erro crítico: {str(e)}'}
    
    finally:
        # Cleanup
        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
                if temp_file.endswith(('.c', '.cpp')):
                    out_file = temp_file + '.out'
                    if os.path.exists(out_file):
                        os.unlink(out_file)
            except:
                pass


# ===== FUNÇÕES AUXILIARES =====
# Adicione estas funções no seu views.py:

def run_python_safe(file_path, test_input, time_limit_ms):
    """Executa Python com timeout do subprocess"""
    try:
        proc = subprocess.run(
            ['python3', file_path],
            input=test_input,
            capture_output=True,
            text=True,
            timeout=max(time_limit_ms / 1000, 5)  # Mínimo 5 segundos
        )
        
        if proc.returncode != 0:
            error_msg = proc.stderr.strip() or "Erro de execução"
            return {'success': False, 'status': 'runtime_error', 'message': error_msg}
        
        return {'success': True, 'output': proc.stdout}
        
    except subprocess.TimeoutExpired:
        return {'success': False, 'status': 'time_limit', 'message': 'Tempo limite excedido'}
    except Exception as e:
        return {'success': False, 'status': 'runtime_error', 'message': str(e)}

def run_c_safe(file_path, test_input, time_limit_ms):
    """Compila e executa C com timeout"""
    try:
        # Compilar
        compile_proc = subprocess.run(
            ['gcc', file_path, '-o', f'{file_path}.out', '-std=c11', '-Wall', '-lm'],
            capture_output=True,
            text=True,
            timeout=15
        )
        
        if compile_proc.returncode != 0:
            error_msg = compile_proc.stderr.strip() or "Erro de compilação"
            return {'success': False, 'status': 'compilation_error', 'message': error_msg}
        
        # Executar
        proc = subprocess.run(
            [f'{file_path}.out'],
            input=test_input,
            capture_output=True,
            text=True,
            timeout=max(time_limit_ms / 1000, 5)
        )
        
        if proc.returncode != 0:
            error_msg = proc.stderr.strip() or "Erro de execução"
            return {'success': False, 'status': 'runtime_error', 'message': error_msg}
        
        return {'success': True, 'output': proc.stdout}
        
    except subprocess.TimeoutExpired:
        return {'success': False, 'status': 'time_limit', 'message': 'Tempo limite excedido'}
    except Exception as e:
        return {'success': False, 'status': 'runtime_error', 'message': str(e)}

def run_cpp_safe(file_path, test_input, time_limit_ms):
    """Compila e executa C++ com timeout"""
    try:
        # Compilar
        compile_proc = subprocess.run(
            ['g++', file_path, '-o', f'{file_path}.out', '-std=c++17', '-Wall', '-O2', '-lm'],
            capture_output=True,
            text=True,
            timeout=15
        )
        
        if compile_proc.returncode != 0:
            error_msg = compile_proc.stderr.strip() or "Erro de compilação"
            return {'success': False, 'status': 'compilation_error', 'message': error_msg}
        
        # Executar
        proc = subprocess.run(
            [f'{file_path}.out'],
            input=test_input,
            capture_output=True,
            text=True,
            timeout=max(time_limit_ms / 1000, 5)
        )
        
        if proc.returncode != 0:
            error_msg = proc.stderr.strip() or "Erro de execução"
            return {'success': False, 'status': 'runtime_error', 'message': error_msg}
        
        return {'success': True, 'output': proc.stdout}
        
    except subprocess.TimeoutExpired:
        return {'success': False, 'status': 'time_limit', 'message': 'Tempo limite excedido'}
    except Exception as e:
        return {'success': False, 'status': 'runtime_error', 'message': str(e)}

# CORREÇÃO: View legacy melhorada
@login_required
def submit_solution(request, challenge_id):
    """View tradicional para submissão via form - mantida para compatibilidade"""
    challenge = get_object_or_404(Challenge, pk=challenge_id)
    
    if request.method == 'POST':
        code = request.POST.get('code', '').strip()
        
        if not code:
            messages.error(request, "Código não pode estar vazio")
            return redirect('challenge-detail', pk=challenge_id)
        
        try:
            submission = Submission.objects.create(
                challenge=challenge,
                user=request.user,
                code=code,
                language=challenge.language,
                status='pending'
            )
            
            # Avalia submissão
            result = evaluate_submission(submission)
            
            if result['status'] == 'accepted':
                profile = UserProfile.objects.get(user=request.user)
                
                if not profile.completed_challenges.filter(id=challenge.id).exists():
                    profile.completed_challenges.add(challenge)
                    profile.total_points += challenge.points
                    profile.save()
                    profile.unlock_next_state()
                    messages.success(request, "Parabéns! Seu código foi aceito!")
                else:
                    messages.info(request, "Código aceito! (já completado anteriormente)")
            else:
                messages.error(request, f"Submissão rejeitada: {result['message']}")
            
            return redirect('submission-result', submission_id=submission.id)
            
        except Exception as e:
            logger.error(f"Error in legacy submit: {e}")
            messages.error(request, f"Erro ao processar submissão: {str(e)}")
    
    return redirect('challenge-detail', pk=challenge_id)

def evaluate_submission(submission):
    """
    Função principal de avaliação com melhor tratamento de erros
    CORREÇÃO: Timeout e validação melhorada
    """
    try:
        challenge = submission.challenge
        language = submission.language
        
        # Validações básicas
        if not submission.code.strip():
            submission.status = 'compilation_error'
            submission.error_message = 'Código vazio'
            submission.save()
            return {'status': 'compilation_error', 'message': 'Código vazio'}
        
        if not challenge.test_cases:
            submission.status = 'runtime_error'
            submission.error_message = 'Nenhum caso de teste encontrado'
            submission.save()
            return {'status': 'runtime_error', 'message': 'Nenhum caso de teste encontrado'}
        
        # Status inicial
        submission.status = 'running'
        submission.save()
        
        logger.info(f"[EVAL] Starting evaluation for submission {submission.id} - Language: {language.name}")
        
        # Avaliação por linguagem
        if language.name.lower() == 'java':
            from .java_executor_render import evaluate_java_submission_render
            return evaluate_java_submission_render(submission)
        else:
            return evaluate_other_languages_improved(submission)
            
    except Exception as e:
        logger.error(f"[EVAL] Critical error in evaluate_submission: {e}")
        logger.error(f"[EVAL] Traceback: {traceback.format_exc()}")
        submission.status = 'runtime_error'
        submission.error_message = f'Erro crítico: {str(e)}'
        submission.save()
        return {'status': 'runtime_error', 'message': f'Erro crítico: {str(e)}'}

def evaluate_other_languages_improved(submission):
    """
    CORREÇÃO: Avaliação melhorada para Python, C, C++
    """
    challenge = submission.challenge
    language = submission.language
    code = submission.code
    
    temp_files = []  # Lista para cleanup
    
    try:
        logger.info(f"[EVAL] Evaluating {language.name} code - {len(challenge.test_cases)} test cases")
        
        start_time = time.time()
        
        for i, test_case in enumerate(challenge.test_cases, 1):
            logger.debug(f"[EVAL] Running test case {i}/{len(challenge.test_cases)}")
            
            test_input = test_case.get('input', '')
            expected_output = test_case.get('output', '').strip()
            
            # CORREÇÃO: Melhor tratamento de casos de teste
            if not isinstance(test_input, str):
                test_input = str(test_input)
            if not isinstance(expected_output, str):
                expected_output = str(expected_output)
            
            # Criar arquivo temporário com nome único
            import uuid
            temp_id = str(uuid.uuid4())[:8]
            temp_file = tempfile.NamedTemporaryFile(
                suffix=f'_{temp_id}.{language.extension}', 
                delete=False,
                mode='w',
                encoding='utf-8'
            )
            
            try:
                temp_file.write(code)
                temp_file.flush()
                temp_file_path = temp_file.name
                temp_files.append(temp_file_path)
                
            finally:
                temp_file.close()
            
            # Executar baseado na linguagem
            try:
                if language.name.lower() == 'python':
                    result = run_python_code(temp_file_path, test_input, challenge.time_limit)
                elif language.name.lower() == 'c':
                    result = run_c_code(temp_file_path, test_input, challenge.time_limit)
                elif language.name.lower() in ['c++', 'cpp']:
                    result = run_cpp_code(temp_file_path, test_input, challenge.time_limit)
                else:
                    raise ValueError(f"Linguagem não suportada: {language.name}")
                
                # Verificar resultado
                if not result['success']:
                    submission.status = result['status']
                    submission.error_message = result['message']
                    submission.save()
                    return result
                
                # Comparar saída
                actual_output = result['output'].strip()
                
                if actual_output != expected_output:
                    submission.status = 'wrong_answer'
                    submission.save()
                    
                    debug_msg = f"Teste {i}: Esperado '{expected_output}', Obtido '{actual_output}'"
                    logger.info(f"[EVAL] Wrong answer: {debug_msg}")
                    
                    return {
                        'status': 'wrong_answer', 
                        'message': f'Resposta incorreta no teste {i}',
                        'test_case': i,
                        'expected': expected_output,
                        'actual': actual_output
                    }
                
                logger.debug(f"[EVAL] Test case {i} passed")
                
            except Exception as e:
                logger.error(f"[EVAL] Error in test case {i}: {e}")
                submission.status = 'runtime_error'
                submission.error_message = f'Erro no teste {i}: {str(e)}'
                submission.save()
                return {'status': 'runtime_error', 'message': f'Erro no teste {i}: {str(e)}'}
        
        # Todos os testes passaram
        execution_time = (time.time() - start_time) * 1000
        submission.status = 'accepted'
        submission.execution_time = execution_time
        submission.save()
        
        logger.info(f"[EVAL] All tests passed - Execution time: {execution_time:.2f}ms")
        
        return {
            'status': 'accepted', 
            'message': f'Todos os {len(challenge.test_cases)} testes passaram',
            'execution_time': execution_time,
            'passed_tests': len(challenge.test_cases),
            'total_tests': len(challenge.test_cases)
        }
    
    except Exception as e:
        logger.error(f"[EVAL] Critical error in language evaluation: {e}")
        logger.error(f"[EVAL] Traceback: {traceback.format_exc()}")
        submission.status = 'runtime_error'
        submission.error_message = f'Erro crítico: {str(e)}'
        submission.save()
        return {'status': 'runtime_error', 'message': f'Erro crítico: {str(e)}'}
    
    finally:
        # CORREÇÃO: Cleanup garantido
        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
                # Cleanup de arquivos compilados
                if temp_file.endswith('.c') or temp_file.endswith('.cpp'):
                    out_file = temp_file + '.out'
                    if os.path.exists(out_file):
                        os.unlink(out_file)
            except:
                pass

def run_python_code(file_path, test_input, time_limit_ms):
    """Executa código Python com timeout"""
    try:
        proc = subprocess.Popen(
            ['python3', file_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        stdout, stderr = proc.communicate(
            input=test_input, 
            timeout=time_limit_ms / 1000
        )
        
        if proc.returncode != 0:
            error_msg = stderr.strip() or "Erro de execução"
            return {'success': False, 'status': 'runtime_error', 'message': error_msg}
        
        return {'success': True, 'output': stdout}
        
    except subprocess.TimeoutExpired:
        proc.kill()
        return {'success': False, 'status': 'time_limit', 'message': 'Tempo limite excedido'}
    except Exception as e:
        return {'success': False, 'status': 'runtime_error', 'message': str(e)}

def run_c_code(file_path, test_input, time_limit_ms):
    """Compila e executa código C"""
    try:
        # Compilar
        compile_proc = subprocess.run(
            ['gcc', file_path, '-o', f'{file_path}.out', '-std=c11', '-Wall', '-lm'],
            capture_output=True,
            text=True,
            timeout=15
        )
        
        if compile_proc.returncode != 0:
            error_msg = compile_proc.stderr.strip() or "Erro de compilação"
            return {'success': False, 'status': 'compilation_error', 'message': error_msg}
        
        # Executar
        proc = subprocess.Popen(
            [f'{file_path}.out'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        stdout, stderr = proc.communicate(
            input=test_input,
            timeout=time_limit_ms / 1000
        )
        
        if proc.returncode != 0:
            error_msg = stderr.strip() or "Erro de execução"
            return {'success': False, 'status': 'runtime_error', 'message': error_msg}
        
        return {'success': True, 'output': stdout}
        
    except subprocess.TimeoutExpired:
        proc.kill()
        return {'success': False, 'status': 'time_limit', 'message': 'Tempo limite excedido'}
    except Exception as e:
        return {'success': False, 'status': 'runtime_error', 'message': str(e)}

def run_cpp_code(file_path, test_input, time_limit_ms):
    """Compila e executa código C++"""
    try:
        # Compilar
        compile_proc = subprocess.run(
            ['g++', file_path, '-o', f'{file_path}.out', '-std=c++17', '-Wall', '-O2', '-lm'],
            capture_output=True,
            text=True,
            timeout=15
        )
        
        if compile_proc.returncode != 0:
            error_msg = compile_proc.stderr.strip() or "Erro de compilação"
            return {'success': False, 'status': 'compilation_error', 'message': error_msg}
        
        # Executar
        proc = subprocess.Popen(
            [f'{file_path}.out'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        stdout, stderr = proc.communicate(
            input=test_input,
            timeout=time_limit_ms / 1000
        )
        
        if proc.returncode != 0:
            error_msg = stderr.strip() or "Erro de execução"
            return {'success': False, 'status': 'runtime_error', 'message': error_msg}
        
        return {'success': True, 'output': stdout}
        
    except subprocess.TimeoutExpired:
        proc.kill()
        return {'success': False, 'status': 'time_limit', 'message': 'Tempo limite excedido'}
    except Exception as e:
        return {'success': False, 'status': 'runtime_error', 'message': str(e)}

# Views restantes mantidas como estavam
@login_required
def submission_result(request, submission_id):
    submission = get_object_or_404(Submission, pk=submission_id, user=request.user)
    
    context = {
        'submission': submission,
        'challenge': submission.challenge,
    }
    
    return render(request, 'challenges/results.html', context)

@login_required
def user_submissions(request):
    """Lista todas as submissões do usuário"""
    submissions = Submission.objects.filter(user=request.user).order_by('-submitted_at')
    
    context = {
        'submissions': submissions,
    }
    
    return render(request, 'challenges/user_submissions.html', context)

# Adicione esta função no seu challenges/views.py

# VERSÃO SIMPLIFICADA PARA DEBUG
# Substitua temporariamente a view leaderboard por esta versão

def leaderboard(request):
    """
    View simplificada para debug do leaderboard
    """
    try:
        # Import básico para testar
        from django.contrib.auth.models import User
        from django.db.models import Sum, Count
        from .models import Challenge, Submission
        
        # Teste básico 1: Verificar se consegue acessar os modelos
        print("DEBUG: Tentando acessar modelos...")
        
        total_users = User.objects.count()
        total_challenges = Challenge.objects.count()
        total_submissions = Submission.objects.count()
        
        print(f"DEBUG: {total_users} usuários, {total_challenges} desafios, {total_submissions} submissões")
        
        # Teste básico 2: Buscar usuários com submissões aceitas
        print("DEBUG: Buscando usuários com submissões aceitas...")
        
        users_with_accepted = User.objects.filter(
            submission__status='accepted'
        ).distinct()
        
        print(f"DEBUG: {users_with_accepted.count()} usuários com submissões aceitas")
        
        # Criar lista simples para teste
        users_data = []
        
        for user in users_with_accepted[:10]:  # Limitar a 10 para debug
            try:
                # Buscar dados básicos do usuário
                user_submissions = Submission.objects.filter(
                    user=user,
                    status='accepted'
                )
                
                total_points = 0
                completed_challenges = 0
                
                # Calcular pontos de forma mais segura
                for submission in user_submissions:
                    if submission.challenge and submission.challenge.points:
                        total_points += submission.challenge.points
                
                # Contar desafios únicos completados
                completed_challenges = user_submissions.values('challenge').distinct().count()
                
                # Calcular porcentagem
                completion_percentage = round((completed_challenges / total_challenges) * 100) if total_challenges > 0 else 0
                
                users_data.append({
                    'user': user,
                    'total_points': total_points,
                    'completed_challenges': completed_challenges,
                    'completion_percentage': completion_percentage,
                })
                
                print(f"DEBUG: Usuário {user.username}: {total_points} pontos, {completed_challenges} desafios")
                
            except Exception as e:
                print(f"DEBUG: Erro ao processar usuário {user.username}: {str(e)}")
                continue
        
        # Ordenar por pontos
        users_data.sort(key=lambda x: (x['total_points'], x['completed_challenges']), reverse=True)
        
        print(f"DEBUG: Processados {len(users_data)} usuários com sucesso")
        
        # Estatísticas do usuário atual
        user_stats = None
        if request.user.is_authenticated:
            print(f"DEBUG: Usuário logado: {request.user.username}")
            
            for index, user_data in enumerate(users_data):
                if user_data['user'] == request.user:
                    user_stats = user_data.copy()
                    user_stats['position'] = index + 1
                    break
            
            if not user_stats:
                user_stats = {
                    'position': None,
                    'total_points': 0,
                    'completed_challenges': 0,
                    'completion_percentage': 0,
                }
        
        # Estatísticas gerais simplificadas
        completed_users = len([u for u in users_data if u['completed_challenges'] == total_challenges])
        
        context = {
            'users': users_data,
            'user_stats': user_stats,
            'total_users': total_users,
            'completed_users': completed_users,
            'total_submissions': total_submissions,
            'total_points': sum(u['total_points'] for u in users_data),
        }
        
        print("DEBUG: Context preparado com sucesso")
        print(f"DEBUG: Context keys: {list(context.keys())}")
        
        return render(request, 'challenges/leaderboard.html', context)
        
    except Exception as e:
        # Se houver qualquer erro, mostrar no log e retornar template mínimo
        print(f"DEBUG: ERRO na view leaderboard: {str(e)}")
        print(f"DEBUG: Tipo do erro: {type(e).__name__}")
        
        import traceback
        print(f"DEBUG: Traceback completo:")
        print(traceback.format_exc())
        
        # Context mínimo para não quebrar o template
        context = {
            'users': [],
            'user_stats': None,
            'total_users': 0,
            'completed_users': 0,
            'total_submissions': 0,
            'total_points': 0,
            'error_message': str(e),
        }
        
        return render(request, 'challenges/leaderboard.html', context)

@login_required
def test_congratulations(request):
    """View temporária para testar a página de parabéns"""
    # Forçar redirecionamento para congratulations
    return redirect('congratulations')

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
    
@csrf_exempt
def debug_submit(request):
    """
    View de debug para identificar exatamente o que está causando o 400
    ADICIONE ESTA VIEW NO FINAL DO SEU ARQUIVO views.py
    """
    response_data = {
        'method': request.method,
        'content_type': request.content_type,
        'user_authenticated': request.user.is_authenticated,
        'user': str(request.user) if request.user.is_authenticated else None,
        'headers': {},
        'body_info': {},
        'debug_info': {}
    }
    
    # Capturar headers importantes
    for header in ['Content-Type', 'Content-Length', 'X-CSRFToken']:
        value = request.META.get(f'HTTP_{header.upper().replace("-", "_")}')
        if value:
            response_data['headers'][header] = value
    
    # Analisar body
    try:
        body_raw = request.body
        response_data['body_info'] = {
            'length': len(body_raw),
            'encoding': 'utf-8' if body_raw else 'empty',
            'preview': body_raw.decode('utf-8')[:200] if body_raw else 'empty'
        }
        
        # Tentar parse JSON
        if body_raw:
            try:
                data = json.loads(body_raw)
                response_data['json_valid'] = True
                response_data['json_keys'] = list(data.keys()) if isinstance(data, dict) else 'not_dict'
                response_data['json_types'] = {k: type(v).__name__ for k, v in data.items()} if isinstance(data, dict) else {}
                
                # Verificar campo code especificamente
                if 'code' in data:
                    code = data['code']
                    response_data['code_info'] = {
                        'type': type(code).__name__,
                        'length': len(code) if isinstance(code, str) else 'not_string',
                        'empty_after_strip': not code.strip() if isinstance(code, str) else 'not_string',
                        'preview': code[:100] if isinstance(code, str) else str(code)[:100]
                    }
                
            except json.JSONDecodeError as e:
                response_data['json_valid'] = False
                response_data['json_error'] = str(e)
        else:
            response_data['json_valid'] = False
            response_data['json_error'] = 'empty_body'
            
    except Exception as e:
        response_data['body_error'] = str(e)
    
    return JsonResponse(response_data)

@login_required
@csrf_exempt
@require_POST  
def submit_solution_ajax_debug(request, pk):
    """
    SUBSTITUA TEMPORARIAMENTE SUA FUNÇÃO submit_solution_ajax POR ESTA
    """
    logger = logging.getLogger(__name__)
    
    # Log inicial
    logger.info(f"[SUBMIT] Request received - Method: {request.method}, Content-Type: {request.content_type}")
    logger.info(f"[SUBMIT] User: {request.user}, Authenticated: {request.user.is_authenticated}")
    logger.info(f"[SUBMIT] Challenge PK: {pk}")
    
    # 1. VERIFICAR MÉTODO E CONTENT-TYPE
    if request.method != 'POST':
        logger.error(f"[SUBMIT] Invalid method: {request.method}")
        return JsonResponse({
            'success': False,
            'error': 'Método deve ser POST',
            'debug': {'method': request.method}
        }, status=400)
    
    if request.content_type != 'application/json':
        logger.error(f"[SUBMIT] Invalid content-type: {request.content_type}")
        return JsonResponse({
            'success': False,
            'error': 'Content-Type deve ser application/json',
            'debug': {'content_type': request.content_type}
        }, status=400)
    
    # 2. VERIFICAR AUTENTICAÇÃO
    if not request.user.is_authenticated:
        logger.error("[SUBMIT] User not authenticated")
        return JsonResponse({
            'success': False,
            'error': 'Usuário deve estar logado'
        }, status=401)
    
    # 3. VERIFICAR CHALLENGE
    try:
        challenge = Challenge.objects.get(pk=pk)
        logger.info(f"[SUBMIT] Challenge found: {challenge.title}")
    except Challenge.DoesNotExist:
        logger.error(f"[SUBMIT] Challenge {pk} not found")
        return JsonResponse({
            'success': False,
            'error': f'Desafio {pk} não encontrado'
        }, status=404)
    except Exception as e:
        logger.error(f"[SUBMIT] Error getting challenge: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Erro ao buscar desafio',
            'debug': {'error': str(e)}
        }, status=500)
    
    # 4. VERIFICAR BODY
    try:
        body_raw = request.body
        logger.info(f"[SUBMIT] Body length: {len(body_raw)}")
        
        if not body_raw:
            logger.error("[SUBMIT] Empty body")
            return JsonResponse({
                'success': False,
                'error': 'Request body vazio'
            }, status=400)
        
        # Log do body (primeiros 200 chars)
        body_preview = body_raw.decode('utf-8')[:200]
        logger.info(f"[SUBMIT] Body preview: {body_preview}")
        
    except Exception as e:
        logger.error(f"[SUBMIT] Error reading body: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Erro ao ler request body',
            'debug': {'error': str(e)}
        }, status=400)
    
    # 5. VERIFICAR JSON
    try:
        data = json.loads(body_raw)
        logger.info(f"[SUBMIT] JSON parsed successfully - Keys: {list(data.keys())}")
        
        if not isinstance(data, dict):
            logger.error(f"[SUBMIT] Data is not dict: {type(data)}")
            return JsonResponse({
                'success': False,
                'error': 'Dados devem ser um objeto JSON',
                'debug': {'data_type': type(data).__name__}
            }, status=400)
            
    except json.JSONDecodeError as e:
        logger.error(f"[SUBMIT] JSON decode error: {e}")
        return JsonResponse({
            'success': False,
            'error': 'JSON inválido',
            'debug': {'json_error': str(e), 'body_preview': body_preview}
        }, status=400)
    except Exception as e:
        logger.error(f"[SUBMIT] Error parsing JSON: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Erro ao processar JSON',
            'debug': {'error': str(e)}
        }, status=400)
    
    # 6. VERIFICAR CAMPO CODE
    try:
        if 'code' not in data:
            logger.error("[SUBMIT] Missing 'code' field")
            return JsonResponse({
                'success': False,
                'error': "Campo 'code' é obrigatório",
                'debug': {'available_keys': list(data.keys())}
            }, status=400)
        
        code = data['code']
        logger.info(f"[SUBMIT] Code field found - Type: {type(code).__name__}")
        
        if not isinstance(code, str):
            logger.error(f"[SUBMIT] Code is not string: {type(code)}")
            return JsonResponse({
                'success': False,
                'error': "Campo 'code' deve ser uma string",
                'debug': {'code_type': type(code).__name__}
            }, status=400)
        
        code = code.strip()
        logger.info(f"[SUBMIT] Code length after strip: {len(code)}")
        
        if not code:
            logger.error("[SUBMIT] Empty code after strip")
            return JsonResponse({
                'success': False,
                'error': 'Código não pode estar vazio'
            }, status=400)
        
        if len(code) > 50000:
            logger.error(f"[SUBMIT] Code too long: {len(code)}")
            return JsonResponse({
                'success': False,
                'error': 'Código muito longo (máximo 50KB)',
                'debug': {'code_length': len(code)}
            }, status=400)
            
    except Exception as e:
        logger.error(f"[SUBMIT] Error validating code: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Erro ao validar código',
            'debug': {'error': str(e)}
        }, status=400)
    
    # RETORNAR SUCESSO SEM AVALIAR (para teste)
    return JsonResponse({
        'success': True,
        'message': 'Submissão validada com sucesso (modo debug)',
        'debug': {
            'challenge': challenge.title,
            'code_length': len(code),
            'language': challenge.language.name
        }
    })

@csrf_exempt
def debug_challenge_data(request, challenge_id):
    """
    Debug específico para um desafio
    """
    try:
        challenge = Challenge.objects.get(id=challenge_id)
        
        # Dados básicos
        response_data = {
            'challenge_id': challenge.id,
            'title': challenge.title,
            'state': challenge.state.name,
            'language': challenge.language.name,
            'difficulty': challenge.difficulty,
            'points': challenge.points,
            'time_limit': challenge.time_limit,
            'test_cases_info': {},
            'validation_errors': [],
            'encoding_issues': []
        }
        
        # Analisar test_cases
        if challenge.test_cases:
            response_data['test_cases_info'] = {
                'type': type(challenge.test_cases).__name__,
                'count': len(challenge.test_cases),
                'cases': []
            }
            
            for i, test_case in enumerate(challenge.test_cases):
                case_info = {
                    'index': i,
                    'type': type(test_case).__name__,
                    'valid': True,
                    'errors': []
                }
                
                if isinstance(test_case, dict):
                    case_info['keys'] = list(test_case.keys())
                    
                    # Verificar campos obrigatórios
                    if 'input' not in test_case:
                        case_info['errors'].append('Missing input field')
                        case_info['valid'] = False
                    
                    if 'output' not in test_case:
                        case_info['errors'].append('Missing output field')
                        case_info['valid'] = False
                    
                    # Verificar tipos
                    input_val = test_case.get('input')
                    output_val = test_case.get('output')
                    
                    case_info['input_type'] = type(input_val).__name__
                    case_info['output_type'] = type(output_val).__name__
                    
                    # Verificar encoding
                    for field_name, field_val in [('input', input_val), ('output', output_val)]:
                        if field_val is not None:
                            try:
                                str(field_val).encode('utf-8')
                            except Exception as e:
                                case_info['errors'].append(f'{field_name} encoding error: {str(e)}')
                                case_info['valid'] = False
                    
                    # Verificar se são strings ou podem ser convertidas
                    try:
                        str(input_val)
                        str(output_val)
                    except Exception as e:
                        case_info['errors'].append(f'String conversion error: {str(e)}')
                        case_info['valid'] = False
                
                else:
                    case_info['errors'].append('Test case is not a dictionary')
                    case_info['valid'] = False
                
                response_data['test_cases_info']['cases'].append(case_info)
                
                if not case_info['valid']:
                    response_data['validation_errors'].extend(case_info['errors'])
        
        # Tentar serialização JSON
        try:
            json.dumps(challenge.test_cases, ensure_ascii=False)
            response_data['json_serializable'] = True
        except Exception as e:
            response_data['json_serializable'] = False
            response_data['json_error'] = str(e)
        
        # Verificar campos de texto
        text_fields = ['description', 'input_description', 'output_description', 'example_input', 'example_output']
        response_data['text_fields'] = {}
        
        for field in text_fields:
            value = getattr(challenge, field, None)
            field_info = {
                'has_value': value is not None and value != '',
                'length': len(value) if value else 0,
                'utf8_valid': True
            }
            
            if value:
                try:
                    value.encode('utf-8')
                except Exception as e:
                    field_info['utf8_valid'] = False
                    field_info['encoding_error'] = str(e)
                    response_data['encoding_issues'].append(f'{field}: {str(e)}')
            
            response_data['text_fields'][field] = field_info
        
        return JsonResponse(response_data)
        
    except Challenge.DoesNotExist:
        return JsonResponse({
            'error': f'Challenge {challenge_id} not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'error': f'Debug error: {str(e)}'
        }, status=500)
    
@csrf_exempt
def debug_environment(request):
    """Debug de ambiente para comparar local vs Render"""
    import sys
    import platform
    import subprocess
    import tempfile
    import os
    
    env_info = {
        'python_version': sys.version,
        'platform': platform.platform(),
        'architecture': platform.architecture(),
        'temp_dir': tempfile.gettempdir(),
        'java_available': False,
        'javac_available': False,
        'can_create_temp': False,
        'can_compile_java': False,
        'challenges_count': 0,
        'challenge_253_exists': False
    }
    
    # Verificar Java
    try:
        result = subprocess.run(['java', '-version'], 
                              capture_output=True, text=True, timeout=5)
        env_info['java_available'] = result.returncode == 0
        if result.returncode == 0:
            env_info['java_version'] = result.stderr.strip().split('\n')[0]
    except:
        pass
    
    # Verificar Javac
    try:
        result = subprocess.run(['javac', '-version'], 
                              capture_output=True, text=True, timeout=5)
        env_info['javac_available'] = result.returncode == 0
        if result.returncode == 0:
            env_info['javac_version'] = result.stderr.strip()
    except:
        pass
    
    # Verificar temp files
    try:
        temp_dir = tempfile.mkdtemp()
        env_info['can_create_temp'] = True
        env_info['temp_dir_writable'] = os.access(temp_dir, os.W_OK)
        
        # Tentar compilar Java
        test_file = os.path.join(temp_dir, "Test.java")
        with open(test_file, 'w') as f:
            f.write("public class Test { public static void main(String[] args) { System.out.println(\"test\"); } }")
        
        compile_result = subprocess.run(['javac', test_file], 
                                      capture_output=True, text=True, timeout=10)
        env_info['can_compile_java'] = compile_result.returncode == 0
        if compile_result.returncode != 0:
            env_info['compile_error'] = compile_result.stderr
        
        import shutil
        shutil.rmtree(temp_dir)
        
    except Exception as e:
        env_info['temp_error'] = str(e)
    
    # Verificar banco de dados
    try:
        from challenges.models import Challenge
        env_info['challenges_count'] = Challenge.objects.count()
        env_info['challenge_253_exists'] = Challenge.objects.filter(id=253).exists()
        
        if env_info['challenge_253_exists']:
            challenge = Challenge.objects.get(id=253)
            env_info['challenge_253_data'] = {
                'title': challenge.title,
                'language': challenge.language.name,
                'test_cases_count': len(challenge.test_cases),
                'test_cases_type': type(challenge.test_cases).__name__
            }
    except Exception as e:
        env_info['db_error'] = str(e)
    
    return JsonResponse(env_info)

@login_required
@csrf_exempt
def test_challenge_253(request):
    """Teste específico do challenge 253 no Render"""
    
    try:
        # Código Fibonacci simples
        fibonacci_code = '''public class Fibonacci {
    public static void main(String[] args) {
        java.util.Scanner scanner = new java.util.Scanner(System.in);
        int n = scanner.nextInt();
        
        if (n <= 0) {
            System.out.println("0");
            return;
        }
        if (n == 1 || n == 2) {
            System.out.println("1");
            return;
        }
        
        int a = 1, b = 1;
        for (int i = 3; i <= n; i++) {
            int temp = a + b;
            a = b;
            b = temp;
        }
        System.out.println(b);
    }
}'''
        
        # Buscar challenge
        challenge = Challenge.objects.get(id=253)
        
        # Criar submissão de teste
        submission = Submission.objects.create(
            challenge=challenge,
            user=request.user,
            code=fibonacci_code,
            language=challenge.language,
            status='pending'
        )
        
        # Avaliar
        from .java_executor import evaluate_java_submission
        result = evaluate_java_submission(submission)
        
        return JsonResponse({
            'success': True,
            'submission_id': submission.id,
            'result': result,
            'submission_status': submission.status,
            'execution_time': submission.execution_time,
            'error_message': submission.error_message
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        })
    