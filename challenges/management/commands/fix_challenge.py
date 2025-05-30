from django.core.management.base import BaseCommand
from challenges.models import Challenge
import json

class Command(BaseCommand):
    help = 'Corrige test cases de um desafio'
    
    def add_arguments(self, parser):
        parser.add_argument('challenge_id', type=int, help='ID do desafio para corrigir')
        parser.add_argument('--dry-run', action='store_true', help='Apenas mostrar o que seria corrigido')
    
    def handle(self, *args, **options):
        challenge_id = options['challenge_id']
        dry_run = options['dry_run']
        
        try:
            challenge = Challenge.objects.get(id=challenge_id)
            
            self.stdout.write(f"=== CORRIGINDO CHALLENGE {challenge_id}: {challenge.title} ===")
            
            if not challenge.test_cases:
                self.stdout.write("Nenhum test case encontrado")
                return
            
            original_test_cases = challenge.test_cases[:]
            fixed_test_cases = []
            changes_made = False
            
            for i, test_case in enumerate(challenge.test_cases):
                self.stdout.write(f"\nProcessando test case {i+1}...")
                
                if not isinstance(test_case, dict):
                    self.stdout.write(f"  ERRO: Test case {i+1} não é dict: {type(test_case)}")
                    continue
                
                fixed_case = {}
                
                # Corrigir input
                input_val = test_case.get('input')
                if input_val is None:
                    self.stdout.write(f"  AVISO: input ausente, usando string vazia")
                    fixed_case['input'] = ''
                    changes_made = True
                else:
                    # Garantir que é string
                    fixed_case['input'] = str(input_val)
                    if str(input_val) != input_val:
                        self.stdout.write(f"  CORREÇÃO: input convertido para string")
                        changes_made = True
                
                # Corrigir output
                output_val = test_case.get('output')
                if output_val is None:
                    self.stdout.write(f"  ERRO: output ausente no test case {i+1}")
                    continue
                else:
                    # Garantir que é string
                    fixed_case['output'] = str(output_val)
                    if str(output_val) != output_val:
                        self.stdout.write(f"  CORREÇÃO: output convertido para string")
                        changes_made = True
                
                # Verificar encoding
                try:
                    fixed_case['input'].encode('utf-8')
                    fixed_case['output'].encode('utf-8')
                except Exception as e:
                    self.stdout.write(f"  ERRO: Problema de encoding no test case {i+1}: {e}")
                    continue
                
                fixed_test_cases.append(fixed_case)
                self.stdout.write(f"  Test case {i+1}: OK")
            
            if changes_made:
                self.stdout.write(f"\n=== MUDANÇAS DETECTADAS ===")
                self.stdout.write(f"Test cases originais: {len(original_test_cases)}")
                self.stdout.write(f"Test cases corrigidos: {len(fixed_test_cases)}")
                
                if not dry_run:
                    challenge.test_cases = fixed_test_cases
                    challenge.save()
                    self.stdout.write(self.style.SUCCESS("Challenge corrigido e salvo!"))
                else:
                    self.stdout.write("DRY RUN - Nenhuma mudança foi salva")
                    
                # Mostrar preview dos test cases corrigidos
                self.stdout.write(f"\n=== PREVIEW DOS TEST CASES CORRIGIDOS ===")
                for i, tc in enumerate(fixed_test_cases[:3]):  # Mostrar apenas os 3 primeiros
                    self.stdout.write(f"Test case {i+1}:")
                    self.stdout.write(f"  Input: {repr(tc['input'])}")
                    self.stdout.write(f"  Output: {repr(tc['output'])}")
            else:
                self.stdout.write(self.style.SUCCESS("Nenhuma correção necessária"))
        
        except Challenge.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Challenge {challenge_id} não encontrado'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erro: {e}'))