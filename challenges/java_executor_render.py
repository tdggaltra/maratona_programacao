# Java Executor Otimizado para Render (recursos limitados)

# java_executor_render.py - Versão otimizada para Render

import subprocess
import tempfile
import os
import time
import shutil
import uuid
import logging
import psutil  # Para monitorar recursos

logger = logging.getLogger(__name__)

class RenderJavaExecutor:
    """
    Executor Java otimizado para ambientes com recursos limitados (Render)
    """
    
    def __init__(self, time_limit=5000, memory_limit=64):
        # Limites mais conservadores para Render
        self.time_limit = min(time_limit / 1000, 10)  # Máximo 10 segundos
        self.memory_limit = min(memory_limit, 32)  # Máximo 32MB para Java
        self.compile_timeout = 8  # 8 segundos para compilação
        self.max_execution_time = min(self.time_limit, 8)  # Máximo 8 segundos execução
        self.temp_dir = None
        
        # Verificar recursos disponíveis
        try:
            memory = psutil.virtual_memory()
            available_mb = memory.available / (1024 * 1024)
            logger.info(f"[RENDER] Available memory: {available_mb:.1f}MB")
            
            # Se memória muito baixa, reduzir ainda mais
            if available_mb < 200:
                self.memory_limit = min(self.memory_limit, 16)
                self.compile_timeout = 5
                self.max_execution_time = 5
                logger.warning(f"[RENDER] Low memory detected, reducing limits")
        except:
            pass
    
    def create_temp_directory(self):
        """Cria diretório temporário com fallbacks"""
        try:
            # Tentar diferentes locais para temp
            for temp_base in ['/tmp', '/var/tmp', tempfile.gettempdir()]:
                try:
                    if os.path.exists(temp_base) and os.access(temp_base, os.W_OK):
                        unique_id = str(uuid.uuid4())[:8]
                        self.temp_dir = os.path.join(temp_base, f'java_exec_{unique_id}')
                        os.makedirs(self.temp_dir, exist_ok=True)
                        logger.debug(f"[RENDER] Temp dir created: {self.temp_dir}")
                        return self.temp_dir
                except Exception as e:
                    logger.warning(f"[RENDER] Failed to create temp in {temp_base}: {e}")
                    continue
            
            # Fallback para tempfile padrão
            self.temp_dir = tempfile.mkdtemp(prefix='java_exec_')
            logger.debug(f"[RENDER] Fallback temp dir: {self.temp_dir}")
            return self.temp_dir
            
        except Exception as e:
            logger.error(f"[RENDER] Critical: Cannot create temp directory: {e}")
            raise
    
    def cleanup_temp_directory(self):
        """Remove diretório temporário com retry"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            for attempt in range(3):  # 3 tentativas
                try:
                    shutil.rmtree(self.temp_dir, ignore_errors=True)
                    logger.debug(f"[RENDER] Temp dir cleaned: {self.temp_dir}")
                    break
                except Exception as e:
                    logger.warning(f"[RENDER] Cleanup attempt {attempt+1} failed: {e}")
                    time.sleep(0.1)
    
    def extract_class_name(self, java_code):
        """Extração robusta de nome de classe"""
        import re
        
        try:
            # Remove comentários
            code_clean = re.sub(r'//.*?\n|/\*.*?\*/', '', java_code, flags=re.DOTALL)
            
            # Procura classe pública primeiro
            match = re.search(r'public\s+class\s+(\w+)', code_clean, re.IGNORECASE)
            if match:
                return match.group(1)
            
            # Procura qualquer classe
            match = re.search(r'class\s+(\w+)', code_clean, re.IGNORECASE)
            if match:
                return match.group(1)
            
            logger.warning("[RENDER] No class name found, using default")
            return 'Solution'
            
        except Exception as e:
            logger.error(f"[RENDER] Error extracting class name: {e}")
            return 'Solution'
    
    def compile_java(self, java_file_path, class_name):
        """Compilação Java otimizada para Render"""
        try:
            logger.debug(f"[RENDER] Compiling: {java_file_path}")
            
            # Comando de compilação mais conservador
            compile_cmd = [
                'javac',
                '-J-Xmx32m',  # Limitar memória do compilador
                '-cp', '.',
                '-encoding', 'UTF-8',
                '-Xlint:none',  # Desabilitar warnings
                java_file_path
            ]
            
            start_time = time.time()
            
            # Usar processo mais controlado
            process = subprocess.Popen(
                compile_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=self.temp_dir,
                env=dict(os.environ, JAVA_TOOL_OPTIONS='-Xmx32m')
            )
            
            try:
                stdout, stderr = process.communicate(timeout=self.compile_timeout)
                compile_time = time.time() - start_time
                
                logger.debug(f"[RENDER] Compilation took {compile_time:.2f}s")
                
                if process.returncode != 0:
                    error_msg = stderr.decode('utf-8', errors='ignore').strip()
                    error_msg = error_msg[:500]  # Limitar tamanho do erro
                    logger.warning(f"[RENDER] Compilation failed: {error_msg}")
                    
                    return {
                        'success': False,
                        'error': 'compilation_error',
                        'message': error_msg or 'Erro de compilação desconhecido'
                    }
                
                # Verificar se .class foi criado
                class_file = os.path.join(self.temp_dir, f'{class_name}.class')
                if not os.path.exists(class_file):
                    return {
                        'success': False,
                        'error': 'compilation_error',
                        'message': 'Arquivo .class não foi gerado'
                    }
                
                logger.debug("[RENDER] Compilation successful")
                return {'success': True}
                
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=2)
                logger.warning(f"[RENDER] Compilation timeout ({self.compile_timeout}s)")
                
                return {
                    'success': False,
                    'error': 'compilation_timeout',
                    'message': f'Compilação excedeu {self.compile_timeout}s'
                }
                
        except FileNotFoundError:
            logger.error("[RENDER] javac not found")
            return {
                'success': False,
                'error': 'compilation_error',
                'message': 'Compilador Java não encontrado no servidor'
            }
        except Exception as e:
            logger.error(f"[RENDER] Compilation error: {e}")
            return {
                'success': False,
                'error': 'compilation_error',
                'message': f'Erro na compilação: {str(e)}'
            }
    
    def execute_java(self, class_name, test_input=""):
        """Execução Java otimizada"""
        try:
            logger.debug(f"[RENDER] Executing: {class_name}")
            
            # Comando de execução muito conservador
            exec_cmd = [
                'java',
                '-Xmx16m',  # Memória muito limitada
                '-Xms8m',   # Memória inicial pequena
                '-XX:+UseSerialGC',  # GC mais simples
                '-XX:MaxHeapFreeRatio=10',
                '-XX:MinHeapFreeRatio=5',
                '-Dfile.encoding=UTF-8',
                '-cp', '.',
                class_name
            ]
            
            start_time = time.time()
            
            process = subprocess.Popen(
                exec_cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=self.temp_dir,
                env=dict(os.environ, JAVA_TOOL_OPTIONS='-Xmx16m')
            )
            
            try:
                stdout, stderr = process.communicate(
                    input=test_input.encode('utf-8'),
                    timeout=self.max_execution_time
                )
                
                execution_time = (time.time() - start_time) * 1000
                logger.debug(f"[RENDER] Execution took {execution_time:.1f}ms")
                
                if process.returncode != 0:
                    error_msg = stderr.decode('utf-8', errors='ignore').strip()
                    error_msg = error_msg[:300]  # Limitar erro
                    logger.warning(f"[RENDER] Execution failed: {error_msg}")
                    
                    return {
                        'success': False,
                        'error': 'runtime_error',
                        'message': error_msg or 'Erro de execução',
                        'execution_time': execution_time
                    }
                
                output = stdout.decode('utf-8', errors='ignore')
                return {
                    'success': True,
                    'output': output,
                    'execution_time': execution_time
                }
                
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=2)
                logger.warning(f"[RENDER] Execution timeout ({self.max_execution_time}s)")
                
                return {
                    'success': False,
                    'error': 'time_limit_exceeded',
                    'message': f'Execução excedeu {self.max_execution_time}s',
                    'execution_time': self.max_execution_time * 1000
                }
                
        except Exception as e:
            logger.error(f"[RENDER] Execution error: {e}")
            return {
                'success': False,
                'error': 'execution_error',
                'message': f'Erro na execução: {str(e)}',
                'execution_time': 0
            }
    
    def run_test_case(self, java_code, test_input, expected_output):
        """Executa caso de teste com monitoramento de recursos"""
        try:
            # Monitorar memória antes
            try:
                memory_before = psutil.virtual_memory().available / (1024 * 1024)
                logger.debug(f"[RENDER] Memory before test: {memory_before:.1f}MB")
            except:
                pass
            
            class_name = self.extract_class_name(java_code)
            logger.debug(f"[RENDER] Class name: {class_name}")
            
            # Criar arquivo Java
            java_file = os.path.join(self.temp_dir, f'{class_name}.java')
            with open(java_file, 'w', encoding='utf-8') as f:
                f.write(java_code)
            
            # Compilar
            compile_result = self.compile_java(java_file, class_name)
            if not compile_result['success']:
                return compile_result
            
            # Executar
            exec_result = self.execute_java(class_name, test_input)
            if not exec_result['success']:
                return exec_result
            
            # Comparar resultado
            actual_output = exec_result['output'].strip()
            expected_output = expected_output.strip()
            
            if actual_output == expected_output:
                logger.debug("[RENDER] Test case passed")
                return {
                    'success': True,
                    'status': 'passed',
                    'execution_time': exec_result['execution_time'],
                    'actual_output': actual_output,
                    'expected_output': expected_output
                }
            else:
                logger.debug(f"[RENDER] Test case failed - Expected: {repr(expected_output)}, Got: {repr(actual_output)}")
                return {
                    'success': False,
                    'error': 'wrong_answer',
                    'message': 'Saída incorreta',
                    'execution_time': exec_result['execution_time'],
                    'actual_output': actual_output,
                    'expected_output': expected_output
                }
                
        except Exception as e:
            logger.error(f"[RENDER] Test case error: {e}")
            return {
                'success': False,
                'error': 'test_error',
                'message': f'Erro no teste: {str(e)}',
                'execution_time': 0
            }
    
    def evaluate_submission(self, java_code, test_cases):
        """Avalia submissão com limpeza de recursos"""
        try:
            logger.info(f"[RENDER] Starting evaluation - {len(test_cases)} test cases")
            self.create_temp_directory()
            
            results = []
            total_time = 0
            
            for i, test_case in enumerate(test_cases):
                logger.debug(f"[RENDER] Running test case {i+1}/{len(test_cases)}")
                
                test_input = str(test_case.get('input', ''))
                expected_output = str(test_case.get('output', ''))
                
                result = self.run_test_case(java_code, test_input, expected_output)
                results.append({
                    'test_case': i + 1,
                    'result': result
                })
                
                if result['success']:
                    total_time += result.get('execution_time', 0)
                else:
                    logger.info(f"[RENDER] Test case {i+1} failed: {result['error']}")
                    return {
                        'status': result['error'],
                        'message': result['message'],
                        'execution_time': total_time,
                        'test_results': results,
                        'passed_tests': i,
                        'total_tests': len(test_cases),
                        'failed_test_case': i + 1
                    }
                
                # Limpeza entre testes para economizar recursos
                if i < len(test_cases) - 1:  # Não no último teste
                    time.sleep(0.1)  # Pequena pausa
            
            logger.info(f"[RENDER] All {len(test_cases)} tests passed")
            return {
                'status': 'accepted',
                'message': 'Todos os testes passaram',
                'execution_time': total_time,
                'test_results': results,
                'passed_tests': len(test_cases),
                'total_tests': len(test_cases)
            }
            
        except Exception as e:
            logger.error(f"[RENDER] Evaluation error: {e}")
            return {
                'status': 'evaluation_error',
                'message': f'Erro na avaliação: {str(e)}',
                'execution_time': 0,
                'test_results': [],
                'passed_tests': 0,
                'total_tests': len(test_cases)
            }
        finally:
            self.cleanup_temp_directory()


# FUNÇÃO PARA USAR NO RENDER
def evaluate_java_submission_render(submission):
    """
    Função otimizada para Render - SUBSTITUA evaluate_java_submission por esta
    """
    try:
        challenge = submission.challenge
        
        # Verificações básicas
        if not submission.code.strip():
            return {'status': 'compilation_error', 'message': 'Código vazio'}
        
        if not challenge.test_cases:
            return {'status': 'runtime_error', 'message': 'Nenhum caso de teste'}
        
        # Criar executor otimizado para Render
        executor = RenderJavaExecutor(
            time_limit=min(challenge.time_limit, 8000),  # Máximo 8 segundos
            memory_limit=32  # 32MB máximo
        )
        
        logger.info(f"[RENDER] Evaluating submission {submission.id}")
        
        # Avaliar
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
            submission.error_message += f" (Teste {result['failed_test_case']})"
        
        submission.save()
        
        logger.info(f"[RENDER] Evaluation completed: {submission.status}")
        return result
        
    except Exception as e:
        logger.error(f"[RENDER] Critical evaluation error: {e}")
        submission.status = 'runtime_error'
        submission.error_message = f'Erro crítico: {str(e)}'
        submission.save()
        
        return {
            'status': 'runtime_error',
            'message': f'Erro crítico: {str(e)}'
        }

# PARA USAR NO SEU VIEWS.PY:
"""
# No evaluate_submission_safe, substitua a linha:
if language.name.lower() == 'java':
    return evaluate_java_submission(submission)

# Por:
if language.name.lower() == 'java':
    return evaluate_java_submission_render(submission)
"""