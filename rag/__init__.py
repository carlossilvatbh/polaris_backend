"""
RAG (Retrieval-Augmented Generation) Module for POLARIS
Sistema de busca e enriquecimento de contexto para documentos jurídicos
"""

# Verificação segura de dependências RAG
try:
    import langchain
    import chromadb
    import sentence_transformers
    RAG_AVAILABLE = True
    RAG_STATUS = "✅ RAG totalmente funcional"
except ImportError as e:
    RAG_AVAILABLE = False
    RAG_STATUS = f"⚠️ RAG não disponível: {str(e)}"
    print(f"\n{RAG_STATUS}")
    print("Para ativar RAG, execute: pip install -r requirements_rag.txt")

from .rag_manager import JuridicalRAGManager
from .mcp_integration import MCPRAGIntegration
from .document_processor import DocumentProcessor
from .utils import RAGUtils

__version__ = "1.0.0"
__all__ = [
    'RAG_AVAILABLE',
    'RAG_STATUS', 
    'JuridicalRAGManager',
    'MCPRAGIntegration',
    'DocumentProcessor',
    'RAGUtils'
]
