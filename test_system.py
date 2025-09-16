#!/usr/bin/env python3
"""
Script de teste para validação do POLARIS Backend
"""

import requests
import json
import sys
from datetime import datetime

BASE_URL = "http://localhost:5001"

def test_health_check():
    """Testa o health check básico"""
    print("🔍 Testando Health Check...")
    try:
        response = requests.get(f"{BASE_URL}/api/health")
        print(f"✅ Status: {response.status_code}")
        print(f"✅ Response: {response.json()}")
        return True
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        return False

def test_generate_document_without_auth():
    """Testa endpoint protegido sem autenticação"""
    print("\n🔍 Testando endpoint protegido sem autenticação...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/generate-document",
            json={"prompt": "Teste"}
        )
        print(f"✅ Status: {response.status_code} (esperado 401)")
        print(f"✅ Response: {response.json()}")
        return response.status_code == 401
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        return False

def test_user_registration():
    """Testa criação de usuário"""
    print("\n🔍 Testando criação de usuário...")
    try:
        user_data = {
            "nome": "Usuario Teste",
            "email": f"teste_{int(datetime.now().timestamp())}@polaris.com",
            "senha": "123456"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/users/register",
            json=user_data
        )
        print(f"✅ Status: {response.status_code}")
        result = response.json()
        print(f"✅ Response: {result}")
        
        if response.status_code == 201:
            return result.get('token')  # Retorna token para próximos testes
        
        return None
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        return None

def test_claude_ai_simulation(token):
    """Testa o Claude AI em modo simulação"""
    print("\n🔍 Testando Claude AI (modo simulação)...")
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/ai/chat",
            headers=headers,
            json={"prompt": "Olá, como você pode me ajudar?"}
        )
        print(f"✅ Status: {response.status_code}")
        result = response.json()
        print(f"✅ Response: {result}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        return False

def main():
    """Executa todos os testes"""
    print("🚀 INICIANDO TESTES DO POLARIS BACKEND")
    print("=" * 50)
    
    tests_passed = 0
    total_tests = 0
    
    # Teste 1: Health Check
    total_tests += 1
    if test_health_check():
        tests_passed += 1
    
    # Teste 2: Endpoint protegido
    total_tests += 1
    if test_generate_document_without_auth():
        tests_passed += 1
    
    # Teste 3: Criação de usuário
    total_tests += 1
    token = test_user_registration()
    if token:
        tests_passed += 1
        
        # Teste 4: Claude AI (se temos token)
        total_tests += 1
        if test_claude_ai_simulation(token):
            tests_passed += 1
    else:
        total_tests += 1  # Conta o teste do Claude AI como faltante
    
    # Resultado final
    print("\n" + "=" * 50)
    print(f"📊 RESULTADO DOS TESTES: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("🎉 TODOS OS TESTES PASSARAM!")
        print("✅ Sistema POLARIS está funcional!")
        sys.exit(0)
    else:
        print(f"⚠️  {total_tests - tests_passed} testes falharam")
        print("❌ Sistema precisa de ajustes")
        sys.exit(1)

if __name__ == "__main__":
    main()
