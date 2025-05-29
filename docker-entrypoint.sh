
#!/bin/bash

# Executar migrações
python manage.py migrate

# Popular banco se vazio
python populate_data.py

# Coletar arquivos estáticos
python manage.py collectstatic --noinput

# Iniciar aplicação
exec gunicorn maratona_brasil.wsgi:application --bind 0.0.0.0:${PORT:-10000}