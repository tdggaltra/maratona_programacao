# challenges/management/commands/test_submission.py

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from challenges.models import Challenge, Submission

class Command(BaseCommand):
    help = 'Testa criação de submissão'
    
    def handle(self, *args, **options):
        try:
            # Buscar usuário e challenge
            user = User.objects.first()
            challenge = Challenge.objects.first()
            
            if not user or not challenge:
                self.stdout.write(self.style.ERROR('Usuário ou challenge não encontrado'))
                return
            
            # Código de teste simples
            test_code = '''public class Test {
    public static void main(String[] args) {
        System.out.println("Hello World");
    }
}'''
            
            # Criar submissão
            submission = Submission(
                challenge=challenge,
                user=user,
                code=test_code,
                language=challenge.language,
                status='pending'
            )
            
            # Validar
            submission.full_clean()
            submission.save()
            
            self.stdout.write(
                self.style.SUCCESS(f'Submissão {submission.id} criada com sucesso!')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Erro: {e}')
            )