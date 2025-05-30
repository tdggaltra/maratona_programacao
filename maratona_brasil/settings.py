# maratona_brasil/settings.py

import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'sua-chave-secreta-aqui')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

# Configuração para produção no Render
ALLOWED_HOSTS = [
    'maratona-programacao.onrender.com',
    'maratona-programacao-1.onrender.com',  # Nova URL Docker
    'localhost', 
    '127.0.0.1',
    '*'  # Permitir qualquer host (para desenvolvimento)
]

# Aplicativos instalados
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Apps de terceiros
    'crispy_forms',
    
    # Apps locais
    'core',
    'challenges',
    'accounts.apps.AccountsConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Adicionar whitenoise apenas se instalado
try:
    import whitenoise
    MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
    # Para melhor performance na produção
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
except ImportError:
    pass  # WhiteNoise não instalado, continuar sem ele

ROOT_URLCONF = 'maratona_brasil.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'maratona_brasil.wsgi.application'

# Configuração do banco de dados
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Validação de senha
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Configurações de internacionalização
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Arquivos estáticos (CSS, JavaScript, Imagens)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Diretórios de arquivos estáticos
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

# Para melhor performance na produção (comentado até instalar whitenoise)
# STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Arquivos de mídia
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Configurações de login/logout
LOGIN_REDIRECT_URL = 'home'
LOGIN_URL = 'login'
LOGOUT_REDIRECT_URL = 'about'

# Configurações de sessão
SESSION_COOKIE_AGE = 3600 * 24 * 7  # 7 dias
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# Configurações de mensagens para melhor feedback
from django.contrib.messages import constants as messages
MESSAGE_TAGS = {
    messages.DEBUG: 'debug',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'danger',
}

# Crispy Forms
CRISPY_TEMPLATE_PACK = 'bootstrap4'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ==========================================
# CONFIGURAÇÕES PARA EXECUÇÃO DE CÓDIGO JAVA
# ==========================================

# Configurações para execução de código
CODE_EXECUTION = {
    # Diretório temporário para execução de código
    'TEMP_DIR': BASE_DIR / 'temp_code_execution',
    
    # Configurações de segurança
    'ENABLE_CODE_EXECUTION': True,  # Habilitar execução em produção também
    'MAX_EXECUTION_TIME': 10,  # segundos
    'MAX_MEMORY_USAGE': 256,   # MB
    'MAX_OUTPUT_SIZE': 1024 * 1024,  # 1MB
    
    # Configurações específicas para Java
    'JAVA': {
        'COMPILER_PATH': 'javac',
        'RUNTIME_PATH': 'java',
        'COMPILE_TIMEOUT': 30,
        'MEMORY_LIMIT': 128,
        'CLASSPATH': '.',
        'POLICY_FILE': BASE_DIR / 'java.policy',
        'TIMEOUT': 10,  # Aumentado de 5 para 10 segundos
        'JVM_ARGS': [
            '-Xmx128m',
            '-Xss1m',
            '-Djava.security.manager',
            '-Djava.security.policy=java.policy'
        ]
    },
    
    # Outras linguagens
    'PYTHON': {
        'INTERPRETER_PATH': 'python3',
        'TIMEOUT': 5,
    },
    
    'C': {
        'COMPILER_PATH': 'gcc',
        'COMPILER_FLAGS': ['-O2', '-std=c99', '-lm'],  # Adicionado -lm para bibliotecas matemáticas
        'TIMEOUT': 5,
    },
    
    'CPP': {
        'COMPILER_PATH': 'g++',
        'COMPILER_FLAGS': ['-O2', '-std=c++17', '-lm'],  # Adicionado -lm para bibliotecas matemáticas
        'TIMEOUT': 5,
    }
}

# Configurações de logging (simplificadas para produção)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        'challenges.java_executor': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# Configurações de segurança para produção
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_SECONDS = 31536000
    SESSION_COOKIE_SECURE = False  # Render não força HTTPS internamente
    CSRF_COOKIE_SECURE = False     # Render não força HTTPS internamente

# Configurações de cache
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# Configurações específicas para o sistema de quiz
QUIZ_SETTINGS = {
    'MAX_SUBMISSIONS_PER_HOUR': 30,
    'POINTS_MULTIPLIER': {
        'easy': 1.0,
        'medium': 1.5,
        'hard': 2.0,
        'expert': 3.0,
        'final': 5.0,
    },
    'UNLOCK_DELAY_SECONDS': 0,
}

# Email settings
if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = 'smtp.gmail.com'
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
    EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')

# ==========================================
# CRIAÇÃO DE DIRETÓRIOS NECESSÁRIOS
# ==========================================

# Criar diretórios necessários se não existirem
directories_to_create = [
    CODE_EXECUTION['TEMP_DIR'],
    BASE_DIR / 'media',
    BASE_DIR / 'staticfiles',
]

for directory in directories_to_create:
    try:
        os.makedirs(directory, exist_ok=True)
    except (OSError, PermissionError):
        pass  # Ignora erros de permissão

# ==========================================
# CONFIGURAÇÕES DE DESENVOLVIMENTO
# ==========================================

if DEBUG:
    # Django Debug Toolbar (se instalado)
    try:
        import debug_toolbar
        INSTALLED_APPS.append('debug_toolbar')
        MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')
        INTERNAL_IPS = ['127.0.0.1']
        
        DEBUG_TOOLBAR_CONFIG = {
            'SHOW_TOOLBAR_CALLBACK': lambda request: DEBUG,
        }
    except ImportError:
        pass
    
    # Verificar se os comandos Java estão disponíveis
    import shutil
    
    if not shutil.which(CODE_EXECUTION['JAVA']['COMPILER_PATH']):
        print("⚠️  AVISO: javac não encontrado. Execução Java pode não funcionar.")
        print("   Instale Java JDK para usar desafios Java.")
    
    if not shutil.which(CODE_EXECUTION['JAVA']['RUNTIME_PATH']):
        print("⚠️  AVISO: java não encontrado. Execução Java pode não funcionar.")
        print("   Instale Java JRE/JDK para usar desafios Java.")

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': '/tmp/django_debug.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'challenges.views': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}