# POLARIS Backend - Dockerfile
# Containerização segura preservando todas as funcionalidades existentes

FROM python:3.11-slim

# Definir diretório de trabalho
WORKDIR /app

# Instalar dependências básicas do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements primeiro para aproveitar cache do Docker
COPY requirements.txt .

# Instalar dependências Python básicas primeiro
RUN pip install --no-cache-dir flask flask-cors flask-sqlalchemy python-dotenv gunicorn psycopg2-binary

# Copiar código da aplicação
COPY . .

# Copiar e configurar script de entrada
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Criar diretórios necessários para uploads e dados
RUN mkdir -p uploads indexes logs

# Definir variáveis de ambiente
ENV FLASK_APP=src/main.py
ENV FLASK_ENV=production
ENV PYTHONPATH=/app
ENV PORT=5000

# Expor porta
EXPOSE 5000

# Health check simples
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

# Definir entrypoint
ENTRYPOINT ["docker-entrypoint.sh"]

# Comando para iniciar a aplicação
CMD ["python", "-m", "gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120", "src.main:app"]

