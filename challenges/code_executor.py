import os
import subprocess
import tempfile
import shutil
from django.conf import settings

class CodeExecutor:
    def __init__(self, language):
        self.language = language.upper()
        self.config = settings.CODE_EXECUTION.get(self.language, {})
        
    def execute(self, code, input_data=""):
        """Compila e executa código"""
        if not settings.CODE_EXECUTION.get('ENABLE_CODE_EXECUTION', False):
            return {"success": False, "error": "Execução de código desabilitada"}
            
        try:
            if self.language == 'C':
                return self._execute_c(code, input_data)
            elif self.language == 'CPP':
                return self._execute_cpp(code, input_data)
            elif self.language == 'JAVA':
                return self._execute_java(code, input_data)
            elif self.language == 'PYTHON':
                return self._execute_python(code, input_data)
            else:
                return {"success": False, "error": f"Linguagem {self.language} não suportada"}
        except Exception as e:
            return {"success": False, "error": f"Erro na execução: {str(e)}"}
    
    def _execute_c(self, code, input_data):
        """Executa código C"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Arquivos temporários
            source_file = os.path.join(temp_dir, "solution.c")
            executable = os.path.join(temp_dir, "solution")
            
            # Escrever código fonte
            with open(source_file, 'w') as f:
                f.write(code)
            
            # Compilar com bibliotecas matemáticas
            compile_cmd = [
                self.config.get('COMPILER_PATH', 'gcc'),
                source_file,
                '-o', executable,
                '-lm',  # Biblioteca matemática
                '-std=c99',
                '-O2'
            ]
            
            compile_result = subprocess.run(
                compile_cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if compile_result.returncode != 0:
                return {
                    "success": False,
                    "error": f"Erro de compilação C: {compile_result.stderr}"
                }
            
            # Executar
            try:
                exec_result = subprocess.run(
                    [executable],
                    input=input_data,
                    capture_output=True,
                    text=True,
                    timeout=self.config.get('TIMEOUT', 5)
                )
                
                return {
                    "success": True,
                    "output": exec_result.stdout,
                    "error": exec_result.stderr if exec_result.stderr else None
                }
            except subprocess.TimeoutExpired:
                return {"success": False, "error": "Tempo limite excedido"}
    
    def _execute_cpp(self, code, input_data):
        """Executa código C++"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Arquivos temporários
            source_file = os.path.join(temp_dir, "solution.cpp")
            executable = os.path.join(temp_dir, "solution")
            
            # Escrever código fonte
            with open(source_file, 'w') as f:
                f.write(code)
            
            # Compilar com bibliotecas matemáticas
            compile_cmd = [
                self.config.get('COMPILER_PATH', 'g++'),
                source_file,
                '-o', executable,
                '-lm',  # Biblioteca matemática
                '-std=c++17',
                '-O2'
            ]
            
            compile_result = subprocess.run(
                compile_cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if compile_result.returncode != 0:
                return {
                    "success": False,
                    "error": f"Erro de compilação C++: {compile_result.stderr}"
                }
            
            # Executar
            try:
                exec_result = subprocess.run(
                    [executable],
                    input=input_data,
                    capture_output=True,
                    text=True,
                    timeout=self.config.get('TIMEOUT', 5)
                )
                
                return {
                    "success": True,
                    "output": exec_result.stdout,
                    "error": exec_result.stderr if exec_result.stderr else None
                }
            except subprocess.TimeoutExpired:
                return {"success": False, "error": "Tempo limite excedido"}
    
    def _execute_java(self, code, input_data):
        """Executa código Java"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Arquivos temporários
            source_file = os.path.join(temp_dir, "Main.java")
            
            # Escrever código fonte
            with open(source_file, 'w') as f:
                f.write(code)
            
            # Compilar
            compile_cmd = [
                self.config.get('COMPILER_PATH', 'javac'),
                source_file
            ]
            
            compile_result = subprocess.run(
                compile_cmd,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=temp_dir
            )
            
            if compile_result.returncode != 0:
                return {
                    "success": False,
                    "error": f"Erro de compilação Java: {compile_result.stderr}"
                }
            
            # Executar
            try:
                exec_result = subprocess.run(
                    ['java', 'Main'],
                    input=input_data,
                    capture_output=True,
                    text=True,
                    timeout=self.config.get('TIMEOUT', 5),
                    cwd=temp_dir
                )
                
                return {
                    "success": True,
                    "output": exec_result.stdout,
                    "error": exec_result.stderr if exec_result.stderr else None
                }
            except subprocess.TimeoutExpired:
                return {"success": False, "error": "Tempo limite excedido"}
    
    def _execute_python(self, code, input_data):
        """Executa código Python"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Arquivo temporário
            source_file = os.path.join(temp_dir, "solution.py")
            
            # Escrever código fonte
            with open(source_file, 'w') as f:
                f.write(code)
            
            # Executar
            try:
                exec_result = subprocess.run(
                    [self.config.get('INTERPRETER_PATH', 'python3'), source_file],
                    input=input_data,
                    capture_output=True,
                    text=True,
                    timeout=self.config.get('TIMEOUT', 5)
                )
                
                return {
                    "success": True,
                    "output": exec_result.stdout,
                    "error": exec_result.stderr if exec_result.stderr else None
                }
            except subprocess.TimeoutExpired:
                return {"success": False, "error": "Tempo limite excedido"}