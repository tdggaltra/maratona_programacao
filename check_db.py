# check_db.py
import os
import django

# Configurar ambiente Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'maratona_brasil.settings')
django.setup()

from challenges.models import BrazilState, ProgrammingLanguage, Challenge
from django.contrib.auth.models import User

def check_database():
    """Verifica o conteúdo do banco de dados"""
    print("=== VERIFICAÇÃO DO BANCO DE DADOS ===")
    
    # Verificar usuários
    users_count = User.objects.count()
    print(f"👥 Usuários: {users_count}")
    if users_count > 0:
        admin_exists = User.objects.filter(username='admin').exists()
        print(f"🔑 Admin existe: {'Sim' if admin_exists else 'Não'}")
    
    # Verificar estados
    states_count = BrazilState.objects.count()
    print(f"🗺️  Estados: {states_count}")
    if states_count > 0:
        print("Estados encontrados:")
        for state in BrazilState.objects.all()[:5]:  # Mostrar apenas os primeiros 5
            print(f"  - {state.name} ({state.abbreviation})")
        if states_count > 5:
            print(f"  ... e mais {states_count - 5} estados")
    
    # Verificar linguagens
    languages_count = ProgrammingLanguage.objects.count()
    print(f"💻 Linguagens: {languages_count}")
    if languages_count > 0:
        print("Linguagens encontradas:")
        for lang in ProgrammingLanguage.objects.all():
            print(f"  - {lang.name} (.{lang.extension})")
    
    # Verificar desafios
    challenges_count = Challenge.objects.count()
    print(f"🎯 Desafios: {challenges_count}")
    if challenges_count > 0:
        print("Desafios encontrados:")
        for challenge in Challenge.objects.all()[:5]:  # Mostrar apenas os primeiros 5
            print(f"  - {challenge.title} ({challenge.state.name}) - {challenge.language.name}")
        if challenges_count > 5:
            print(f"  ... e mais {challenges_count - 5} desafios")
    
    print("=" * 50)
    
    # Resumo
    if states_count == 0:
        print("❌ PROBLEMA: Nenhum estado encontrado!")
    if languages_count == 0:
        print("❌ PROBLEMA: Nenhuma linguagem encontrada!")
    if challenges_count == 0:
        print("❌ PROBLEMA: Nenhum desafio encontrado!")
    
    if states_count > 0 and languages_count > 0 and challenges_count > 0:
        print("✅ Banco de dados parece estar populado corretamente!")
    else:
        print("⚠️  Banco de dados não está completamente populado")

if __name__ == '__main__':
    check_database()