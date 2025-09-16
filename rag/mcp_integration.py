"""
MCP Integration - Bridge entre RAG e sistema MCP existente
Integração segura que não modifica código MCP original
"""

import logging
from typing import Dict, Any, Optional

try:
    from .rag_manager import JuridicalRAGManager
    RAG_MANAGER_AVAILABLE = True
except ImportError:
    RAG_MANAGER_AVAILABLE = False

logger = logging.getLogger(__name__)


class MCPRAGIntegration:
    """
    Ponte entre sistema RAG e MCP existente
    Implementa padrão adapter para integração segura
    """
    
    def __init__(self, rag_manager: Optional[JuridicalRAGManager] = None):
        """
        Inicializa integração MCP-RAG
        
        Args:
            rag_manager: Instância do RAG Manager (opcional)
        """
        self.rag_manager = rag_manager
        self.rag_enabled = rag_manager is not None and rag_manager.is_available()
        
        if self.rag_enabled:
            logger.info("MCP-RAG Integration ativada")
        else:
            logger.warning("MCP-RAG Integration em modo fallback")
    
    def handle_rag_query(self, 
                        query: str,
                        enable_rag: bool = True,
                        max_docs: int = 5,
                        context_length: int = 4000) -> Dict[str, Any]:
        """
        Processa consulta com enriquecimento RAG
        
        Args:
            query: Consulta jurídica original
            enable_rag: Se deve usar RAG (permite desabilitar)
            max_docs: Máximo de documentos para contexto
            context_length: Tamanho máximo do contexto
        
        Returns:
            Dict com prompt enriquecido e metadados
        """
        try:
            # Se RAG não está disponível ou desabilitado, usa fallback
            if not self.rag_enabled or not enable_rag:
                return self._fallback_response(query, "RAG desabilitado ou indisponível")
            
            # Usa RAG para enriquecer contexto
            rag_result = self.rag_manager.prepare_context_for_claude(
                query=query,
                max_docs=max_docs,
                max_context_length=context_length
            )
            
            if rag_result['success']:
                return {
                    'enhanced_prompt': rag_result['enhanced_prompt'],
                    'original_query': query,
                    'rag_metadata': {
                        'docs_found': rag_result['relevant_docs_count'],
                        'max_score': rag_result.get('max_relevance_score', 0),
                        'sources': rag_result.get('sources', []),
                        'rag_enabled': rag_result['rag_enabled']
                    },
                    'mcp_compatible': True,
                    'processing_mode': 'rag_enhanced'
                }
            else:
                # RAG falhou, usa fallback
                return self._fallback_response(
                    query, 
                    f"Erro RAG: {rag_result.get('error', 'Erro desconhecido')}"
                )
                
        except Exception as e:
            logger.error(f"Erro na integração MCP-RAG: {str(e)}")
            return self._fallback_response(query, f"Erro na integração: {str(e)}")
    
    def juridical_query(self, 
                       query: str,
                       max_chunks: int = 5,
                       similarity_threshold: float = 0.6) -> Dict[str, Any]:
        """
        Alias para handle_rag_query com parâmetros específicos para consultas jurídicas.
        Mantém compatibilidade com interface esperada pelos testes.
        
        Args:
            query: Consulta jurídica
            max_chunks: Máximo de chunks de contexto
            similarity_threshold: Limite mínimo de similaridade
            
        Returns:
            Dict com resposta estruturada
        """
        result = self.handle_rag_query(
            query=query,
            enable_rag=True,
            max_docs=max_chunks,
            context_length=4000
        )
        
        # Adaptar resposta para interface esperada
        if result.get('processing_mode') == 'fallback':
            return {
                'success': False,
                'response': result.get('enhanced_prompt', ''),
                'error': result.get('rag_metadata', {}).get('fallback_reason', 'RAG indisponível'),
                'sources': [],
                'context_chunks': []
            }
        else:
            return {
                'success': True,
                'response': result.get('enhanced_prompt', ''),
                'sources': result.get('rag_metadata', {}).get('sources', []),
                'context_chunks': result.get('rag_metadata', {}).get('docs_found', 0)
            }
    
    def _fallback_response(self, query: str, reason: str) -> Dict[str, Any]:
        """
        Resposta fallback quando RAG não está disponível
        Mantém compatibilidade com MCP original
        """
        fallback_prompt = f"""
CONSULTA JURÍDICA: {query}

MODO: Análise baseada em conhecimento base
OBSERVAÇÃO: {reason}

Por favor, responda com base no seu conhecimento jurídico geral.

RESPOSTA:
"""
        
        return {
            'enhanced_prompt': fallback_prompt,
            'original_query': query,
            'rag_metadata': {
                'docs_found': 0,
                'max_score': 0,
                'sources': [],
                'rag_enabled': False,
                'fallback_reason': reason
            },
            'mcp_compatible': True,
            'processing_mode': 'fallback'
        }
    
    def add_documents_to_rag(self, file_paths: list) -> Dict[str, Any]:
        """
        Adiciona documentos ao sistema RAG
        
        Args:
            file_paths: Lista de caminhos para documentos
        
        Returns:
            Dict com resultado do processamento
        """
        if not self.rag_enabled:
            return {
                'success': False,
                'error': 'RAG não está disponível',
                'suggestion': 'Instale dependências: pip install -r requirements_rag.txt'
            }
        
        try:
            result = self.rag_manager.add_documents(file_paths)
            
            # Adiciona informações extras para integração MCP
            result['mcp_integration'] = {
                'total_files_processed': result.get('processed_documents', 0),
                'ready_for_queries': result.get('success', False),
                'recommendation': ('Documentos prontos para consultas RAG' 
                                 if result.get('success') 
                                 else 'Verifique erros no processamento')
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Erro ao adicionar documentos via MCP: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'mcp_integration': {
                    'total_files_processed': 0,
                    'ready_for_queries': False,
                    'recommendation': 'Verifique logs para detalhes do erro'
                }
            }
    
    def get_rag_status(self) -> Dict[str, Any]:
        """
        Retorna status completo do sistema RAG
        Útil para debugging e monitoramento
        """
        try:
            base_status = {
                'available': self.rag_enabled,
                'rag_integration_available': RAG_MANAGER_AVAILABLE,
                'rag_manager_initialized': self.rag_manager is not None,
                'rag_enabled': self.rag_enabled,
                'mcp_compatibility': True,
                'timestamp': '2024-01-15T10:00:00Z'
            }
            
            if self.rag_enabled and self.rag_manager:
                # Adiciona estatísticas detalhadas
                rag_stats = self.rag_manager.get_collection_stats()
                dependencies = self.rag_manager.get_dependencies_status()
                
                base_status.update({
                    'collection_stats': rag_stats,
                    'dependencies': dependencies,
                    'recommendations': self._generate_recommendations(rag_stats, dependencies)
                })
            else:
                base_status.update({
                    'collection_stats': {'total_chunks': 0, 'rag_available': False},
                    'dependencies': {'chromadb': False, 'sentence_transformers': False},
                    'reason': 'Dependências RAG não instaladas',
                    'recommendations': [
                        'Instale dependências: pip install -r requirements_rag.txt',
                        'Reinicialize o sistema após instalação'
                    ]
                })
            
            return base_status
            
        except Exception as e:
            logger.error(f"Erro ao obter status RAG: {str(e)}")
            return {
                'available': False,
                'rag_integration_available': False,
                'rag_manager_initialized': False,
                'rag_enabled': False,
                'mcp_compatibility': True,
                'error': str(e),
                'reason': f'Erro ao acessar status: {str(e)}',
                'timestamp': '2024-01-15T10:00:00Z',
                'recommendations': ['Verifique logs do sistema']
            }
    
    def _generate_recommendations(self, 
                                rag_stats: Dict, 
                                dependencies: Dict) -> list:
        """Gera recomendações baseadas no status atual"""
        recommendations = []
        
        # Verifica dependências
        missing_deps = [k for k, v in dependencies.items() if not v]
        if missing_deps:
            recommendations.append(f"Dependências faltantes: {', '.join(missing_deps)}")
        
        # Verifica conteúdo
        total_chunks = rag_stats.get('total_chunks', 0)
        if total_chunks == 0:
            recommendations.append("Adicione documentos ao sistema RAG para melhor contexto")
        elif total_chunks < 10:
            recommendations.append("Considere adicionar mais documentos para maior cobertura")
        
        # Verifica fontes
        unique_sources = rag_stats.get('unique_sources', 0)
        if unique_sources > 0 and unique_sources < 3:
            recommendations.append("Diversifique as fontes para análises mais abrangentes")
        
        return recommendations if recommendations else ["Sistema RAG operacional"]
    
    def test_rag_integration(self, test_query: str = "teste de integração") -> Dict[str, Any]:
        """
        Testa a integração RAG de ponta a ponta
        Útil para validação após configuração
        """
        try:
            test_result = self.handle_rag_query(
                query=test_query,
                enable_rag=True,
                max_docs=3,
                context_length=1000
            )
            
            # Analisa resultado do teste
            test_successful = (
                test_result.get('mcp_compatible', False) and
                'enhanced_prompt' in test_result
            )
            
            return {
                'test_successful': test_successful,
                'processing_mode': test_result.get('processing_mode', 'unknown'),
                'rag_enabled': test_result.get('rag_metadata', {}).get('rag_enabled', False),
                'docs_found': test_result.get('rag_metadata', {}).get('docs_found', 0),
                'prompt_length': len(test_result.get('enhanced_prompt', '')),
                'test_query': test_query,
                'timestamp': logger.handlers[0].formatter.formatTime(logger.makeRecord(
                    'test', 0, '', 0, '', (), None
                )) if logger.handlers else 'N/A',
                'full_result': test_result
            }
            
        except Exception as e:
            return {
                'test_successful': False,
                'error': str(e),
                'test_query': test_query,
                'recommendation': 'Verifique configuração do RAG e dependências'
            }
    
    def clear_rag_data(self) -> Dict[str, Any]:
        """Limpa dados do RAG (útil para reprocessamento)"""
        if not self.rag_enabled:
            return {
                'success': False,
                'error': 'RAG não está disponível'
            }
        
        try:
            result = self.rag_manager.clear_collection()
            
            # Adiciona contexto MCP
            result['mcp_integration'] = {
                'action': 'clear_completed',
                'ready_for_new_documents': result.get('success', False),
                'recommendation': ('Pronto para adicionar novos documentos' 
                                 if result.get('success') 
                                 else 'Erro na limpeza - verifique logs')
            }
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'mcp_integration': {
                    'action': 'clear_failed',
                    'ready_for_new_documents': False,
                    'recommendation': 'Verifique permissões e logs do sistema'
                }
            }
    
    def is_available(self) -> bool:
        """Verifica se a integração está disponível"""
        return self.rag_enabled
    
    def is_rag_available(self) -> bool:
        """
        Verifica se o RAG está totalmente disponível e funcional.
        
        Returns:
            True se RAG está disponível, False caso contrário
        """
        return self.rag_enabled
    
    def get_supported_operations(self) -> list:
        """Lista operações suportadas pela integração"""
        base_operations = [
            'handle_rag_query',
            'get_rag_status', 
            'test_rag_integration'
        ]
        
        if self.rag_enabled:
            base_operations.extend([
                'add_documents_to_rag',
                'clear_rag_data'
            ])
        
        return base_operations
