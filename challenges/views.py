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

@login_required
@csrf_exempt  # CORREÇÃO: Adicionar csrf_exempt para AJAX
@require_POST  
def submit_solution_ajax(request, pk):
    """
    View AJAX corrigida com validação robusta
    CORREÇÃO PRINCIPAL: Melhor validação de dados e tratamento de erros
    """
    
    def create_error_response(message, status=400, details=None):
        """Helper para criar respostas de erro consistentes"""
        response_data = {
            'success': False,
            'error': message
        }
        if details:
            response_data['details'] = details
        return JsonResponse(response_data, status=status)
    
    try:
        logger.info(f"[SUBMIT] Starting AJAX submit for challenge {pk} by user {request.user.username}")
        
        # 1. VALIDAÇÃO BÁSICA DA REQUISIÇÃO
        if request.content_type != 'application/json':
            logger.error(f"[SUBMIT] Invalid content type: {request.content_type}")
            return create_error_response(
                "Content-Type deve ser application/json",
                details={'received_content_type': request.content_type}
            )
        
        # 2. VALIDAÇÃO DO CHALLENGE
        try:
            challenge = Challenge.objects.get(pk=pk)
            logger.info(f"[SUBMIT] Challenge found: {challenge.title}")
        except Challenge.DoesNotExist:
            logger.error(f"[SUBMIT] Challenge {pk} not found")
            return create_error_response(f"Desafio {pk} não encontrado", status=404)
        
        # 3. VALIDAÇÃO E PARSE DO JSON
        try:
            if not request.body:
                logger.error("[SUBMIT] Empty request body")
                return create_error_response("Request body vazio")
            
            # Log do body para debug (apenas primeiros 200 chars)
            body_preview = request.body.decode('utf-8')[:200]
            logger.debug(f"[SUBMIT] Body preview: {body_preview}")
            
            data = json.loads(request.body)
            logger.debug(f"[SUBMIT] JSON parsed successfully: {list(data.keys())}")
            
        except UnicodeDecodeError as e:
            logger.error(f"[SUBMIT] Unicode decode error: {e}")
            return create_error_response("Erro de encoding no request body")
        except json.JSONDecodeError as e:
            logger.error(f"[SUBMIT] JSON decode error: {e}")
            return create_error_response(
                "JSON inválido",
                details={'json_error': str(e)}
            )
        
        # 4. VALIDAÇÃO DOS CAMPOS OBRIGATÓRIOS
        if not isinstance(data, dict):
            logger.error(f"[SUBMIT] Data is not a dict: {type(data)}")
            return create_error_response("Dados devem ser um objeto JSON")
        
        # CORREÇÃO: Validação rigorosa do código
        code = data.get('code')
        if code is None:
            logger.error("[SUBMIT] Missing 'code' field")
            return create_error_response("Campo 'code' é obrigatório")
        
        if not isinstance(code, str):
            logger.error(f"[SUBMIT] Code is not string: {type(code)}")
            return create_error_response("Campo 'code' deve ser uma string")
        
        # CORREÇÃO: Validação mais robusta do código
        code = code.strip()
        if not code:
            logger.error("[SUBMIT] Empty code after strip")
            return create_error_response("Código não pode estar vazio")
        
        # CORREÇÃO: Validação de tamanho do código
        if len(code) > 50000:  # 50KB limite
            logger.error(f"[SUBMIT] Code too long: {len(code)} chars")
            return create_error_response("Código muito longo (máximo 50KB)")
        
        # CORREÇÃO: Validação de caracteres problemáticos
        try:
            # Tenta encode/decode para verificar se há caracteres problemáticos
            code.encode('utf-8').decode('utf-8')
        except UnicodeError as e:
            logger.error(f"[SUBMIT] Unicode error in code: {e}")
            return create_error_response("Código contém caracteres inválidos")
        
        logger.info(f"[SUBMIT] Code validated - Length: {len(code)} chars")
        
        # 5. VALIDAÇÃO DE ACESSO AO CHALLENGE
        try:
            profile = UserProfile.objects.get(user=request.user)
        except UserProfile.DoesNotExist:
            logger.info("[SUBMIT] Creating new profile for user")
            initial_state = BrazilState.objects.filter(order=1).first()
            profile = UserProfile.objects.create(
                user=request.user,
                current_state=initial_state
            )
        
        if challenge.state.order > profile.current_state.order:
            logger.warning(f"[SUBMIT] User trying to access locked challenge: {challenge.state.order} > {profile.current_state.order}")
            return create_error_response(
                "Você precisa completar os desafios anteriores primeiro!",
                status=403
            )
        
        # 6. CRIAR SUBMISSÃO COM VALIDAÇÃO
        try:
            logger.info("[SUBMIT] Creating submission...")
            
            submission = Submission(
                challenge=challenge,
                user=request.user,
                code=code,
                language=challenge.language,
                status='pending'
            )
            
            # CORREÇÃO: Validar modelo antes de salvar
            try:
                submission.full_clean()
            except ValidationError as e:
                logger.error(f"[SUBMIT] Validation error: {e}")
                return create_error_response(
                    "Dados da submissão inválidos",
                    details={'validation_errors': e.message_dict}
                )
            
            submission.save()
            logger.info(f"[SUBMIT] Submission created: {submission.id}")
            
        except Exception as e:
            logger.error(f"[SUBMIT] Error creating submission: {e}")
            logger.error(f"[SUBMIT] Traceback: {traceback.format_exc()}")
            return create_error_response(
                "Erro ao criar submissão",
                details={'error': str(e)}
            )
        
        # 7. AVALIAR SUBMISSÃO COM TIMEOUT
        try:
            logger.info("[SUBMIT] Starting evaluation...")
            
            # CORREÇÃO: Timeout para avaliação
            import signal
            
            def timeout_handler(signum, frame):
                raise TimeoutError("Evaluation timeout")
            
            # Configurar timeout de 60 segundos para avaliação
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(60)
            
            try:
                result = evaluate_submission(submission)
                logger.info(f"[SUBMIT] Evaluation completed: {result.get('status')}")
            finally:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
                
        except TimeoutError:
            logger.error("[SUBMIT] Evaluation timeout")
            submission.status = 'runtime_error'
            submission.error_message = 'Timeout na avaliação'
            submission.save()
            return create_error_response("Timeout na avaliação do código")
            
        except Exception as e:
            logger.error(f"[SUBMIT] Error in evaluation: {e}")
            logger.error(f"[SUBMIT] Traceback: {traceback.format_exc()}")
            submission.status = 'runtime_error'
            submission.error_message = f'Erro na avaliação: {str(e)}'
            submission.save()
            return create_error_response(
                "Erro na avaliação do código",
                details={'error': str(e)}
            )
        
        # 8. PROCESSAR RESULTADO
        if result.get('status') == 'accepted':
            try:
                logger.info("[SUBMIT] Processing accepted result...")
                
                # Verificar se já completou
                already_completed = profile.completed_challenges.filter(id=challenge.id).exists()
                
                response_data = {
                    'success': True,
                    'status': 'accepted',
                    'submission_id': submission.id,
                    'execution_time': submission.execution_time,
                }
                
                if not already_completed:
                    # Adicionar pontos
                    profile.completed_challenges.add(challenge)
                    profile.total_points += challenge.points
                    profile.save()
                    
                    # Tentar desbloquear próximo estado
                    try:
                        next_unlocked = profile.unlock_next_state()
                    except Exception as e:
                        logger.warning(f"[SUBMIT] Error unlocking next state: {e}")
                        next_unlocked = False
                    
                    # Verificar conclusão total
                    total_challenges = Challenge.objects.count()
                    completed_challenges = profile.completed_challenges.count()
                    all_completed = (completed_challenges >= total_challenges)
                    
                    response_data.update({
                        'message': 'Parabéns! Solução aceita!',
                        'points_earned': challenge.points,
                        'next_unlocked': next_unlocked,
                        'all_completed': all_completed,
                        'total_points': profile.total_points,
                        'completed_count': completed_challenges,
                        'total_count': total_challenges,
                    })
                else:
                    response_data.update({
                        'message': 'Solução aceita! (já completado anteriormente)',
                        'points_earned': 0,
                        'next_unlocked': False,
                        'all_completed': False,
                    })
                
                logger.info(f"[SUBMIT] Success response prepared: {response_data['message']}")
                return JsonResponse(response_data)
                
            except Exception as e:
                logger.error(f"[SUBMIT] Error processing accepted result: {e}")
                logger.error(f"[SUBMIT] Traceback: {traceback.format_exc()}")
                return create_error_response(
                    "Erro ao processar resultado aceito",
                    details={'error': str(e)}
                )
        else:
            # Resultado não aceito
            logger.info(f"[SUBMIT] Non-accepted result: {result.get('status')}")
            return JsonResponse({
                'success': True,
                'status': result.get('status', 'unknown'),
                'message': result.get('message', 'Erro na execução'),
                'submission_id': submission.id,
                'execution_time': submission.execution_time,
                'error_details': result.get('error_details'),
            })
            
    except Exception as e:
        logger.error(f"[SUBMIT] Critical error: {e}")
        logger.error(f"[SUBMIT] Full traceback: {traceback.format_exc()}")
        return create_error_response(
            "Erro interno do servidor",
            status=500,
            details={'error': str(e)}
        )

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
            return evaluate_java_submission(submission)
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

@login_required
def leaderboard(request):
    """Exibe ranking dos usuários"""
    try:
        profiles = UserProfile.objects.select_related('user').order_by('-total_points')[:50]
        
        # Encontra posição do usuário atual
        user_position = None
        user_profile = request.user.userprofile
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