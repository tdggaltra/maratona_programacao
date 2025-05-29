#!/usr/bin/env python3

import os
import django
import sys

# Configurar Django
try:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'maratona_brasil.settings')
    django.setup()
    from challenges.java_executor import JavaCodeExecutor
except ImportError as e:
    print(f"❌ Erro ao importar: {e}")
    print("Certifique-se de que o arquivo java_executor.py foi criado.")
    sys.exit(1)

def test_java():
    print("🧪 Testando execução Java...")
    
    java_code = '''
import java.util.Scanner;

public class Main {
    public static void main(String[] args) {
        System.out.println("Hello, World!");
    }
}
'''
    
    executor = JavaCodeExecutor(time_limit=5000)
    test_cases = [{'input': '', 'output': 'Hello, World!'}]
    
    result = executor.evaluate_submission(java_code, test_cases)
    
    print(f"Status: {result['status']}")
    print(f"Mensagem: {result['message']}")
    
    if result['status'] == 'accepted':
        print("✅ Integração Java funcionando!")
        return True
    else:
        print("❌ Problema na integração Java.")
        return False

if __name__ == '__main__':
    test_java()
