#!/bin/bash

# setup_java_integration.sh
# Script simples para adicionar suporte Java ao sistema existente

echo "🔧 Integrando suporte Java ao sistema existente..."
echo "=================================================="

# Verificar se Java está instalado
echo "Verificando Java..."
if command -v javac &> /dev/null && command -v java &> /dev/null; then
    JAVA_VERSION=$(java -version 2>&1 | head -n 1)
    echo "✅ Java encontrado: $JAVA_VERSION"
else
    echo "❌ Java JDK não encontrado."
    echo "Por favor, instale Java JDK 11 ou superior:"
    echo ""
    echo "Ubuntu/Debian: sudo apt-get install openjdk-11-jdk"
    echo "CentOS/RHEL:   sudo yum install java-11-openjdk-devel"
    echo "macOS:         brew install openjdk@11"
    echo ""
    exit 1
fi

# Criar diretórios necessários
echo "Criando diretórios..."
mkdir -p temp_code_execution
mkdir -p logs
chmod 755 temp_code_execution

# Criar arquivo de política Java
echo "Criando política de segurança Java..."
cat > java.policy << 'EOF'
grant {
    permission java.io.FilePermission "<<ALL FILES>>", "read";
    permission java.lang.RuntimePermission "writeFileDescriptor";
    permission java.lang.RuntimePermission "readFileDescriptor";
    permission java.lang.RuntimePermission "accessDeclaredMembers";
    permission java.lang.RuntimePermission "accessClassInPackage.*";
    permission java.util.PropertyPermission "*", "read";
    permission java.lang.RuntimePermission "charsetProvider";
    permission java.lang.RuntimePermission "accessClassInPackage.sun.util.resources";
    permission java.lang.RuntimePermission "accessClassInPackage.sun.text.resources";
};

grant codeBase "file:${java.home}/lib/-" {
    permission java.security.AllPermission;
};
EOF

# Criar arquivo de teste
echo "Criando teste Java..."
cat > test_java_simple.py << 'EOF'
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
EOF

chmod +x test_java_simple.py

# Instruções finais
echo ""
echo "✅ Setup concluído!"
echo ""
echo "📋 Próximos passos:"
echo "1. Copie o código do java_executor.py para challenges/java_executor.py"
echo "2. Atualize seu challenges/views.py com as modificações fornecidas"
echo "3. Adicione as configurações ao seu settings.py"
echo "4. Aplique as modificações ao seu template challenge_detail.html"
echo "5. Execute: python test_java_simple.py"
echo ""
echo "🔗 Arquivos criados:"
echo "   - java.policy (política de segurança)"
echo "   - temp_code_execution/ (diretório temporário)"
echo "   - logs/ (para logs de execução)"
echo "   - test_java_simple.py (teste da integração)"
echo ""
echo "⚠️  Lembre-se: Seu sistema existente para Python/C/C++ continuará funcionando normalmente!"
