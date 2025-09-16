"""
RAG Manager - Core do sistema RAG jurídico
Gerencia embeddings, vector store e busca semântica
"""

import json
import logging
from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime

# Imports seguros com fallback
try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

from .document_processor import DocumentProcessor
from .utils import RAGUtils

logger = logging.getLogger(__name__)


class JuridicalRAGManager:
    """Gerenciador principal do sistema RAG jurídico"""
    
    def __init__(self, 
                 chroma_db_path: str = "./chroma_db",
                 collection_name: str = "juridical_documents",
                 embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"):
        """
        Inicializa o RAG Manager
        
        Args:
            chroma_db_path: Caminho para o banco vetorial
            collection_name: Nome da coleção
            embedding_model: Modelo de embeddings
        """
        self.chroma_db_path = Path(chroma_db_path)
        self.collection_name = collection_name
        self.embedding_model_name = embedding_model
        
        # Verifica dependências
        self.rag_available = self._check_dependencies()
        
        if not self.rag_available:
            logger.warning("RAG não está totalmente funcional. Verifique dependências.")
            self.client = None
            self.collection = None
            self.embedding_model = None
            return
        
        # Inicializa componentes
        try:
            self.document_processor = DocumentProcessor()
            self.client = self._init_chromadb()
            self.collection = self._init_collection()
            self.embedding_model = self._init_embedding_model()
            
            logger.info("RAG Manager inicializado com sucesso")
            logger.info(f"Banco vetorial: {self.chroma_db_path}")
            logger.info(f"Modelo de embeddings: {self.embedding_model_name}")
            
        except Exception as e:
            logger.error(f"Erro ao inicializar RAG Manager: {str(e)}")
            self.rag_available = False
            self.client = None
            self.collection = None
            self.embedding_model = None
    
    def _check_dependencies(self) -> bool:
        """Verifica se todas as dependências estão disponíveis"""
        if not CHROMADB_AVAILABLE:
            logger.error("ChromaDB não está instalado")
            return False
        
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            logger.error("sentence-transformers não está instalado")
            return False
        
        return True
    
    def _init_chromadb(self):
        """Inicializa cliente ChromaDB"""
        try:
            # Cria diretório se não existir
            self.chroma_db_path.mkdir(parents=True, exist_ok=True)
            
            # Configurações do ChromaDB
            settings = Settings(
                chroma_db_impl="duckdb+parquet",
                persist_directory=str(self.chroma_db_path),
                anonymized_telemetry=False
            )
            
            client = chromadb.Client(settings)
            logger.info("ChromaDB inicializado com sucesso")
            return client
            
        except Exception as e:
            logger.error(f"Erro ao inicializar ChromaDB: {str(e)}")
            raise
    
    def _init_collection(self):
        """Inicializa ou carrega coleção"""
        try:
            # Tenta carregar coleção existente
            try:
                collection = self.client.get_collection(
                    name=self.collection_name)
                logger.info(f"Coleção '{self.collection_name}' carregada")
            except Exception:
                # Cria nova coleção
                collection = self.client.create_collection(
                    name=self.collection_name,
                    metadata={
                        "description": "Documentos jurídicos processados pelo POLARIS"
                    }
                )
                logger.info(f"Nova coleção '{self.collection_name}' criada")
            
            return collection
            
        except Exception as e:
            logger.error(f"Erro ao inicializar coleção: {str(e)}")
            raise
    
    def _init_embedding_model(self):
        """Inicializa modelo de embeddings"""
        try:
            model = SentenceTransformer(self.embedding_model_name)
            logger.info(f"Modelo de embeddings carregado: {self.embedding_model_name}")
            return model
            
        except Exception as e:
            logger.error(f"Erro ao carregar modelo de embeddings: {str(e)}")
            # Fallback para modelo mais simples
            try:
                model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.warning("Usando modelo fallback: all-MiniLM-L6-v2")
                return model
            except Exception as fallback_error:
                raise Exception(
                    f"Não foi possível carregar modelo: {str(fallback_error)}"
                )
    
    def add_documents(self, file_paths: List[str]) -> Dict[str, Any]:
        """
        Adiciona documentos ao banco vetorial
        
        Args:
            file_paths: Lista de caminhos para arquivos
        
        Returns:
            Dict com resultados do processamento
        """
        if not self.rag_available:
            return {
                'success': False,
                'error': 'RAG não está disponível',
                'processed_documents': 0,
                'total_chunks': 0
            }
        
        try:
            # Processa documentos
            processing_result = self.document_processor.process_multiple_documents(file_paths)
            
            if not processing_result['successful']:
                return {
                    'success': False,
                    'error': 'Nenhum documento foi processado com sucesso',
                    'failed_files': processing_result['failed'],
                    'processed_documents': 0,
                    'total_chunks': 0
                }
            
            # Prepara dados para inserção no ChromaDB
            all_chunks = []
            all_embeddings = []
            all_metadatas = []
            all_ids = []
            
            for doc_result in processing_result['successful']:
                chunks = doc_result['chunks']
                source_file = doc_result['source_file']
                
                for chunk in chunks:
                    # Texto do chunk
                    chunk_text = chunk['text']
                    all_chunks.append(chunk_text)
                    
                    # Gera embedding
                    embedding = self.embedding_model.encode(chunk_text).tolist()
                    all_embeddings.append(embedding)
                    
                    # Metadados
                    metadata = {
                        'source_file': source_file,
                        'chunk_id': chunk['chunk_id'],
                        'chunk_type': chunk['type'],
                        'char_count': chunk['char_count'],
                        'word_count': len(chunk_text.split()),
                        'processed_at': datetime.now().isoformat(),
                        'file_metadata': json.dumps(chunk['document_metadata'])
                    }
                    all_metadatas.append(metadata)
                    
                    # ID único
                    chunk_id = f"{source_file}_{chunk['chunk_id']}_{datetime.now().timestamp()}"
                    all_ids.append(chunk_id)
            
            # Insere no ChromaDB
            self.collection.add(
                embeddings=all_embeddings,
                documents=all_chunks,
                metadatas=all_metadatas,
                ids=all_ids
            )
            
            # Persiste dados
            self.client.persist()
            
            result = {
                'success': True,
                'processed_documents': len(processing_result['successful']),
                'total_chunks': len(all_chunks),
                'failed_files': processing_result['failed'],
                'processing_summary': processing_result['processing_summary']
            }
            
            logger.info(f"Documentos adicionados ao RAG: {result}")
            return result
            
        except Exception as e:
            error_msg = f"Erro ao adicionar documentos ao RAG: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'processed_documents': 0,
                'total_chunks': 0
            }
    
    def search_relevant_docs(self, 
                           query: str, 
                           k: int = 5,
                           score_threshold: float = 0.5) -> List[Dict[str, Any]]:
        """
        Busca documentos relevantes para uma consulta
        
        Args:
            query: Consulta jurídica
            k: Número máximo de resultados
            score_threshold: Threshold mínimo de relevância
        
        Returns:
            Lista de documentos relevantes
        """
        if not self.rag_available:
            logger.warning("RAG não disponível para busca")
            return []
        
        try:
            # Gera embedding da consulta
            query_embedding = self.embedding_model.encode(query).tolist()
            
            # Busca no ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=k,
                include=['documents', 'metadatas', 'distances']
            )
            
            # Processa resultados
            relevant_docs = []
            
            if results['documents'] and results['documents'][0]:
                documents = results['documents'][0]
                metadatas = results['metadatas'][0]
                distances = results['distances'][0]
                
                for i, (doc, metadata, distance) in enumerate(zip(documents, metadatas, distances)):
                    # Converte distância para score (quanto menor a distância, maior o score)
                    score = 1.0 / (1.0 + distance)
                    
                    # Filtra por threshold
                    if score >= score_threshold:
                        relevant_docs.append({
                            'text': doc,
                            'score': score,
                            'distance': distance,
                            'source': metadata.get('source_file', 'Desconhecido'),
                            'type': metadata.get('chunk_type', 'N/A'),
                            'chunk_id': metadata.get('chunk_id', 0),
                            'char_count': metadata.get('char_count', 0),
                            'metadata': metadata,
                            'rank': i + 1
                        })
            
            logger.info(f"Busca realizada: '{query[:50]}...' - {len(relevant_docs)} resultados relevantes")
            return relevant_docs
            
        except Exception as e:
            logger.error(f"Erro na busca RAG: {str(e)}")
            return []
    
    def prepare_context_for_claude(self, 
                                 query: str,
                                 max_docs: int = 5,
                                 max_context_length: int = 4000) -> Dict[str, Any]:
        """
        Prepara contexto enriquecido para envio ao Claude
        
        Args:
            query: Consulta jurídica
            max_docs: Número máximo de documentos para incluir
            max_context_length: Tamanho máximo do contexto
        
        Returns:
            Dict com prompt enriquecido e metadados
        """
        try:
            # Busca documentos relevantes
            relevant_docs = self.search_relevant_docs(query, k=max_docs)
            
            # Formata contexto
            if relevant_docs:
                formatted_context = RAGUtils.format_context_for_claude(
                    relevant_docs, 
                    query, 
                    max_context_length
                )
                
                return {
                    'success': True,
                    'enhanced_prompt': formatted_context,
                    'original_query': query,
                    'relevant_docs_count': len(relevant_docs),
                    'max_relevance_score': max(doc['score'] for doc in relevant_docs),
                    'sources': [doc['source'] for doc in relevant_docs],
                    'rag_enabled': True
                }
            else:
                # Fallback sem contexto RAG
                fallback_prompt = f"""
CONSULTA JURÍDICA: {query}

CONTEXTO: Nenhum documento relevante encontrado no banco de conhecimento.
Por favor, responda baseado no seu conhecimento jurídico geral.

RESPOSTA:
"""
                return {
                    'success': True,
                    'enhanced_prompt': fallback_prompt,
                    'original_query': query,
                    'relevant_docs_count': 0,
                    'max_relevance_score': 0,
                    'sources': [],
                    'rag_enabled': False,
                    'fallback_reason': 'Nenhum documento relevante encontrado'
                }
                
        except Exception as e:
            error_msg = f"Erro ao preparar contexto: {str(e)}"
            logger.error(error_msg)
            
            # Fallback em caso de erro
            return {
                'success': False,
                'enhanced_prompt': f"CONSULTA: {query}\n\nERRO RAG: {error_msg}",
                'original_query': query,
                'relevant_docs_count': 0,
                'max_relevance_score': 0,
                'sources': [],
                'rag_enabled': False,
                'error': error_msg
            }
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas da coleção"""
        if not self.rag_available or not self.collection:
            return {
                'rag_available': False,
                'total_chunks': 0,
                'error': 'RAG não disponível'
            }
        
        try:
            count = self.collection.count()
            
            # Tenta obter algumas amostras para análise
            sample_size = min(10, count) if count > 0 else 0
            
            stats = {
                'rag_available': True,
                'total_chunks': count,
                'collection_name': self.collection_name,
                'db_path': str(self.chroma_db_path),
                'embedding_model': self.embedding_model_name,
                'sample_size': sample_size
            }
            
            if sample_size > 0:
                # Obtém amostra para estatísticas
                sample = self.collection.peek(limit=sample_size)
                if sample['metadatas']:
                    sources = set()
                    chunk_types = {}
                    
                    for metadata in sample['metadatas']:
                        if 'source_file' in metadata:
                            sources.add(metadata['source_file'])
                        
                        chunk_type = metadata.get('chunk_type', 'unknown')
                        chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1
                    
                    stats.update({
                        'unique_sources': len(sources),
                        'source_files': list(sources),
                        'chunk_type_distribution': chunk_types
                    })
            
            return stats
            
        except Exception as e:
            return {
                'rag_available': False,
                'total_chunks': 0,
                'error': str(e)
            }
    
    def clear_collection(self) -> Dict[str, Any]:
        """Limpa todos os documentos da coleção"""
        if not self.rag_available:
            return {
                'success': False,
                'error': 'RAG não disponível'
            }
        
        try:
            # Obtém todos os IDs
            all_data = self.collection.get()
            
            if all_data['ids']:
                # Remove todos os documentos
                self.collection.delete(ids=all_data['ids'])
                self.client.persist()
                
                logger.info(f"Coleção '{self.collection_name}' limpa - {len(all_data['ids'])} chunks removidos")
                
                return {
                    'success': True,
                    'removed_chunks': len(all_data['ids'])
                }
            else:
                return {
                    'success': True,
                    'removed_chunks': 0,
                    'message': 'Coleção já estava vazia'
                }
                
        except Exception as e:
            error_msg = f"Erro ao limpar coleção: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
    
    def is_available(self) -> bool:
        """Verifica se o RAG está disponível"""
        return self.rag_available
    
    def get_dependencies_status(self) -> Dict[str, bool]:
        """Retorna status das dependências"""
        return {
            'chromadb': CHROMADB_AVAILABLE,
            'sentence_transformers': SENTENCE_TRANSFORMERS_AVAILABLE,
            'document_processor': True,
            'rag_manager': self.rag_available
        }
