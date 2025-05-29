# 🇧🇷 Maratona Brasil - Sistema de Desafios de Programação

Um sistema interativo de desafios de programação que leva os estudantes em uma jornada pelos estados do Brasil, resolvendo problemas únicos para cada região.

## 📋 Funcionalidades

- 🗺️ **Mapa Interativo** - Navegue pelos estados do Brasil
- 💻 **Múltiplas Linguagens** - Suporte para Python, Java, C, C++
- 🏆 **Sistema de Progressão** - Desbloqueie estados sequencialmente
- 📊 **Acompanhamento** - Pontuação e estatísticas de progresso
- 👤 **Perfis de Usuário** - Sistema completo de autenticação
- 🎯 **Desafios Únicos** - Problemas específicos para cada estado

## 🚀 Tecnologias Utilizadas

- **Backend**: Django 4.2.7
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **Banco de Dados**: SQLite (desenvolvimento) / PostgreSQL (produção)
- **Autenticação**: Django Auth System
- **Execução de Código**: Subprocess (Python, Java, C, C++)

## 📦 Instalação

### 1. Clonar o repositório
```bash
git clone https://github.com/tdggaltra/maratona-brasil.git
cd maratona-brasil
```

### 2. Criar ambiente virtual
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

### 3. Instalar dependências
```bash
pip install -r requirements.txt
```

### 4. Configurar banco de dados
```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Popular dados iniciais
```bash
python populate_data.py
```

### 6. Criar superusuário
```bash
python manage.py createsuperuser
```

### 7. Executar servidor
```bash
python manage.py runserver
```

Acesse: `http://localhost:8000`

## 🗂️ Estrutura do Projeto

```
maratona_brasil/
├── accounts/          # Autenticação e perfis
├── challenges/        # Sistema de desafios
├── core/             # Funcionalidades principais
├── static/           # Arquivos estáticos
├── templates/        # Templates HTML
├── media/           # Uploads de usuários
├── populate_data.py # Script de dados iniciais
└── requirements.txt # Dependências
```

## 🎮 Como Usar

1. **Registre-se** ou faça login
2. **Navegue pelo mapa** do Brasil
3. **Clique em um estado** disponível
4. **Resolva o desafio** de programação
5. **Desbloqueie** o próximo estado
6. **Complete** todos os 27 desafios!

## 🏆 Estados e Desafios

- **🟢 Norte**: Desafios introdutórios (Python)
- **🔴 Nordeste**: Algoritmos básicos (Python/JavaScript)
- **🟠 Centro-Oeste**: Estruturas de dados (Python/C)
- **🟡 Sudeste**: Algoritmos intermediários (Java/C++)
- **🔵 Sul**: Desafios avançados (C++)
- **⭐ DF**: Desafio final especial

## 🛠️ Configuração para Produção

### Variáveis de Ambiente
```bash
SECRET_KEY=sua-chave-secreta-super-forte
DEBUG=False
DATABASE_URL=postgresql://usuario:senha@host:porta/database
ALLOWED_HOSTS=seudominio.com,*.railway.app
```

### Deploy (Railway)
1. Conecte o repositório ao Railway
2. Configure as variáveis de ambiente
3. O deploy será automático

### Deploy (Outras Plataformas)
```bash
# Coletar arquivos estáticos
python manage.py collectstatic

# Aplicar migrações
python manage.py migrate

# Popular dados (primeira vez)
python populate_data.py
```

## 🧪 Testes

```bash
# Executar testes
python manage.py test

# Verificar cobertura
coverage run manage.py test
coverage report
```

## 📚 Linguagens Suportadas

| Linguagem | Extensão | Status |
|-----------|----------|--------|
| Python    | .py      | ✅ Completo |
| Java      | .java    | ✅ Completo |
| C         | .c       | ✅ Completo |
| C++       | .cpp     | ✅ Completo |
| JavaScript| .js      | 🚧 Em desenvolvimento |

## 🤝 Contribuindo

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para detalhes.

## 👨‍💻 Autor

**Seu Nome**
- GitHub: [@seu-usuario](https://github.com/seu-usuario)
- Email: seuemail@exemplo.com

## 🙏 Agradecimentos

- Estudantes que testaram o sistema
- Comunidade Django Brasil
- Contribuidores open source

---

⭐ Se este projeto te ajudou, deixe uma estrela no repositório!  
