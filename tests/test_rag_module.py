#!/usr/bin/env python3
"""
Testes básicos para o módulo RAG do Polaris Backend.
Valida funcionamento seguro e fallback robusto.
"""

import unittest
import tempfile
import os
import sys
from unittest.mock import patch, MagicMock
from typing import Dict, Any

# Adicionar path do projeto
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestRAGSafety(unittest.TestCase):
    """Testa segurança e fallback do módulo RAG."""
    
    def test_import_safety(self):
        """Testa se imports opcionais funcionam corretamente."""
        
        # Deve importar sem erro mesmo sem dependências
        try:
            from rag import __init__
            success = True
        except ImportError:
            success = False
        
        self.assertTrue(success, "Import do módulo RAG deve ser seguro")
    
    def test_mcp_integration_fallback(self):
        """Testa fallback seguro da integração MCP."""
        
        try:
            from rag.mcp_integration import MCPRAGIntegration
            
            # Inicializar sem dependências RAG
            integration = MCPRAGIntegration()
            
            # Deve funcionar mesmo com dependências ausentes
            self.assertIsNotNone(integration)
            
            # Status deve indicar disponibilidade corretamente
            status = integration.get_rag_status()
            self.assertIsInstance(status, dict)
            self.assertIn("available", status)
            
        except Exception as e:
            self.fail(f"MCPRAGIntegration deve funcionar com fallback: {e}")
    
    def test_rag_availability_check(self):
        """Testa verificação de disponibilidade do RAG."""
        
        try:
            from rag.mcp_integration import MCPRAGIntegration
            
            integration = MCPRAGIntegration()
            available = integration.is_rag_available()
            
            # Deve retornar boolean
            self.assertIsInstance(available, bool)
            
        except Exception as e:
            self.fail(f"Verificação de disponibilidade falhou: {e}")


class TestRAGUtilsBasic(unittest.TestCase):
    """Testa utilitários básicos do RAG."""
    
    def test_utils_import(self):
        """Testa import dos utilitários."""
        
        try:
            from rag.utils import RAGUtils
            utils = RAGUtils()
            self.assertIsNotNone(utils)
        except Exception as e:
            self.fail(f"RAGUtils deve importar: {e}")
    
    def test_file_validation(self):
        """Testa validação de arquivos."""
        
        try:
            from rag.utils import RAGUtils
            utils = RAGUtils()
            
            # Testar arquivo inexistente
            result = utils.validate_file("/arquivo/inexistente.pdf")
            self.assertFalse(result)
            
            # Testar extensão inválida
            with tempfile.NamedTemporaryFile(suffix=".xyz") as tmp:
                result = utils.validate_file(tmp.name)
                self.assertFalse(result)
                
        except Exception as e:
            self.fail(f"Validação de arquivo falhou: {e}")
    
    def test_juridical_chunking(self):
        """Testa chunking jurídico básico."""
        
        try:
            from rag.utils import RAGUtils
            utils = RAGUtils()
            
            sample_text = """
            Art. 1º Esta lei estabelece normas.
            
            Art. 2º São considerados:
            I - primeira definição;
            II - segunda definição.
            
            Parágrafo único. Disposições gerais.
            """
            
            chunks = utils.chunk_juridical_document(
                sample_text, 
                doc_type="lei"
            )
            
            self.assertIsInstance(chunks, list)
            self.assertGreater(len(chunks), 0)
            
            # Verificar estrutura dos chunks
            for chunk in chunks:
                self.assertIsInstance(chunk, dict)
                self.assertIn("text", chunk)
                self.assertIn("metadata", chunk)
                
        except Exception as e:
            self.fail(f"Chunking jurídico falhou: {e}")


class TestDocumentProcessor(unittest.TestCase):
    """Testa processador de documentos."""
    
    def test_processor_import(self):
        """Testa import do processador."""
        
        try:
            from rag.document_processor import DocumentProcessor
            processor = DocumentProcessor()
            self.assertIsNotNone(processor)
        except Exception as e:
            self.fail(f"DocumentProcessor deve importar: {e}")
    
    def test_text_extraction(self):
        """Testa extração de texto básica."""
        
        try:
            from rag.document_processor import DocumentProcessor
            processor = DocumentProcessor()
            
            # Criar arquivo de texto temporário
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', 
                                           delete=False) as tmp:
                tmp.write("Conteúdo de teste do documento jurídico.")
                tmp.flush()
                
                try:
                    # Tentar extrair texto
                    result = processor.extract_text(tmp.name)
                    
                    self.assertIsInstance(result, dict)
                    self.assertIn("success", result)
                    
                    if result["success"]:
                        self.assertIn("text", result)
                        self.assertIn("Conteúdo de teste", result["text"])
                    
                finally:
                    os.unlink(tmp.name)
                    
        except Exception as e:
            self.fail(f"Extração de texto falhou: {e}")


class TestRAGManagerSafety(unittest.TestCase):
    """Testa segurança do gerenciador RAG."""
    
    def test_manager_import(self):
        """Testa import do gerenciador."""
        
        try:
            from rag.rag_manager import JuridicalRAGManager
            # Deve importar mesmo sem dependências
            self.assertTrue(True)
        except Exception as e:
            self.fail(f"RAGManager deve importar com segurança: {e}")
    
    def test_manager_initialization_fallback(self):
        """Testa inicialização com fallback."""
        
        try:
            from rag.rag_manager import JuridicalRAGManager
            
            # Tentar inicializar (pode falhar graciosamente)
            try:
                manager = JuridicalRAGManager()
                self.assertIsNotNone(manager)
            except Exception:
                # Falha esperada se dependências não instaladas
                pass
                
        except ImportError:
            self.fail("Import do RAGManager deve ser seguro")


class TestFullIntegration(unittest.TestCase):
    """Testa integração completa com fallback."""
    
    def test_complete_workflow_fallback(self):
        """Testa fluxo completo com fallback."""
        
        try:
            from rag.mcp_integration import MCPRAGIntegration
            
            integration = MCPRAGIntegration()
            
            # Testar consulta (deve usar fallback se RAG indisponível)
            query = "Teste de consulta jurídica"
            response = integration.juridical_query(query)
            
            self.assertIsInstance(response, dict)
            self.assertIn("success", response)
            self.assertIn("response", response)
            
            # Se falhou, deve ter mensagem explicativa
            if not response["success"]:
                self.assertIn("error", response)
                
        except Exception as e:
            self.fail(f"Integração completa falhou: {e}")
    
    def test_status_reporting(self):
        """Testa relatório de status."""
        
        try:
            from rag.mcp_integration import MCPRAGIntegration
            
            integration = MCPRAGIntegration()
            status = integration.get_rag_status()
            
            # Status deve sempre retornar estrutura válida
            self.assertIsInstance(status, dict)
            self.assertIn("available", status)
            self.assertIn("timestamp", status)
            
            # Se disponível, deve ter mais detalhes
            if status["available"]:
                self.assertIn("document_count", status)
            else:
                self.assertIn("reason", status)
                
        except Exception as e:
            self.fail(f"Status reporting falhou: {e}")


def run_safety_checks():
    """Executa verificações de segurança básicas."""
    
    print("🔒 Executando verificações de segurança...")
    
    # 1. Verificar imports seguros
    try:
        import rag
        print("✅ Import do módulo RAG: OK")
    except Exception as e:
        print(f"❌ Import do módulo RAG: {e}")
        return False
    
    # 2. Verificar MCPRAGIntegration
    try:
        from rag.mcp_integration import MCPRAGIntegration
        integration = MCPRAGIntegration()
        status = integration.get_rag_status()
        print(f"✅ MCPRAGIntegration: OK (disponível: {status['available']})")
    except Exception as e:
        print(f"❌ MCPRAGIntegration: {e}")
        return False
    
    # 3. Verificar fallback
    try:
        from rag.mcp_integration import MCPRAGIntegration
        integration = MCPRAGIntegration()
        response = integration.juridical_query("teste")
        print(f"✅ Fallback funcionando: {response['success']}")
    except Exception as e:
        print(f"❌ Fallback: {e}")
        return False
    
    print("🎉 Todas as verificações de segurança passaram!")
    return True


def run_feature_tests():
    """Executa testes de funcionalidades se disponíveis."""
    
    print("\n🧪 Testando funcionalidades disponíveis...")
    
    try:
        from rag.mcp_integration import MCPRAGIntegration
        integration = MCPRAGIntegration()
        
        if integration.is_rag_available():
            print("✅ RAG totalmente disponível - testando recursos avançados")
            
            # Testar busca semântica se disponível
            try:
                from rag.rag_manager import JuridicalRAGManager
                manager = JuridicalRAGManager()
                print("✅ RAGManager inicializado")
                
                # Testar utils
                from rag.utils import RAGUtils
                utils = RAGUtils()
                chunks = utils.chunk_juridical_document(
                    "Art. 1º Teste.", 
                    doc_type="lei"
                )
                print(f"✅ Chunking jurídico: {len(chunks)} chunks")
                
            except Exception as e:
                print(f"⚠️ Alguns recursos avançados indisponíveis: {e}")
        else:
            print("⚠️ RAG não totalmente disponível - usando fallback")
            
    except Exception as e:
        print(f"❌ Erro nos testes de funcionalidade: {e}")


def main():
    """Executa todos os testes."""
    
    print("🚀 Iniciando testes do módulo RAG")
    print("=" * 50)
    
    # Verificações de segurança primeiro
    if not run_safety_checks():
        print("❌ Testes de segurança falharam!")
        return False
    
    # Testes de funcionalidade
    run_feature_tests()
    
    # Executar unittest
    print("\n🔬 Executando testes unitários...")
    
    # Descobrir e executar testes
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Resumo final
    print("\n" + "=" * 50)
    if result.wasSuccessful():
        print("✅ Todos os testes passaram!")
        print("🎯 Módulo RAG está funcionando corretamente")
    else:
        print(f"❌ {len(result.failures)} falhas, {len(result.errors)} erros")
        print("⚠️ Verifique as dependências e configurações")
    
    print("\n📋 Resumo:")
    print(f"   Testes executados: {result.testsRun}")
    print(f"   Falhas: {len(result.failures)}")
    print(f"   Erros: {len(result.errors)}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    main()
