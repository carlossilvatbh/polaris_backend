"""
RAG (Retrieval-Augmented Generation) Module for POLARIS
Sistema de busca e enriquecimento de contexto para documentos jurídicos
"""

# Verificação segura de dependências RAG
RAG_AVAILABLE = False
RAG_STATUS = "⚠️ RAG avançado indisponível devido a conflitos de dependências"

# Tentar importar dependências individualmente
try:
    import langchain  # noqa: F401
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

try:
    import chromadb  # noqa: F401
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

# Comentando sentence_transformers até resolver conflitos de versão
# try:
#     import sentence_transformers
#     SENTENCE_TRANSFORMERS_AVAILABLE = True
# except ImportError:
#     SENTENCE_TRANSFORMERS_AVAILABLE = False
SENTENCE_TRANSFORMERS_AVAILABLE = False

# Status baseado em dependências disponíveis
if LANGCHAIN_AVAILABLE and CHROMADB_AVAILABLE:
    RAG_STATUS = "⚠️ RAG parcialmente funcional (sem sentence-transformers)"
else:
    rag_msg = (f"⚠️ RAG indisponível - langchain: {LANGCHAIN_AVAILABLE}, "
               f"chromadb: {CHROMADB_AVAILABLE}")
    RAG_STATUS = rag_msg
    print(f"\n{RAG_STATUS}")
    print("Para ativar RAG, execute: pip install -r requirements_rag.txt")

# Imports condicionais para evitar conflitos de dependências
try:
    from .document_processor import DocumentProcessor
    DOCUMENT_PROCESSOR_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ DocumentProcessor indisponível: {e}")
    DOCUMENT_PROCESSOR_AVAILABLE = False
    DocumentProcessor = None

try:
    from .utils import RAGUtils
    RAG_UTILS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ RAGUtils indisponível: {e}")
    RAG_UTILS_AVAILABLE = False
    RAGUtils = None

# Comentando imports problemáticos temporariamente
# from .rag_manager import JuridicalRAGManager
# from .mcp_integration import MCPRAGIntegration
JuridicalRAGManager = None
MCPRAGIntegration = None

__version__ = "1.0.0"
__all__ = [
    'RAG_AVAILABLE',
    'RAG_STATUS',
    'LANGCHAIN_AVAILABLE',
    'CHROMADB_AVAILABLE',
    'SENTENCE_TRANSFORMERS_AVAILABLE',
    'JuridicalRAGManager',
    'MCPRAGIntegration',
    'DocumentProcessor',
    'RAGUtils'
]
