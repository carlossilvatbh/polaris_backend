# Módulo RAG - Polaris Backend

## Visão Geral

O módulo RAG (Retrieval-Augmented Generation) é uma extensão opcional do Polaris Backend que adiciona capacidades de busca semântica em documentos jurídicos, melhorando significativamente a qualidade das respostas geradas pela IA.

## Características

- ✅ **Módulo Independente**: Não afeta funcionalidades existentes
- ✅ **Fallback Seguro**: Sistema funciona normalmente sem RAG instalado
- ✅ **Chunking Jurídico**: Processamento otimizado para documentos legais
- ✅ **Compatibilidade MCP**: Integração transparente com Model Context Protocol
- ✅ **Múltiplos Formatos**: Suporte para PDF, DOCX e TXT
- ✅ **Busca Semântica**: ChromaDB + sentence-transformers
- ✅ **Logs Detalhados**: Monitoramento completo de operações

## Instalação

### 1. Instalar Dependências RAG

```bash
# No diretório do projeto
pip install -r requirements_rag.txt
```

### 2. Verificar Instalação

```python
from rag.mcp_integration import MCPRAGIntegration

integration = MCPRAGIntegration()
status = integration.get_rag_status()
print(status)
```

## Uso Básico

### 1. Adicionando Documentos

```python
from rag.mcp_integration import MCPRAGIntegration

# Inicializar integração
rag_integration = MCPRAGIntegration()

# Adicionar documento individual
result = rag_integration.add_document(
    file_path="/caminho/para/documento.pdf",
    doc_type="lei",
    metadata={
        "titulo": "Lei 8.078/90",
        "categoria": "direito_consumidor",
        "data": "1990-09-11"
    }
)

# Adicionar múltiplos documentos
documents = [
    {
        "file_path": "/docs/codigo_civil.pdf",
        "doc_type": "codigo",
        "metadata": {"categoria": "civil"}
    },
    {
        "file_path": "/docs/clt.pdf", 
        "doc_type": "consolidacao",
        "metadata": {"categoria": "trabalhista"}
    }
]

for doc in documents:
    rag_integration.add_document(**doc)
```

### 2. Consulta com RAG

```python
# Consulta jurídica com contexto RAG
response = rag_integration.juridical_query(
    query="Quais são os direitos básicos do consumidor?",
    max_chunks=5,
    similarity_threshold=0.7
)

print("Resposta:", response["response"])
print("Documentos consultados:", response["sources"])
```

### 3. Integração com MCP Existente

```python
from src.services.mcp_service import MCPService
from rag.mcp_integration import MCPRAGIntegration

class EnhancedMCPService(MCPService):
    def __init__(self):
        super().__init__()
        self.rag_integration = MCPRAGIntegration()
    
    def enhanced_query(self, query: str):
        # Primeiro tenta com RAG
        if self.rag_integration.is_rag_available():
            rag_response = self.rag_integration.juridical_query(query)
            if rag_response["success"]:
                return rag_response
        
        # Fallback para MCP tradicional
        return self.traditional_mcp_query(query)
```

## Configuração Avançada

### 1. Configuração do ChromaDB

```python
from rag.rag_manager import JuridicalRAGManager

# Configuração personalizada
rag_manager = JuridicalRAGManager(
    persist_directory="./data/chroma_db",
    collection_name="documentos_juridicos_custom",
    embedding_model="sentence-transformers/all-MiniLM-L6-v2"
)
```

### 2. Chunking Personalizado

```python
from rag.utils import RAGUtils

utils = RAGUtils()

# Configurar chunking para documentos específicos
chunks = utils.chunk_juridical_document(
    text=document_text,
    chunk_size=800,
    chunk_overlap=100,
    doc_type="sentenca"
)
```

### 3. Busca Semântica Direta

```python
from rag.rag_manager import JuridicalRAGManager

rag_manager = JuridicalRAGManager()

# Busca semântica customizada
results = rag_manager.semantic_search(
    query="responsabilidade civil do fornecedor",
    k=10,
    filter_metadata={"categoria": "direito_consumidor"}
)
```

## Tipos de Documentos Suportados

| Tipo | Extensões | Chunking Específico |
|------|-----------|-------------------|
| PDF | `.pdf` | Artigos, seções, parágrafos |
| Word | `.docx`, `.doc` | Estrutura hierárquica |
| Texto | `.txt` | Quebras naturais |

## Metadados Recomendados

```python
metadata_exemplo = {
    "titulo": "Lei de Proteção de Dados",
    "numero": "13.709/2018", 
    "categoria": "direito_digital",
    "data": "2018-08-14",
    "jurisdicao": "federal",
    "status": "vigente",
    "tags": ["lgpd", "proteção_dados", "privacidade"]
}
```

## Monitoramento e Logs

O módulo RAG gera logs detalhados em diferentes níveis:

```python
import logging

# Configurar logs para RAG
logging.getLogger('rag').setLevel(logging.INFO)
logging.getLogger('chromadb').setLevel(logging.WARNING)
```

### Verificação de Status

```python
# Status completo do sistema RAG
status = rag_integration.get_rag_status()
print(f"RAG Disponível: {status['available']}")
print(f"Documentos Indexados: {status['document_count']}")
print(f"Última Atualização: {status['last_update']}")
```

## Troubleshooting

### Problema: "RAG dependencies not available"

**Solução**: Instalar dependências RAG
```bash
pip install -r requirements_rag.txt
```

### Problema: ChromaDB não persiste dados

**Solução**: Verificar permissões de diretório
```python
import os
os.makedirs("./data/chroma_db", exist_ok=True)
```

### Problema: Embeddings lentos

**Solução**: Usar modelo menor
```python
rag_manager = JuridicalRAGManager(
    embedding_model="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)
```

## Performance

### Benchmarks Típicos

- **Indexação**: ~2-5 docs/segundo (PDF médio)
- **Busca**: ~100-500ms por consulta
- **Memoria**: ~500MB-2GB (dependendo do corpus)

### Otimizações

1. **Batch Processing**: Processe múltiplos documentos em lote
2. **Chunking Eficiente**: Use tamanhos de chunk apropriados (500-1000 tokens)
3. **Filtros de Metadados**: Use filtros para reduzir espaço de busca

## Integração com Claude

O módulo RAG prepara automaticamente o contexto para Claude:

```python
# O contexto é formatado automaticamente
context = rag_manager.prepare_context_for_claude(relevant_chunks)
```

Formato do contexto:
```
=== DOCUMENTOS RELEVANTES ===

**Documento: Lei 8.078/90 - Art. 6º**
**Fonte: /docs/cdc.pdf**
**Relevância: 0.89**

São direitos básicos do consumidor:
I - a proteção da vida, saúde e segurança...

---

**Documento: Jurisprudência STJ**
...
```

## Segurança

- ✅ **Imports Opcionais**: Não quebra se dependências ausentes
- ✅ **Fallback Robusto**: Sistema funciona sem RAG
- ✅ **Validação de Entrada**: Todos os inputs são validados
- ✅ **Tratamento de Erros**: Logs detalhados de falhas
- ✅ **Isolamento**: Módulo independente dos arquivos MCP

## Desenvolvimento

### Estrutura de Arquivos

```
rag/
├── __init__.py              # Exportações públicas
├── rag_manager.py          # Core RAG (ChromaDB + embeddings)
├── document_processor.py   # Processamento de documentos
├── mcp_integration.py      # Bridge segura para MCP
└── utils.py               # Utilitários e chunking jurídico
```

### Testando Localmente

```python
# Teste básico de funcionamento
from rag.mcp_integration import MCPRAGIntegration

integration = MCPRAGIntegration()
if integration.is_rag_available():
    print("✅ RAG funcionando corretamente")
else:
    print("❌ Instalar dependências RAG")
```

## Contribuição

Para contribuir com o módulo RAG:

1. Manter compatibilidade com MCP existente
2. Usar imports opcionais para novas dependências
3. Implementar fallbacks robustos
4. Adicionar logs detalhados
5. Documentar mudanças

## Licença

Parte do projeto Polaris Backend - Todos os direitos reservados.
