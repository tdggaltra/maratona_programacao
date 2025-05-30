from django.core.management.base import BaseCommand
from challenges.models import Challenge
from challenges.java_executor import JavaCodeExecutor

class Command(BaseCommand):
    help = 'Testa Java executor específico'
    
    def handle(self, *args, **options):
        try:
            # Código Java simples
            test_code = '''public class Test {
    public static void main(String[] args) {
        System.out.println("Hello World");
    }
}'''
            
            test_cases = [
                {'input': '', 'output': 'Hello World'}
            ]
            
            self.stdout.write("=== TESTE JAVA EXECUTOR ===")
            self.stdout.write(f"Código: {len(test_code)} caracteres")
            self.stdout.write(f"Test cases: {len(test_cases)}")
            
            # Criar executor
            executor = JavaCodeExecutor(time_limit=5000, memory_limit=128)
            
            self.stdout.write("Executor criado...")
            
            # Executar
            result = executor.evaluate_submission(test_code, test_cases)
            
            self.stdout.write(f"Resultado: {result}")
            
            if result['status'] == 'accepted':
                self.stdout.write(self.style.SUCCESS("✅ Java executor funcionando!"))
            else:
                self.stdout.write(self.style.ERROR(f"❌ Java executor falhou: {result['message']}"))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Erro crítico: {e}"))
            import traceback
            self.stdout.write(traceback.format_exc())