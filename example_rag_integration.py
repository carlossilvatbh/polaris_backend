#!/usr/bin/env python3
"""
Script de exemplo: Integração RAG com MCP Polaris
Demonstra como integrar o módulo RAG com o sistema MCP existente
sem quebrar funcionalidades.
"""

import sys
import os
import logging
from typing import Dict, Any, Optional

# Adicionar path do projeto
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_rag_availability() -> bool:
    """Verifica se o módulo RAG está disponível."""
    try:
        from rag.mcp_integration import MCPRAGIntegration
        integration = MCPRAGIntegration()
        return integration.is_rag_available()
    except ImportError as e:
        logger.warning(f"Módulo RAG não disponível: {e}")
        return False


class EnhancedJuridicalService:
    """
    Serviço jurídico aprimorado que integra RAG com MCP existente.
    Mantém funcionalidade completa mesmo sem RAG instalado.
    """
    
    def __init__(self):
        self.rag_available = False
        self.rag_integration = None
        
        # Tentar inicializar RAG
        try:
            from rag.mcp_integration import MCPRAGIntegration
            self.rag_integration = MCPRAGIntegration()
            self.rag_available = self.rag_integration.is_rag_available()
            
            if self.rag_available:
                logger.info("✅ RAG inicializado com sucesso")
            else:
                logger.info("⚠️ RAG não disponível - usando fallback")
                
        except ImportError:
            logger.info("📦 Dependências RAG não instaladas - usando MCP tradicional")
    
    def juridical_query(self, query: str, use_rag: bool = True) -> Dict[str, Any]:
        """
        Executa consulta jurídica com RAG se disponível, senão usa MCP tradicional.
        
        Args:
            query: Pergunta jurídica
            use_rag: Se deve tentar usar RAG (default: True)
        
        Returns:
            Resposta estruturada com metadados
        """
        logger.info(f"Consulta jurídica: {query[:100]}...")
        
        # Tentar RAG primeiro se disponível e solicitado
        if use_rag and self.rag_available and self.rag_integration:
            try:
                logger.info("🔍 Executando consulta com RAG...")
                rag_response = self.rag_integration.juridical_query(
                    query=query,
                    max_chunks=5,
                    similarity_threshold=0.6
                )
                
                if rag_response.get("success", False):
                    logger.info("✅ Consulta RAG bem-sucedida")
                    return {
                        "response": rag_response["response"],
                        "method": "RAG",
                        "sources": rag_response.get("sources", []),
                        "chunks_used": len(rag_response.get("context_chunks", [])),
                        "success": True
                    }
                else:
                    logger.warning("⚠️ RAG falhou, usando fallback MCP")
                    
            except Exception as e:
                logger.error(f"❌ Erro no RAG: {e}")
                logger.info("🔄 Fallback para MCP tradicional")
        
        # Fallback para MCP tradicional
        return self._traditional_mcp_query(query)
    
    def _traditional_mcp_query(self, query: str) -> Dict[str, Any]:
        """
        Simula consulta MCP tradicional (aqui você integraria com o MCP real).
        """
        logger.info("🔧 Executando consulta MCP tradicional")
        
        # Aqui você integraria com o serviço MCP existente
        # from src.services.mcp_service import MCPService
        # mcp_service = MCPService()
        # response = mcp_service.query(query)
        
        # Simulação para demonstração
        response = f"Resposta MCP tradicional para: {query}"
        
        return {
            "response": response,
            "method": "MCP_Traditional",
            "sources": [],
            "chunks_used": 0,
            "success": True
        }
    
    def add_document_to_rag(self, file_path: str, doc_type: str = "lei", 
                           metadata: Optional[Dict] = None) -> bool:
        """
        Adiciona documento ao índice RAG se disponível.
        
        Args:
            file_path: Caminho para o arquivo
            doc_type: Tipo do documento
            metadata: Metadados opcionais
        
        Returns:
            True se adicionado com sucesso
        """
        if not self.rag_available or not self.rag_integration:
            logger.warning("RAG não disponível para adicionar documento")
            return False
        
        try:
            result = self.rag_integration.add_document(
                file_path=file_path,
                doc_type=doc_type,
                metadata=metadata or {}
            )
            
            if result.get("success", False):
                logger.info(f"✅ Documento adicionado: {file_path}")
                return True
            else:
                logger.error(f"❌ Falha ao adicionar documento: {result.get('error')}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro ao adicionar documento: {e}")
            return False
    
    def get_system_status(self) -> Dict[str, Any]:
        """Retorna status completo do sistema."""
        status = {
            "rag_available": self.rag_available,
            "mcp_available": True,  # MCP sempre disponível
            "timestamp": "2024-01-15T10:00:00Z"
        }
        
        if self.rag_available and self.rag_integration:
            try:
                rag_status = self.rag_integration.get_rag_status()
                status.update({
                    "rag_details": rag_status,
                    "document_count": rag_status.get("document_count", 0)
                })
            except Exception as e:
                logger.error(f"Erro ao obter status RAG: {e}")
                status["rag_error"] = str(e)
        
        return status


def demo_basic_usage():
    """Demonstração básica de uso."""
    print("=" * 60)
    print("DEMO: Integração RAG + MCP Polaris")
    print("=" * 60)
    
    # Inicializar serviço
    service = EnhancedJuridicalService()
    
    # Verificar status
    status = service.get_system_status()
    print(f"\n📊 Status do Sistema:")
    print(f"RAG Disponível: {status['rag_available']}")
    print(f"MCP Disponível: {status['mcp_available']}")
    
    if status.get('document_count'):
        print(f"Documentos Indexados: {status['document_count']}")
    
    # Exemplos de consultas
    queries = [
        "Quais são os direitos básicos do consumidor?",
        "Como funciona a responsabilidade civil do fornecedor?",
        "O que é considerado vício do produto?"
    ]
    
    print(f"\n🔍 Testando Consultas:")
    print("-" * 40)
    
    for i, query in enumerate(queries, 1):
        print(f"\n{i}. Pergunta: {query}")
        
        try:
            response = service.juridical_query(query)
            
            print(f"   Método: {response['method']}")
            print(f"   Sucesso: {response['success']}")
            print(f"   Resposta: {response['response'][:100]}...")
            
            if response.get('chunks_used', 0) > 0:
                print(f"   Chunks utilizados: {response['chunks_used']}")
            
            if response.get('sources'):
                print(f"   Fontes: {len(response['sources'])} documentos")
                
        except Exception as e:
            print(f"   ❌ Erro: {e}")


def demo_document_management():
    """Demonstração de gestão de documentos."""
    print("\n" + "=" * 60)
    print("DEMO: Gestão de Documentos RAG")
    print("=" * 60)
    
    service = EnhancedJuridicalService()
    
    # Documentos de exemplo (simulados)
    example_docs = [
        {
            "file_path": "/docs/codigo_defesa_consumidor.pdf",
            "doc_type": "lei",
            "metadata": {
                "titulo": "Código de Defesa do Consumidor",
                "numero": "8.078/90",
                "categoria": "direito_consumidor"
            }
        },
        {
            "file_path": "/docs/codigo_civil.pdf",
            "doc_type": "codigo",
            "metadata": {
                "titulo": "Código Civil",
                "numero": "10.406/02",
                "categoria": "direito_civil"
            }
        }
    ]
    
    print("\n📚 Simulando Adição de Documentos:")
    print("-" * 40)
    
    for doc in example_docs:
        print(f"\n📄 Documento: {doc['metadata']['titulo']}")
        
        # Simular adição (na prática você passaria o caminho real)
        success = service.add_document_to_rag(
            file_path=doc["file_path"],
            doc_type=doc["doc_type"],
            metadata=doc["metadata"]
        )
        
        if success:
            print("   ✅ Adicionado com sucesso")
        else:
            print("   ⚠️ Não foi possível adicionar (RAG não disponível)")


def demo_advanced_features():
    """Demonstração de recursos avançados."""
    print("\n" + "=" * 60)
    print("DEMO: Recursos Avançados")
    print("=" * 60)
    
    # Verificar dependências RAG
    rag_available = check_rag_availability()
    print(f"\n🔧 RAG Disponível: {rag_available}")
    
    if rag_available:
        try:
            from rag.rag_manager import JuridicalRAGManager
            from rag.utils import RAGUtils
            
            print("\n🧮 Testando Componentes RAG:")
            print("-" * 30)
            
            # Testar utils
            utils = RAGUtils()
            print("✅ RAGUtils inicializado")
            
            # Testar chunking
            sample_text = """
            Art. 6º São direitos básicos do consumidor:
            I - a proteção da vida, saúde e segurança contra os riscos provocados por práticas no fornecimento de produtos e serviços considerados perigosos ou nocivos;
            II - a educação e divulgação sobre o consumo adequado dos produtos e serviços, asseguradas a liberdade de escolha e a igualdade nas contratações;
            """
            
            chunks = utils.chunk_juridical_document(sample_text, doc_type="lei")
            print(f"✅ Chunking: {len(chunks)} chunks criados")
            
            # Testar RAG Manager
            rag_manager = JuridicalRAGManager()
            print("✅ RAGManager inicializado")
            
            print("\n🎯 Componentes RAG funcionando corretamente!")
            
        except Exception as e:
            print(f"❌ Erro nos componentes RAG: {e}")
    else:
        print("\n💡 Para ativar RAG, execute:")
        print("   pip install -r requirements_rag.txt")


def main():
    """Função principal - executa todas as demonstrações."""
    print("🚀 Iniciando demonstração de integração RAG + MCP")
    
    # Executar demos
    demo_basic_usage()
    demo_document_management() 
    demo_advanced_features()
    
    print("\n" + "=" * 60)
    print("✅ Demonstração concluída!")
    print("=" * 60)
    
    print("\n📝 Próximos passos:")
    print("1. Instalar dependências RAG se necessário")
    print("2. Adicionar documentos jurídicos ao índice")
    print("3. Testar consultas com contexto real")
    print("4. Configurar logs de produção")
    print("5. Monitorar performance e ajustar parâmetros")


if __name__ == "__main__":
    main()
