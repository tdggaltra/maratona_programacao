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

class JavaCodeExecutor:
    """
    Executor de código Java seguro para o sistema de quiz
    """
    
    def __init__(self, time_limit=5000, memory_limit=128):
        self.time_limit = time_limit / 1000  # Converte para segundos
        self.memory_limit = memory_limit  # MB
        self.temp_dir = None
        
    def create_temp_directory(self):
        """Cria diretório temporário para execução"""
        self.temp_dir = tempfile.mkdtemp(prefix='java_exec_')
        return self.temp_dir
    
    def cleanup_temp_directory(self):
        """Remove diretório temporário"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def extract_class_name(self, java_code):
        """
        Extrai o nome da classe principal do código Java
        """
        lines = java_code.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('public class '):
                # Extrai o nome da classe
                parts = line.split()
                if len(parts) >= 3:
                    class_name = parts[2].replace('{', '').strip()
                    return class_name
        
        # Se não encontrar classe pública, procura por qualquer classe
        for line in lines:
            line = line.strip()
            if line.startswith('class ') and not line.startswith('//'):
                parts = line.split()
                if len(parts) >= 2:
                    class_name = parts[1].replace('{', '').strip()
                    return class_name
        
        # Nome padrão se não encontrar
        return 'Main'
    
    def create_java_file(self, code, class_name):
        """Cria arquivo .java com o código"""
        if not self.temp_dir:
            self.create_temp_directory()
            
        java_file_path = os.path.join(self.temp_dir, f'{class_name}.java')
        
        with open(java_file_path, 'w', encoding='utf-8') as f:
            f.write(code)
            
        return java_file_path
    
    def compile_java(self, java_file_path, class_name):
        """
        Compila o código Java
        """
        try:
            # Comando de compilação
            compile_cmd = [
                'javac',
                '-cp', self.temp_dir,
                '-d', self.temp_dir,
                java_file_path
            ]
            
            # Execute a compilação
            result = subprocess.run(
                compile_cmd,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=self.temp_dir
            )
            
            if result.returncode != 0:
                return {
                    'success': False,
                    'error': 'compilation_error',
                    'message': result.stderr or 'Erro de compilação desconhecido'
                }
            
            # Verifica se o arquivo .class foi criado
            class_file = os.path.join(self.temp_dir, f'{class_name}.class')
            if not os.path.exists(class_file):
                return {
                    'success': False,
                    'error': 'compilation_error',
                    'message': 'Arquivo .class não foi gerado'
                }
            
            return {'success': True}
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'compilation_timeout',
                'message': 'Tempo limite de compilação excedido'
            }
        except Exception as e:
            return {
                'success': False,
                'error': 'compilation_error',  
                'message': f'Erro na compilação: {str(e)}'
            }
    
    def execute_java(self, class_name, test_input=""):
        """
        Executa o código Java compilado
        """
        try:
            # Comando de execução
            exec_cmd = [
                'java',
                '-cp', self.temp_dir,
                '-Xmx{}m'.format(self.memory_limit),  # Limite de memória
                class_name
            ]
            
            # Executa o programa
            start_time = time.time()
            
            process = subprocess.Popen(
                exec_cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=self.temp_dir
            )
            
            try:
                stdout, stderr = process.communicate(
                    input=test_input,
                    timeout=max(self.time_limit, 10)
                )
                execution_time = (time.time() - start_time) * 1000  # ms
                
                if process.returncode != 0:
                    return {
                        'success': False,
                        'error': 'runtime_error',
                        'message': stderr or 'Erro de execução',
                        'execution_time': execution_time
                    }
                
                return {
                    'success': True,
                    'output': stdout,
                    'execution_time': execution_time
                }
                
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
                return {
                    'success': False,
                    'error': 'time_limit_exceeded',
                    'message': f'Tempo limite excedido ({self.time_limit}s)',
                    'execution_time': self.time_limit * 1000
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': 'execution_error',
                'message': f'Erro na execução: {str(e)}',
                'execution_time': 0
            }
    
    def run_test_case(self, java_code, test_input, expected_output):
        """
        Executa um caso de teste específico
        """
        try:
            # Extrai nome da classe
            class_name = self.extract_class_name(java_code)
            
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
            
            # Compara saída
            actual_output = exec_result['output'].strip()
            expected_output = expected_output.strip()
            
            if actual_output == expected_output:
                return {
                    'success': True,
                    'status': 'passed',
                    'execution_time': exec_result['execution_time'],
                    'actual_output': actual_output,
                    'expected_output': expected_output
                }
            else:
                return {
                    'success': False,
                    'error': 'wrong_answer',
                    'message': 'Saída não corresponde ao esperado',
                    'execution_time': exec_result['execution_time'],
                    'actual_output': actual_output,
                    'expected_output': expected_output
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': 'test_error',
                'message': f'Erro no teste: {str(e)}',
                'execution_time': 0
            }
    
    def evaluate_submission(self, java_code, test_cases):
        """
        Avalia uma submissão completa com múltiplos casos de teste
        """
        try:
            self.create_temp_directory()
            
            results = []
            total_time = 0
            
            for i, test_case in enumerate(test_cases):
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
                    # Se um teste falhar, retorna o resultado imediatamente
                    return {
                        'status': result['error'],
                        'message': result['message'],
                        'execution_time': total_time,
                        'test_results': results,
                        'passed_tests': i,
                        'total_tests': len(test_cases)
                    }
            
            # Todos os testes passaram
            return {
                'status': 'accepted',
                'message': 'Todos os testes passaram',
                'execution_time': total_time,
                'test_results': results,
                'passed_tests': len(test_cases),
                'total_tests': len(test_cases)
            }
            
        except Exception as e:
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
    """
    challenge = submission.challenge
    
    # Verifica se é código Java
    if submission.language.name.lower() != 'java':
        return {
            'status': 'language_error',
            'message': 'Esta função é apenas para código Java'
        }
    
    # Cria executor
    executor = JavaCodeExecutor(
        time_limit=challenge.time_limit,
        memory_limit=128
    )
    
    # Avalia submissão
    result = executor.evaluate_submission(
        submission.code,
        challenge.test_cases
    )
    
    # Atualiza status da submissão
    status_mapping = {
        'accepted': 'accepted',
        'compilation_error': 'compilation_error',
        'compilation_timeout': 'compilation_error',
        'runtime_error': 'runtime_error',
        'time_limit_exceeded': 'time_limit',
        'wrong_answer': 'wrong_answer',
        'evaluation_error': 'runtime_error',
        'language_error': 'runtime_error'
    }
    
    submission.status = status_mapping.get(result['status'], 'runtime_error')
    submission.execution_time = result.get('execution_time', 0)
    submission.error_message = result.get('message', '')
    submission.save()
    
    return result


# Exemplo de uso no views.py:
"""
# No seu views.py, substitua a função evaluate_submission por:

from .java_executor import evaluate_java_submission

def evaluate_submission(submission):
    if submission.language.name.lower() == 'java':
        return evaluate_java_submission(submission)
    else:
        # Mantém a lógica existente para outras linguagens
        # ... seu código atual ...
"""