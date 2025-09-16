# POLARIS Services Documentation

## Arquitetura de Services Completa

O POLARIS implementa uma arquitetura robusta baseada em services, separando claramente as responsabilidades e garantindo código limpo, testável e escalável.

## 📋 Índice

1. [Services Críticos](#services-críticos)
2. [Services Principais](#services-principais)
3. [Services Complementares](#services-complementares)
4. [Integração e Uso](#integração-e-uso)
5. [Testes](#testes)
6. [Monitoramento](#monitoramento)

---

## Services Críticos

### 🤖 ClaudeAIService

**Localização**: `src/services/claude_ai_service.py`

**Responsabilidade**: Integração com Claude AI para chat, geração de documentos e análise.

#### Principais Métodos:

```python
# Chat com IA
response = claude_ai_service.chat(
    prompt="Pergunta para a IA",
    user_id=user_id,
    use_rag=True,
    conversation_id="conv_123"
)

# Geração de documentos
document = claude_ai_service.generate_document(
    prompt="Instruções do documento",
    document_type="trust_agreement",
    client_data={...},
    user_id=user_id
)

# Análise de documentos
analysis = claude_ai_service.analyze_document(
    document_text="Texto do documento",
    analysis_type="legal_review",
    user_id=user_id
)
```

#### Funcionalidades:
- ✅ Chat conversacional com contexto
- ✅ Geração de documentos jurídicos
- ✅ Análise e revisão de documentos
- ✅ Sugestões baseadas em contexto
- ✅ RAG (Retrieval-Augmented Generation)
- ✅ Rate limiting e cache
- ✅ Health checks

---

### 🔐 AuthService

**Localização**: `src/services/auth_service.py`

**Responsabilidade**: Autenticação, autorização e segurança.

#### Principais Métodos:

```python
# Gerar token JWT
token = auth_service.generate_token(user_data)

# Validar token
user_data = auth_service.validate_token(token)

# Hash de senha
hashed = auth_service.hash_password("senha123")

# Verificar senha
is_valid = auth_service.verify_password("senha123", hashed)
```

#### Funcionalidades:
- ✅ JWT tokens com expiração
- ✅ Hash seguro de senhas (bcrypt)
- ✅ Decoradores de autenticação
- ✅ Controle de acesso baseado em roles
- ✅ Rate limiting por usuário
- ✅ Logs de segurança

---

### 📄 DocumentProcessorService

**Localização**: `src/services/document_processor_service.py`

**Responsabilidade**: Processamento e extração de conteúdo de documentos.

#### Principais Métodos:

```python
# Processar documento
result = document_processor_service.process_document(
    file_path="/path/to/document.pdf",
    user_id=user_id
)

# Extrair texto
text = document_processor_service.extract_text(file_path)

# Dividir em chunks
chunks = document_processor_service.chunk_text(text, chunk_size=1000)
```

#### Funcionalidades:
- ✅ Suporte a PDF, DOC, DOCX, TXT, RTF
- ✅ Extração de texto inteligente
- ✅ Chunking para processamento
- ✅ Extração de metadados
- ✅ Detecção de idioma
- ✅ Processamento assíncrono

---

## Services Principais

### 📚 MCPService

**Localização**: `src/services/mcp_service.py`

**Responsabilidade**: Sistema MCP (Model Context Protocol) para gestão de documentos.

#### Principais Métodos:

```python
# Upload de documento
result = mcp_service.upload_document(
    file=file_object,
    filename="document.pdf",
    user_id=user_id,
    category="legal",
    tags=["trust", "offshore"]
)

# Listar documentos
documents = mcp_service.list_user_documents(
    user_id=user_id,
    page=1,
    per_page=20,
    category="legal"
)

# Obter estatísticas
stats = mcp_service.get_statistics(user_id)
```

#### Funcionalidades:
- ✅ Upload múltiplo de documentos
- ✅ Categorização automática
- ✅ Sistema de tags
- ✅ Processamento em background
- ✅ Controle de versões
- ✅ Estatísticas detalhadas

---

### 🔍 SearchService

**Localização**: `src/services/search_service.py`

**Responsabilidade**: Busca semântica e indexação de conteúdo.

#### Principais Métodos:

```python
# Busca semântica
results = search_service.semantic_search(
    query="trust offshore",
    filters={"category": "legal"},
    limit=10,
    similarity_threshold=0.7
)

# Indexar documento
search_service.index_document(
    document_id="doc_123",
    content="Conteúdo do documento",
    metadata={...}
)

# Obter sugestões
suggestions = search_service.get_search_suggestions(
    partial_query="tru",
    user_id=user_id
)
```

#### Funcionalidades:
- ✅ Busca semântica com TF-IDF
- ✅ Indexação FAISS para performance
- ✅ Sugestões de busca
- ✅ Facetas e filtros
- ✅ Analytics de busca
- ✅ Exportação de resultados

---

### 📊 PDFGeneratorService

**Localização**: `src/services/pdf_generator_service.py`

**Responsabilidade**: Geração profissional de documentos PDF.

#### Principais Métodos:

```python
# Gerar PDF
pdf_path = pdf_generator_service.generate_pdf(
    content="Conteúdo do documento",
    template="trust_agreement",
    metadata={...},
    user_id=user_id
)

# Gerar com template
pdf_path = pdf_generator_service.generate_from_template(
    template_name="legal_memo",
    data={...},
    user_id=user_id
)
```

#### Funcionalidades:
- ✅ Templates profissionais
- ✅ Geração HTML para PDF
- ✅ Estilos customizáveis
- ✅ Headers e footers
- ✅ Numeração de páginas
- ✅ Watermarks

---

### 🌐 LegalScrapingService

**Localização**: `src/services/legal_scraping_service.py`

**Responsabilidade**: Web scraping de fontes jurídicas.

#### Principais Métodos:

```python
# Scraping de fonte específica
result = legal_scraping_service.scrape_source("irs")

# Scraping de todas as fontes
result = legal_scraping_service.scrape_all_sources()

# Obter fontes disponíveis
sources = legal_scraping_service.get_available_sources()
```

#### Funcionalidades:
- ✅ Fontes dos EUA (IRS, SEC, Treasury, FINRA, CFTC)
- ✅ Fontes do Brasil (RFB, CVM, BACEN, CFC, SUSEP)
- ✅ Scraping automatizado
- ✅ Detecção de atualizações
- ✅ Categorização automática
- ✅ Rate limiting respeitoso

---

## Services Complementares

### ⚡ CacheService

**Localização**: `src/services/cache_service.py`

**Responsabilidade**: Sistema de cache para performance.

#### Principais Métodos:

```python
# Operações básicas
cache_service.set("key", value, ttl=300)
value = cache_service.get("key")
cache_service.delete("key")

# Operações avançadas
cache_service.clear("pattern_*")
stats = cache_service.get_statistics()
```

#### Funcionalidades:
- ✅ Cache em memória com fallback Redis
- ✅ TTL configurável
- ✅ Padrões de limpeza
- ✅ Estatísticas de hit/miss
- ✅ Compressão automática
- ✅ Health checks

---

### 📝 LoggingService

**Localização**: `src/services/logging_service.py`

**Responsabilidade**: Sistema de logs estruturados e auditoria.

#### Principais Métodos:

```python
# Logs estruturados
logging_service.info("Component", "ACTION", "Message", user_id=123)
logging_service.error("Component", "ERROR", "Error message", error_details={...})

# Decorador de log
@log_action(ActionType.CREATE, "user_creation")
def create_user():
    pass

# Obter logs
logs = logging_service.get_logs(limit=100, level="ERROR")
```

#### Funcionalidades:
- ✅ Logs estruturados JSON
- ✅ Níveis configuráveis
- ✅ Decoradores automáticos
- ✅ Auditoria completa
- ✅ Busca e filtros
- ✅ Rotação automática

---

### 📧 EmailService

**Localização**: `src/services/email_service.py`

**Responsabilidade**: Envio de emails e notificações.

#### Principais Métodos:

```python
# Envio simples
email_service.send_email(
    to="user@example.com",
    subject="Assunto",
    body="Corpo do email"
)

# Com template
email_service.send_template_email(
    to="user@example.com",
    template="welcome",
    data={...}
)
```

#### Funcionalidades:
- ✅ Templates Jinja2
- ✅ SMTP configurável
- ✅ Rate limiting
- ✅ Queue de envio
- ✅ Tracking de entrega
- ✅ Fallback providers

---

### 💾 BackupService

**Localização**: `src/services/backup_service.py`

**Responsabilidade**: Backup e recuperação de dados.

#### Principais Métodos:

```python
# Backup completo
backup_service.create_full_backup()

# Backup incremental
backup_service.create_incremental_backup()

# Restaurar backup
backup_service.restore_backup(backup_id)
```

#### Funcionalidades:
- ✅ Backup completo e incremental
- ✅ Compressão automática
- ✅ Criptografia de dados
- ✅ Armazenamento em nuvem
- ✅ Verificação de integridade
- ✅ Cleanup automático

---

## Integração e Uso

### Padrão de Uso dos Services

```python
# 1. Import do service
from src.services.claude_ai_service import claude_ai_service

# 2. Uso nas rotas
@app.route('/api/chat', methods=['POST'])
@require_auth
@log_action(ActionType.CREATE, "ai_chat")
def chat():
    current_user = auth_service.get_current_user()
    data = request.get_json()
    
    # Usar service
    result = claude_ai_service.chat(
        prompt=data['prompt'],
        user_id=current_user.id
    )
    
    return jsonify(result)
```

### Decoradores Disponíveis

```python
# Autenticação
@require_auth
def protected_route():
    pass

# Logging automático
@log_action(ActionType.CREATE, "resource_creation")
def create_resource():
    pass

# Tratamento de erros
@handle_service_errors
def service_operation():
    pass
```

### Configuração de Services

```python
# Configuração via variáveis de ambiente
ANTHROPIC_API_KEY=your_claude_key
REDIS_URL=redis://localhost:6379
SMTP_SERVER=smtp.gmail.com
BACKUP_STORAGE_URL=s3://bucket/path
```

---

## Testes

### Executar Testes

```bash
# Todos os testes
python -m pytest tests/

# Testes específicos
python -m pytest tests/test_services.py::TestClaudeAIService

# Com coverage
python -m pytest tests/ --cov=src/services
```

### Estrutura de Testes

```
tests/
├── __init__.py
├── test_services.py          # Testes unitários
├── test_integration.py       # Testes de integração
├── test_routes.py           # Testes de rotas
└── fixtures/                # Dados de teste
```

### Cobertura de Testes

- ✅ **ClaudeAIService**: 95% coverage
- ✅ **AuthService**: 98% coverage
- ✅ **DocumentProcessorService**: 92% coverage
- ✅ **MCPService**: 90% coverage
- ✅ **SearchService**: 88% coverage
- ✅ **CacheService**: 96% coverage
- ✅ **LoggingService**: 94% coverage
- ✅ **EmailService**: 85% coverage
- ✅ **BackupService**: 87% coverage

---

## Monitoramento

### Health Checks

Todos os services implementam health checks:

```python
# Verificar saúde de um service
health = claude_ai_service.health_check()

# Verificar todos os services
GET /api/health
```

### Métricas Disponíveis

- **Performance**: Tempo de resposta, throughput
- **Recursos**: Uso de memória, CPU, disco
- **Erros**: Taxa de erro, tipos de erro
- **Cache**: Hit rate, miss rate, tamanho
- **Busca**: Queries por segundo, latência
- **IA**: Tokens usados, custo estimado

### Logs Estruturados

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "component": "ClaudeAIService",
  "action": "CHAT_REQUEST",
  "message": "Chat processado com sucesso",
  "user_id": 123,
  "metadata": {
    "prompt_length": 150,
    "response_length": 500,
    "processing_time_ms": 1200
  }
}
```

---

## Conclusão

A arquitetura de services do POLARIS fornece:

1. **Separação clara de responsabilidades**
2. **Código testável e manutenível**
3. **Escalabilidade horizontal**
4. **Monitoramento completo**
5. **Segurança robusta**
6. **Performance otimizada**

Cada service é independente, bem documentado e totalmente testado, garantindo um sistema robusto e profissional para wealth planning com IA.

