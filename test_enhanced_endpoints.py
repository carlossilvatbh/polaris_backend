#!/usr/bin/env python3
"""
Teste dos Enhanced AI Endpoints
Valida funcionamento das novas rotas RAG+Claude
"""

import requests
import json
import sys
import os

# Configuração
BASE_URL = "http://localhost:5000/api/v1/enhanced-ai"
TEST_PROMPT = "Quais são os principais tipos de investimento para aposentadoria?"

def test_endpoint(endpoint, method="GET", data=None):
    """Testa um endpoint específico"""
    url = f"{BASE_URL}{endpoint}"
    
    print(f"\n🧪 Testando: {method} {endpoint}")
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=30)
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Sucesso!")
            
            # Mostrar informações relevantes
            if 'status' in result:
                print(f"   Status: {result['status']}")
            if 'content' in result:
                content = result['content'][:100] + "..." if len(result['content']) > 100 else result['content']
                print(f"   Content: {content}")
            if 'model' in result:
                print(f"   Model: {result['model']}")
            if 'rag_status' in result:
                print(f"   RAG Status: {result['rag_status']}")
                
        else:
            print(f"   ❌ Erro: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            
    except requests.exceptions.ConnectionError:
        print(f"   ⚠️ Servidor não está rodando em {BASE_URL}")
        return False
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        return False
        
    return response.status_code == 200

def main():
    """Executa todos os testes"""
    print("🚀 Testando Enhanced AI Endpoints")
    print("=" * 50)
    
    # Testar status
    status_ok = test_endpoint("/status")
    
    if not status_ok:
        print("\n⚠️ Servidor não está rodando. Para iniciar:")
        print("   cd /Users/theolamounier/code/polaris_backend")
        print("   python src/main.py")
        return
    
    # Testar endpoints de chat
    chat_data = {
        "prompt": TEST_PROMPT,
        "user_id": 1
    }
    
    test_endpoint("/chat-smart", "POST", chat_data)
    test_endpoint("/chat-rag", "POST", chat_data)
    test_endpoint("/chat-fallback", "POST", chat_data)
    
    # Testar usage tips
    test_endpoint("/usage-tips")
    
    print("\n" + "=" * 50)
    print("✅ Testes concluídos!")
    print("\nPara ativar RAG completo:")
    print("   pip install -r requirements_rag.txt")
    print("\nPara ativar Claude AI:")
    print("   export ANTHROPIC_API_KEY=sua_api_key")

if __name__ == "__main__":
    main()
