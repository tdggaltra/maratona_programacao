FROM python:3.11

# Instalar Java e dependências do sistema
RUN apt-get update && \
    apt-get install -y default-jdk gcc && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Configurar variáveis de ambiente do Java
ENV JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
ENV PATH="$JAVA_HOME/bin:$PATH"

# Verificar se Java foi instalado
RUN java -version && javac -version

# Definir diretório de trabalho
WORKDIR /app

# Copiar requirements e instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY . .

# Criar diretórios necessários
RUN mkdir -p staticfiles media logs temp_code_execution

# Definir permissões
RUN chmod 755 temp_code_execution

# Executar migrações e popular banco
RUN python manage.py migrate
RUN python populate_data.py
RUN python check_db.py
RUN python manage.py collectstatic --noinput

# Expor porta
EXPOSE $PORT

# Comando para iniciar aplicação
CMD gunicorn maratona_brasil.wsgi:application --bind 0.0.0.0:${PORT:-10000}