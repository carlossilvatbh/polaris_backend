"""
RAG Utils - Utilitários para processamento RAG
Funções auxiliares para chunking, validação e formatação
"""

import os
import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class RAGUtils:
    """Utilitários para processamento RAG jurídico"""
    
    # Padrões jurídicos para chunking inteligente
    JURIDICAL_SEPARATORS = [
        r'\bArt\.?\s*\d+',           # Artigos (Art. 1, Art 2)
        r'\bArtigo\s+\d+',          # Artigo 1, Artigo 2
        r'\bSeção\s+[IVX]+',        # Seção I, Seção II
        r'\bCapítulo\s+[IVX]+',     # Capítulo I, Capítulo II
        r'\b§\s*\d+',               # Parágrafos (§ 1, § 2)
        r'\bInciso\s+[IVX]+',       # Inciso I, Inciso II
        r'\bAlínea\s+[a-z]\)',      # Alínea a), Alínea b)
        r'\n\n+',                   # Quebras de parágrafo
    ]
    
    SUPPORTED_EXTENSIONS = {'.pdf', '.docx', '.doc', '.txt'}
    
    @staticmethod
    def validate_file_path(file_path: str) -> Tuple[bool, str]:
        """
        Valida se o arquivo é suportado e existe
        
        Args:
            file_path: Caminho para o arquivo
        
        Returns:
            Tuple[bool, str]: (é_válido, mensagem)
        """
        try:
            path = Path(file_path)
            
            if not path.exists():
                return False, f"Arquivo não encontrado: {file_path}"
            
            if path.suffix.lower() not in RAGUtils.SUPPORTED_EXTENSIONS:
                return False, f"Extensão não suportada: {path.suffix}"
            
            if path.stat().st_size == 0:
                return False, f"Arquivo vazio: {file_path}"
            
            return True, "Arquivo válido"
            
        except Exception as e:
            return False, f"Erro ao validar arquivo: {str(e)}"
    
    @staticmethod
    def validate_file(file_path: str) -> bool:
        """
        Valida se arquivo existe e tem extensão suportada.
        Versão simplificada de validate_file_path para compatibilidade.
        
        Args:
            file_path: Caminho para o arquivo
            
        Returns:
            True se arquivo é válido
        """
        is_valid, _ = RAGUtils.validate_file_path(file_path)
        return is_valid
    
    @staticmethod
    def intelligent_chunk_text(text: str, 
                              max_chunk_size: int = 1000,
                              overlap_size: int = 200) -> List[Dict[str, Any]]:
        """
        Chunking inteligente para documentos jurídicos
        
        Args:
            text: Texto para dividir
            max_chunk_size: Tamanho máximo do chunk
            overlap_size: Sobreposição entre chunks
        
        Returns:
            List[Dict]: Lista de chunks com metadados
        """
        chunks = []
        
        try:
            # Primeiro, tenta dividir por separadores jurídicos
            juridical_chunks = RAGUtils._split_by_juridical_patterns(text)
            
            # Se não encontrou padrões jurídicos, usa divisão por parágrafos
            if len(juridical_chunks) <= 1:
                juridical_chunks = text.split('\n\n')
            
            current_chunk = ""
            chunk_index = 0
            
            for section in juridical_chunks:
                section = section.strip()
                if not section:
                    continue
                
                # Se adicionar esta seção não ultrapassar o limite
                if len(current_chunk + section) <= max_chunk_size:
                    current_chunk += ("\n\n" if current_chunk else "") + section
                else:
                    # Salva o chunk atual se não estiver vazio
                    if current_chunk:
                        chunks.append({
                            'text': current_chunk.strip(),
                            'chunk_id': chunk_index,
                            'char_count': len(current_chunk),
                            'type': RAGUtils._identify_chunk_type(current_chunk)
                        })
                        chunk_index += 1
                    
                    # Inicia novo chunk
                    current_chunk = section
            
            # Adiciona o último chunk
            if current_chunk:
                chunks.append({
                    'text': current_chunk.strip(),
                    'chunk_id': chunk_index,
                    'char_count': len(current_chunk),
                    'type': RAGUtils._identify_chunk_type(current_chunk)
                })
            
            # Adiciona sobreposição entre chunks
            chunks = RAGUtils._add_overlap(chunks, overlap_size)
            
            logger.info(f"Texto dividido em {len(chunks)} chunks")
            return chunks
            
        except Exception as e:
            logger.error(f"Erro no chunking: {str(e)}")
            # Fallback: divisão simples
            return RAGUtils._simple_chunk_fallback(text, max_chunk_size)
    
    @staticmethod
    def chunk_juridical_document(text: str, 
                                doc_type: str = "lei",
                                chunk_size: int = 500,
                                chunk_overlap: int = 50) -> List[Dict]:
        """
        Aplica chunking jurídico inteligente em texto.
        Interface compatível com testes.
        
        Args:
            text: Texto a ser processado
            doc_type: Tipo do documento
            chunk_size: Tamanho máximo do chunk
            chunk_overlap: Sobreposição entre chunks
            
        Returns:
            Lista de chunks com metadados
        """
        chunks = RAGUtils.intelligent_chunk_text(
            text=text,
            max_chunk_size=chunk_size,
            overlap_size=chunk_overlap
        )
        
        # Adicionar tipo de documento aos metadados
        for chunk in chunks:
            if 'metadata' not in chunk:
                chunk['metadata'] = {}
            chunk['metadata']['doc_type'] = doc_type
            
        return chunks
    
    @staticmethod
    def _split_by_juridical_patterns(text: str) -> List[str]:
        """Divide texto usando padrões jurídicos"""
        # Combina todos os padrões em uma regex
        pattern = '|'.join(f'({pattern})' for pattern in RAGUtils.JURIDICAL_SEPARATORS)
        
        # Encontra todas as posições dos separadores
        matches = list(re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE))
        
        if not matches:
            return [text]
        
        chunks = []
        start = 0
        
        for match in matches:
            # Adiciona o texto antes do separador
            if match.start() > start:
                chunk = text[start:match.start()].strip()
                if chunk:
                    chunks.append(chunk)
            
            start = match.start()
        
        # Adiciona o último chunk
        final_chunk = text[start:].strip()
        if final_chunk:
            chunks.append(final_chunk)
        
        return chunks
    
    @staticmethod
    def _identify_chunk_type(text: str) -> str:
        """Identifica o tipo de chunk baseado no conteúdo"""
        text_lower = text.lower()
        
        if re.search(r'\bart\.?\s*\d+', text_lower):
            return 'artigo'
        elif re.search(r'\bseção\s+[ivx]+', text_lower):
            return 'secao'
        elif re.search(r'\bcapítulo\s+[ivx]+', text_lower):
            return 'capitulo'
        elif re.search(r'\b§\s*\d+', text_lower):
            return 'paragrafo'
        elif re.search(r'\binciso\s+[ivx]+', text_lower):
            return 'inciso'
        else:
            return 'paragrafo_comum'
    
    @staticmethod
    def _add_overlap(chunks: List[Dict], overlap_size: int) -> List[Dict]:
        """Adiciona sobreposição entre chunks consecutivos"""
        if len(chunks) <= 1 or overlap_size <= 0:
            return chunks
        
        overlapped_chunks = []
        
        for i, chunk in enumerate(chunks):
            new_chunk = chunk.copy()
            
            # Adiciona overlap do chunk anterior
            if i > 0:
                prev_text = chunks[i-1]['text']
                overlap_text = prev_text[-overlap_size:] if len(prev_text) > overlap_size else prev_text
                new_chunk['text'] = overlap_text + "\n\n" + new_chunk['text']
            
            # Adiciona overlap do próximo chunk
            if i < len(chunks) - 1:
                next_text = chunks[i+1]['text']
                overlap_text = next_text[:overlap_size] if len(next_text) > overlap_size else next_text
                new_chunk['text'] = new_chunk['text'] + "\n\n" + overlap_text
            
            overlapped_chunks.append(new_chunk)
        
        return overlapped_chunks
    
    @staticmethod
    def _simple_chunk_fallback(text: str, max_size: int) -> List[Dict]:
        """Fallback para chunking simples em caso de erro"""
        chunks = []
        words = text.split()
        current_chunk = []
        current_size = 0
        chunk_index = 0
        
        for word in words:
            if current_size + len(word) + 1 > max_size and current_chunk:
                chunk_text = ' '.join(current_chunk)
                chunks.append({
                    'text': chunk_text,
                    'chunk_id': chunk_index,
                    'char_count': len(chunk_text),
                    'type': 'fallback'
                })
                chunk_index += 1
                current_chunk = [word]
                current_size = len(word)
            else:
                current_chunk.append(word)
                current_size += len(word) + 1
        
        # Adiciona o último chunk
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunks.append({
                'text': chunk_text,
                'chunk_id': chunk_index,
                'char_count': len(chunk_text),
                'type': 'fallback'
            })
        
        return chunks
    
    @staticmethod
    def format_context_for_claude(relevant_docs: List[Dict], 
                                 query: str,
                                 max_context_length: int = 4000) -> str:
        """
        Formata contexto otimizado para Claude AI
        
        Args:
            relevant_docs: Documentos relevantes encontrados
            query: Consulta original
            max_context_length: Tamanho máximo do contexto
        
        Returns:
            str: Contexto formatado para Claude
        """
        if not relevant_docs:
            return f"""
CONSULTA JURÍDICA: {query}

CONTEXTO: Nenhum documento relevante encontrado no banco de dados.
Por favor, responda baseado no seu conhecimento jurídico geral.
"""
        
        # Ordena por relevância (score)
        sorted_docs = sorted(relevant_docs, 
                           key=lambda x: x.get('score', 0), 
                           reverse=True)
        
        context_parts = [
            "=== CONTEXTO JURÍDICO RELEVANTE ===\n"
        ]
        
        current_length = len(context_parts[0])
        doc_count = 0
        
        for doc in sorted_docs:
            # Formata cada documento
            doc_text = f"""
DOCUMENTO {doc_count + 1}: {doc.get('source', 'Fonte não identificada')}
Relevância: {doc.get('score', 0):.2f}
Tipo: {doc.get('type', 'N/A')}

CONTEÚDO:
{doc.get('text', 'Texto não disponível')}

---
"""
            
            # Verifica se ainda cabe no limite
            if current_length + len(doc_text) > max_context_length:
                if doc_count == 0:  # Pelo menos um documento deve ser incluído
                    # Trunca o primeiro documento para caber
                    available_space = max_context_length - current_length - 100
                    if available_space > 0:
                        truncated_text = doc.get('text', '')[:available_space] + "...[TRUNCADO]"
                        doc_text = f"""
DOCUMENTO 1: {doc.get('source', 'Fonte não identificada')}
Relevância: {doc.get('score', 0):.2f}
Tipo: {doc.get('type', 'N/A')}

CONTEÚDO:
{truncated_text}

---
"""
                        context_parts.append(doc_text)
                        doc_count += 1
                break
            
            context_parts.append(doc_text)
            current_length += len(doc_text)
            doc_count += 1
        
        # Adiciona instruções finais
        context_parts.append(f"""
=== CONSULTA ===
{query}

=== INSTRUÇÕES PARA ANÁLISE ===
1. Analise os documentos fornecidos acima
2. Cite especificamente as fontes relevantes
3. Se aplicável, mencione artigos, parágrafos ou seções específicas
4. Forneça uma resposta fundamentada no contexto jurídico
5. Se o contexto for insuficiente, indique claramente

RESPOSTA:
""")
        
        return ''.join(context_parts)
    
    @staticmethod
    def extract_metadata_from_path(file_path: str) -> Dict[str, Any]:
        """Extrai metadados do caminho do arquivo"""
        path = Path(file_path)
        
        return {
            'filename': path.name,
            'extension': path.suffix.lower(),
            'size_bytes': path.stat().st_size if path.exists() else 0,
            'absolute_path': str(path.absolute()),
            'parent_directory': path.parent.name
        }
    
    @staticmethod
    def clean_text(text: str) -> str:
        """Limpa e normaliza texto"""
        if not text:
            return ""
        
        # Remove caracteres especiais desnecessários
        text = re.sub(r'\x00-\x1f\x7f-\x9f', '', text)  # Remove controle chars
        
        # Normaliza espaços em branco
        text = re.sub(r'\s+', ' ', text)
        
        # Remove espaços no início e fim
        text = text.strip()
        
        return text
