# challenges/java_executor.py

import subprocess
import tempfile
import os
import time
import threading
import signal
from pathlib import Path
import shutil
import uuid
import re
import logging

# Configurar logging
logger = logging.getLogger(__name__)

class JavaCodeExecutor:
    """
    Executor de código Java seguro para o sistema de quiz
    """
    
    def __init__(self, time_limit=5000, memory_limit=128):
        self.time_limit = time_limit / 1000  # Converte para segundos
        self.memory_limit = memory_limit  # MB
        self.temp_dir = None
        self.compile_timeout = 15  # 15 segundos para compilação
        self.max_execution_time = min(max(self.time_limit, 5), 30)  # Entre 5-30 segundos
        
    def create_temp_directory(self):
        """Cria diretório temporário para execução"""
        try:
            # Usar UUID para evitar conflitos
            unique_id = str(uuid.uuid4())[:8]
            self.temp_dir = tempfile.mkdtemp(prefix=f'java_exec_{unique_id}_')
            logger.debug(f"Diretório temporário criado: {self.temp_dir}")
            return self.temp_dir
        except Exception as e:
            logger.error(f"Erro ao criar diretório temporário: {e}")
            raise
    
    def cleanup_temp_directory(self):
        """Remove diretório temporário"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir, ignore_errors=True)
                logger.debug(f"Diretório temporário removido: {self.temp_dir}")
            except Exception as e:
                logger.warning(f"Erro ao remover diretório temporário: {e}")
    
    def extract_class_name(self, java_code):
        """
        Extrai o nome da classe principal do código Java usando regex
        CORREÇÃO: Melhor detecção de nome de classe
        """
        try:
            # Remove comentários para evitar falsos positivos
            code_without_comments = re.sub(r'//.*?\n|/\*.*?\*/', '', java_code, flags=re.DOTALL)
            
            # Procura por classe pública primeiro
            public_class_match = re.search(r'public\s+class\s+(\w+)', code_without_comments, re.IGNORECASE)
            if public_class_match:
                return public_class_match.group(1)
            
            # Procura por qualquer classe
            class_match = re.search(r'class\s+(\w+)', code_without_comments, re.IGNORECASE)
            if class_match:
                return class_match.group(1)
            
            # Nome padrão se não encontrar
            logger.warning("Nome de classe não encontrado, usando 'Main'")
            return 'Main'
            
        except Exception as e:
            logger.error(f"Erro ao extrair nome da classe: {e}")
            return 'Main'
    
    def create_java_file(self, code, class_name):
        """
        Cria arquivo .java com o código
        CORREÇÃO: Melhor validação e encoding
        """
        try:
            if not self.temp_dir:
                self.create_temp_directory()
            
            # Validar nome da classe
            if not re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', class_name):
                raise ValueError(f"Nome de classe inválido: {class_name}")
                
            java_file_path = os.path.join(self.temp_dir, f'{class_name}.java')
            
            # Escrever arquivo com encoding correto
            with open(java_file_path, 'w', encoding='utf-8') as f:
                f.write(code)
            
            logger.debug(f"Arquivo Java criado: {java_file_path}")
            return java_file_path
            
        except Exception as e:
            logger.error(f"Erro ao criar arquivo Java: {e}")
            raise
    
    def compile_java(self, java_file_path, class_name):
        """
        Compila o código Java
        CORREÇÃO: Timeout mais agressivo e melhor tratamento de erros
        """
        try:
            logger.debug(f"Iniciando compilação: {java_file_path}")
            
            # Comando de compilação simplificado
            compile_cmd = [
                'javac',
                '-cp', '.',  # Classpath atual
                '-encoding', 'UTF-8',  # Encoding explícito
                java_file_path
            ]
            
            # CORREÇÃO: Timeout mais baixo e processo mais controlado
            start_time = time.time()
            
            result = subprocess.run(
                compile_cmd,
                capture_output=True,
                text=True,
                timeout=self.compile_timeout,  # 15 segundos máximo
                cwd=self.temp_dir,
                env=os.environ.copy()  # Herdar environment
            )
            
            compile_time = time.time() - start_time
            logger.debug(f"Compilação concluída em {compile_time:.2f}s")
            
            if result.returncode != 0:
                error_msg = result.stderr.strip() if result.stderr else 'Erro de compilação desconhecido'
                logger.warning(f"Erro de compilação: {error_msg}")
                return {
                    'success': False,
                    'error': 'compilation_error',
                    'message': error_msg
                }
            
            # Verifica se o arquivo .class foi criado
            class_file = os.path.join(self.temp_dir, f'{class_name}.class')
            if not os.path.exists(class_file):
                logger.error("Arquivo .class não foi gerado")
                return {
                    'success': False,
                    'error': 'compilation_error',
                    'message': 'Arquivo .class não foi gerado'
                }
            
            logger.debug("Compilação bem-sucedida")
            return {'success': True}
            
        except subprocess.TimeoutExpired:
            logger.warning(f"Timeout na compilação após {self.compile_timeout}s")
            return {
                'success': False,
                'error': 'compilation_timeout',
                'message': f'Tempo limite de compilação excedido ({self.compile_timeout}s)'
            }
        except FileNotFoundError:
            logger.error("Comando javac não encontrado")
            return {
                'success': False,
                'error': 'compilation_error',
                'message': 'Compilador Java não encontrado no sistema'
            }
        except Exception as e:
            logger.error(f"Erro inesperado na compilação: {e}")
            return {
                'success': False,
                'error': 'compilation_error',  
                'message': f'Erro na compilação: {str(e)}'
            }
    
    def execute_java(self, class_name, test_input=""):
        """
        Executa o código Java compilado
        CORREÇÃO: Melhor controle de processo e timeout
        """
        try:
            logger.debug(f"Iniciando execução: {class_name}")
            
            # Comando de execução
            exec_cmd = [
                'java',
                '-cp', '.',  # Classpath simplificado
                f'-Xmx{self.memory_limit}m',  # Limite de memória
                '-Xms16m',  # Memória inicial baixa
                '-XX:+UseSerialGC',  # GC mais rápido para execução curta
                '-Dfile.encoding=UTF-8',  # Encoding
                class_name
            ]
            
            start_time = time.time()
            
            # CORREÇÃO: Usar context manager para melhor controle do processo
            with subprocess.Popen(
                exec_cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=self.temp_dir,
                env=os.environ.copy()
            ) as process:
                
                try:
                    stdout, stderr = process.communicate(
                        input=test_input,
                        timeout=self.max_execution_time
                    )
                    
                    execution_time = (time.time() - start_time) * 1000  # ms
                    logger.debug(f"Execução concluída em {execution_time:.2f}ms")
                    
                    if process.returncode != 0:
                        error_msg = stderr.strip() if stderr else 'Erro de execução'
                        logger.warning(f"Erro de execução: {error_msg}")
                        return {
                            'success': False,
                            'error': 'runtime_error',
                            'message': error_msg,
                            'execution_time': execution_time
                        }
                    
                    return {
                        'success': True,
                        'output': stdout,
                        'execution_time': execution_time
                    }
                    
                except subprocess.TimeoutExpired:
                    logger.warning(f"Timeout na execução após {self.max_execution_time}s")
                    process.kill()
                    process.wait(timeout=5)  # Aguarda processo morrer
                    return {
                        'success': False,
                        'error': 'time_limit_exceeded',
                        'message': f'Tempo limite excedido ({self.max_execution_time}s)',
                        'execution_time': self.max_execution_time * 1000
                    }
                    
        except FileNotFoundError:
            logger.error("Comando java não encontrado")
            return {
                'success': False,
                'error': 'execution_error',
                'message': 'Java Runtime não encontrado no sistema',
                'execution_time': 0
            }
        except Exception as e:
            logger.error(f"Erro inesperado na execução: {e}")
            return {
                'success': False,
                'error': 'execution_error',
                'message': f'Erro na execução: {str(e)}',
                'execution_time': 0
            }
    
    def run_test_case(self, java_code, test_input, expected_output):
        """
        Executa um caso de teste específico
        CORREÇÃO: Melhor logging e tratamento de erro
        """
        try:
            logger.debug(f"Executando caso de teste com input: {repr(test_input[:50])}...")
            
            # Extrai nome da classe
            class_name = self.extract_class_name(java_code)
            logger.debug(f"Nome da classe detectado: {class_name}")
            
            # Cria arquivo Java
            java_file = self.create_java_file(java_code, class_name)
            
            # Compila
            compile_result = self.compile_java(java_file, class_name)
            if not compile_result['success']:
                return compile_result
            
            # Executa
            exec_result = self.execute_java(class_name, test_input)
            if not exec_result['success']:
                return exec_result
            
            # Compara saída (normalizada)
            actual_output = exec_result['output'].strip()
            expected_output = expected_output.strip()
            
            # CORREÇÃO: Comparação mais robusta
            if actual_output == expected_output:
                logger.debug("Caso de teste passou")
                return {
                    'success': True,
                    'status': 'passed',
                    'execution_time': exec_result['execution_time'],
                    'actual_output': actual_output,
                    'expected_output': expected_output
                }
            else:
                logger.debug(f"Caso de teste falhou. Esperado: {repr(expected_output)}, Atual: {repr(actual_output)}")
                return {
                    'success': False,
                    'error': 'wrong_answer',
                    'message': 'Saída não corresponde ao esperado',
                    'execution_time': exec_result['execution_time'],
                    'actual_output': actual_output,
                    'expected_output': expected_output
                }
                
        except Exception as e:
            logger.error(f"Erro no caso de teste: {e}")
            return {
                'success': False,
                'error': 'test_error',
                'message': f'Erro no teste: {str(e)}',
                'execution_time': 0
            }
    
    def evaluate_submission(self, java_code, test_cases):
        """
        Avalia uma submissão completa com múltiplos casos de teste
        CORREÇÃO: Melhor controle de recursos e cleanup
        """
        try:
            logger.info(f"Iniciando avaliação com {len(test_cases)} casos de teste")
            self.create_temp_directory()
            
            results = []
            total_time = 0
            
            for i, test_case in enumerate(test_cases):
                logger.debug(f"Executando caso de teste {i+1}/{len(test_cases)}")
                
                test_input = test_case.get('input', '')
                expected_output = test_case.get('output', '')
                
                result = self.run_test_case(java_code, test_input, expected_output)
                results.append({
                    'test_case': i + 1,
                    'result': result
                })
                
                if result['success']:
                    total_time += result.get('execution_time', 0)
                else:
                    # CORREÇÃO: Retornar resultado mais detalhado mesmo em falha
                    logger.info(f"Falha no caso de teste {i+1}: {result['error']}")
                    return {
                        'status': result['error'],
                        'message': result['message'],
                        'execution_time': total_time,
                        'test_results': results,
                        'passed_tests': i,
                        'total_tests': len(test_cases),
                        'failed_test_case': i + 1
                    }
            
            # Todos os testes passaram
            logger.info(f"Todos os {len(test_cases)} casos de teste passaram")
            return {
                'status': 'accepted',
                'message': 'Todos os testes passaram',
                'execution_time': total_time,
                'test_results': results,
                'passed_tests': len(test_cases),
                'total_tests': len(test_cases)
            }
            
        except Exception as e:
            logger.error(f"Erro na avaliação: {e}")
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


def evaluate_java_submission(submission):
    """
    Função principal para avaliar submissões Java
    CORREÇÃO: Melhor validação e tratamento de erros
    """
    try:
        challenge = submission.challenge
        
        # Verifica se é código Java
        if submission.language.name.lower() != 'java':
            logger.error(f"Linguagem incorreta: {submission.language.name}")
            return {
                'status': 'language_error',
                'message': 'Esta função é apenas para código Java'
            }
        
        # CORREÇÃO: Validações adicionais
        if not submission.code.strip():
            return {
                'status': 'compilation_error',
                'message': 'Código vazio'
            }
        
        if not challenge.test_cases:
            return {
                'status': 'evaluation_error',
                'message': 'Nenhum caso de teste encontrado'
            }
        
        # Cria executor
        executor = JavaCodeExecutor(
            time_limit=challenge.time_limit,
            memory_limit=128
        )
        
        logger.info(f"Avaliando submissão {submission.id} para desafio {challenge.title}")
        
        # Avalia submissão
        result = executor.evaluate_submission(
            submission.code,
            challenge.test_cases
        )
        
        # CORREÇÃO: Mapeamento mais completo de status
        status_mapping = {
            'accepted': 'accepted',
            'compilation_error': 'compilation_error',
            'compilation_timeout': 'compilation_error',
            'runtime_error': 'runtime_error',
            'time_limit_exceeded': 'time_limit',
            'wrong_answer': 'wrong_answer',
            'evaluation_error': 'runtime_error',
            'language_error': 'runtime_error',
            'test_error': 'runtime_error'
        }
        
        submission.status = status_mapping.get(result['status'], 'runtime_error')
        submission.execution_time = result.get('execution_time', 0)
        submission.error_message = result.get('message', '')
        
        # CORREÇÃO: Salvar informações adicionais se necessário
        if result.get('failed_test_case'):
            submission.error_message += f" (Falha no caso de teste {result['failed_test_case']})"
        
        submission.save()
        
        logger.info(f"Submissão {submission.id} avaliada: {submission.status}")
        return result
        
    except Exception as e:
        logger.error(f"Erro crítico na avaliação da submissão {submission.id}: {e}")
        submission.status = 'runtime_error'
        submission.error_message = f'Erro interno: {str(e)}'
        submission.save()
        
        return {
            'status': 'evaluation_error',
            'message': f'Erro crítico: {str(e)}'
        }


# CORREÇÃO: Função de teste para validar o executor
def test_java_executor():
    """Função para testar o executor Java"""
    test_code = '''
public class Test {
    public static void main(String[] args) {
        System.out.println("Hello World");
    }
}
'''
    
    test_cases = [
        {'input': '', 'output': 'Hello World'}
    ]
    
    executor = JavaCodeExecutor()
    try:
        result = executor.evaluate_submission(test_code, test_cases)
        print(f"Teste resultado: {result}")
        return result['status'] == 'accepted'
    except Exception as e:
        print(f"Erro no teste: {e}")
        return False


# Exemplo de uso no views.py:
"""
# No seu views.py, substitua a função evaluate_submission por:

from .java_executor import evaluate_java_submission
import logging

logger = logging.getLogger(__name__)

def evaluate_submission(submission):
    try:
        if submission.language.name.lower() == 'java':
            return evaluate_java_submission(submission)
        else:
            # Mantém a lógica existente para outras linguagens
            # ... seu código atual ...
            pass
    except Exception as e:
        logger.error(f"Erro na avaliação da submissão {submission.id}: {e}")
        submission.status = 'runtime_error'
        submission.error_message = 'Erro interno do sistema'
        submission.save()
        raise
"""