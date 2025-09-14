#!/bin/bash
# POLARIS Backend - Docker Entrypoint
# Script de inicialização segura do container

set -e

echo "🚀 Iniciando POLARIS Backend..."

# Aguardar banco de dados estar disponível
if [ "$DATABASE_URL" ]; then
    echo "⏳ Aguardando banco de dados..."
    python -c "
import os
import time
import psycopg2
from urllib.parse import urlparse

if os.getenv('DATABASE_URL'):
    url = urlparse(os.getenv('DATABASE_URL'))
    for i in range(30):
        try:
            conn = psycopg2.connect(
                host=url.hostname,
                port=url.port,
                user=url.username,
                password=url.password,
                database=url.path[1:]
            )
            conn.close()
            print('✅ Banco de dados conectado!')
            break
        except:
            print(f'⏳ Tentativa {i+1}/30...')
            time.sleep(2)
    else:
        print('❌ Falha ao conectar com banco de dados')
        exit(1)
"
fi

# Criar tabelas do banco de dados
echo "📊 Criando tabelas do banco de dados..."
python -c "
import sys
sys.path.append('/app')
from src.main import app, db
with app.app_context():
    db.create_all()
    print('✅ Tabelas criadas com sucesso!')
"

# Criar diretórios necessários
mkdir -p /app/uploads /app/indexes /app/logs

# Definir permissões
chmod 755 /app/uploads /app/indexes /app/logs

echo "✅ POLARIS Backend inicializado com sucesso!"

# Executar comando passado como argumento
exec "$@"

