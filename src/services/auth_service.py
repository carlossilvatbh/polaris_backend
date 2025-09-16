"""
AuthService - Sistema de Autenticação e Autorização

Este service gerencia autenticação de usuários, geração de tokens JWT,
validação de permissões e controle de sessões.
"""

import os
import jwt
import bcrypt
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from dataclasses import dataclass
from functools import wraps
from flask import request, jsonify, current_app

from src.models import db, User


@dataclass
class AuthResult:
    """Resultado de operação de autenticação"""
    success: bool
    user: Optional[Dict] = None
    token: Optional[str] = None
    error: Optional[str] = None
    expires_at: Optional[datetime] = None


@dataclass
class TokenData:
    """Dados extraídos do token JWT"""
    user_id: int
    username: str
    email: str
    expires_at: datetime
    is_valid: bool = True


class AuthService:
    """Service para autenticação e autorização"""
    
    def __init__(self):
        self.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
        self.algorithm = 'HS256'
        self.token_expiry_hours = 24
        self.refresh_token_expiry_days = 30
    
    def register_user(self, username: str, email: str, password: str, 
                     first_name: str = None, last_name: str = None) -> AuthResult:
        """
        Registrar novo usuário
        
        Args:
            username: Nome de usuário único
            email: Email único
            password: Senha em texto plano
            first_name: Primeiro nome (opcional)
            last_name: Último nome (opcional)
            
        Returns:
            AuthResult com resultado da operação
        """
        try:
            # Verificar se usuário já existe
            existing_user = User.query.filter(
                (User.username == username) | (User.email == email)
            ).first()
            
            if existing_user:
                if existing_user.username == username:
                    return AuthResult(
                        success=False,
                        error="Nome de usuário já existe"
                    )
                else:
                    return AuthResult(
                        success=False,
                        error="Email já está em uso"
                    )
            
            # Validar dados
            validation_error = self._validate_user_data(username, email, password)
            if validation_error:
                return AuthResult(
                    success=False,
                    error=validation_error
                )
            
            # Hash da senha
            password_hash = self._hash_password(password)
            
            # Criar usuário
            user = User(
                username=username,
                email=email,
                password_hash=password_hash,
                first_name=first_name or '',
                last_name=last_name or ''
            )
            
            db.session.add(user)
            db.session.commit()
            
            # Gerar token
            token, expires_at = self._generate_token(user)
            
            return AuthResult(
                success=True,
                user=user.to_dict(),
                token=token,
                expires_at=expires_at
            )
            
        except Exception as e:
            db.session.rollback()
            self._log_error(f"Erro no registro: {str(e)}")
            return AuthResult(
                success=False,
                error="Erro interno no registro"
            )
    
    def login(self, username_or_email: str, password: str) -> AuthResult:
        """
        Fazer login do usuário
        
        Args:
            username_or_email: Username ou email
            password: Senha em texto plano
            
        Returns:
            AuthResult com resultado da autenticação
        """
        try:
            # Buscar usuário por username ou email
            user = User.query.filter(
                (User.username == username_or_email) | 
                (User.email == username_or_email)
            ).first()
            
            if not user:
                return AuthResult(
                    success=False,
                    error="Usuário não encontrado"
                )
            
            # Verificar senha
            if not self._verify_password(password, user.password_hash):
                return AuthResult(
                    success=False,
                    error="Senha incorreta"
                )
            
            # Atualizar último login
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            # Gerar token
            token, expires_at = self._generate_token(user)
            
            return AuthResult(
                success=True,
                user=user.to_dict(),
                token=token,
                expires_at=expires_at
            )
            
        except Exception as e:
            self._log_error(f"Erro no login: {str(e)}")
            return AuthResult(
                success=False,
                error="Erro interno no login"
            )
    
    def validate_token(self, token: str) -> TokenData:
        """
        Validar token JWT
        
        Args:
            token: Token JWT
            
        Returns:
            TokenData com dados do token
        """
        try:
            # Decodificar token
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Extrair dados
            user_id = payload.get('user_id')
            username = payload.get('username')
            email = payload.get('email')
            exp = payload.get('exp')
            
            if not all([user_id, username, email, exp]):
                return TokenData(
                    user_id=0,
                    username='',
                    email='',
                    expires_at=datetime.utcnow(),
                    is_valid=False
                )
            
            expires_at = datetime.fromtimestamp(exp)
            
            # Verificar se token não expirou
            if datetime.utcnow() > expires_at:
                return TokenData(
                    user_id=user_id,
                    username=username,
                    email=email,
                    expires_at=expires_at,
                    is_valid=False
                )
            
            # Verificar se usuário ainda existe
            user = User.query.get(user_id)
            if not user:
                return TokenData(
                    user_id=user_id,
                    username=username,
                    email=email,
                    expires_at=expires_at,
                    is_valid=False
                )
            
            return TokenData(
                user_id=user_id,
                username=username,
                email=email,
                expires_at=expires_at,
                is_valid=True
            )
            
        except jwt.ExpiredSignatureError:
            return TokenData(
                user_id=0,
                username='',
                email='',
                expires_at=datetime.utcnow(),
                is_valid=False
            )
        except jwt.InvalidTokenError:
            return TokenData(
                user_id=0,
                username='',
                email='',
                expires_at=datetime.utcnow(),
                is_valid=False
            )
        except Exception as e:
            self._log_error(f"Erro na validação do token: {str(e)}")
            return TokenData(
                user_id=0,
                username='',
                email='',
                expires_at=datetime.utcnow(),
                is_valid=False
            )
    
    def refresh_token(self, token: str) -> AuthResult:
        """
        Renovar token JWT
        
        Args:
            token: Token atual
            
        Returns:
            AuthResult com novo token
        """
        try:
            token_data = self.validate_token(token)
            
            if not token_data.is_valid:
                return AuthResult(
                    success=False,
                    error="Token inválido"
                )
            
            # Buscar usuário
            user = User.query.get(token_data.user_id)
            if not user:
                return AuthResult(
                    success=False,
                    error="Usuário não encontrado"
                )
            
            # Gerar novo token
            new_token, expires_at = self._generate_token(user)
            
            return AuthResult(
                success=True,
                user=user.to_dict(),
                token=new_token,
                expires_at=expires_at
            )
            
        except Exception as e:
            self._log_error(f"Erro na renovação do token: {str(e)}")
            return AuthResult(
                success=False,
                error="Erro interno na renovação"
            )
    
    def change_password(self, user_id: int, current_password: str, new_password: str) -> AuthResult:
        """
        Alterar senha do usuário
        
        Args:
            user_id: ID do usuário
            current_password: Senha atual
            new_password: Nova senha
            
        Returns:
            AuthResult com resultado da operação
        """
        try:
            # Buscar usuário
            user = User.query.get(user_id)
            if not user:
                return AuthResult(
                    success=False,
                    error="Usuário não encontrado"
                )
            
            # Verificar senha atual
            if not self._verify_password(current_password, user.password_hash):
                return AuthResult(
                    success=False,
                    error="Senha atual incorreta"
                )
            
            # Validar nova senha
            validation_error = self._validate_password(new_password)
            if validation_error:
                return AuthResult(
                    success=False,
                    error=validation_error
                )
            
            # Atualizar senha
            user.password_hash = self._hash_password(new_password)
            user.updated_at = datetime.utcnow()
            db.session.commit()
            
            return AuthResult(
                success=True,
                user=user.to_dict()
            )
            
        except Exception as e:
            db.session.rollback()
            self._log_error(f"Erro na alteração de senha: {str(e)}")
            return AuthResult(
                success=False,
                error="Erro interno na alteração de senha"
            )
    
    def get_user_by_token(self, token: str) -> Optional[User]:
        """
        Obter usuário pelo token
        
        Args:
            token: Token JWT
            
        Returns:
            User ou None se inválido
        """
        try:
            token_data = self.validate_token(token)
            
            if not token_data.is_valid:
                return None
            
            return User.query.get(token_data.user_id)
            
        except Exception as e:
            self._log_error(f"Erro ao obter usuário por token: {str(e)}")
            return None
    
    def require_auth(self, f):
        """
        Decorator para exigir autenticação em rotas
        
        Usage:
            @auth_service.require_auth
            def protected_route():
                # current_user estará disponível
                pass
        """
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Obter token do header
            auth_header = request.headers.get('Authorization')
            if not auth_header:
                return jsonify({'error': 'Token de autorização necessário'}), 401
            
            try:
                # Extrair token (formato: "Bearer <token>")
                token = auth_header.split(' ')[1]
            except IndexError:
                return jsonify({'error': 'Formato de token inválido'}), 401
            
            # Validar token
            token_data = self.validate_token(token)
            if not token_data.is_valid:
                return jsonify({'error': 'Token inválido ou expirado'}), 401
            
            # Buscar usuário
            user = User.query.get(token_data.user_id)
            if not user:
                return jsonify({'error': 'Usuário não encontrado'}), 401
            
            # Adicionar usuário ao contexto da requisição
            request.current_user = user
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    def health_check(self) -> Dict[str, Any]:
        """
        Verificar saúde do sistema de autenticação
        
        Returns:
            Dict com status do sistema
        """
        try:
            # Testar geração e validação de token
            test_user_data = {
                'id': 1,
                'username': 'test',
                'email': 'test@test.com'
            }
            
            # Gerar token de teste
            test_payload = {
                'user_id': test_user_data['id'],
                'username': test_user_data['username'],
                'email': test_user_data['email'],
                'exp': datetime.utcnow() + timedelta(minutes=1)
            }
            
            test_token = jwt.encode(test_payload, self.secret_key, algorithm=self.algorithm)
            
            # Validar token de teste
            token_data = self.validate_token(test_token)
            
            return {
                "status": "healthy" if token_data.is_valid else "unhealthy",
                "secret_key_configured": bool(self.secret_key and self.secret_key != 'dev-secret-key-change-in-production'),
                "algorithm": self.algorithm,
                "token_expiry_hours": self.token_expiry_hours,
                "test_token_valid": token_data.is_valid,
                "last_test": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "secret_key_configured": bool(self.secret_key),
                "algorithm": self.algorithm,
                "error": str(e),
                "last_test": datetime.utcnow().isoformat()
            }
    
    # Métodos privados auxiliares
    
    def _generate_token(self, user: User) -> tuple[str, datetime]:
        """Gerar token JWT para usuário"""
        expires_at = datetime.utcnow() + timedelta(hours=self.token_expiry_hours)
        
        payload = {
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
            'exp': expires_at
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        
        return token, expires_at
    
    def _hash_password(self, password: str) -> str:
        """Hash da senha usando bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verificar senha contra hash"""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    
    def _validate_user_data(self, username: str, email: str, password: str) -> Optional[str]:
        """Validar dados do usuário"""
        # Validar username
        if not username or len(username) < 3:
            return "Username deve ter pelo menos 3 caracteres"
        
        if len(username) > 50:
            return "Username deve ter no máximo 50 caracteres"
        
        # Validar email
        if not email or '@' not in email:
            return "Email inválido"
        
        if len(email) > 100:
            return "Email deve ter no máximo 100 caracteres"
        
        # Validar senha
        password_error = self._validate_password(password)
        if password_error:
            return password_error
        
        return None
    
    def _validate_password(self, password: str) -> Optional[str]:
        """Validar senha"""
        if not password:
            return "Senha é obrigatória"
        
        if len(password) < 6:
            return "Senha deve ter pelo menos 6 caracteres"
        
        if len(password) > 100:
            return "Senha deve ter no máximo 100 caracteres"
        
        return None
    
    def _log_error(self, error_msg: str):
        """Log de erro"""
        try:
            # Aqui integraria com LoggingService quando implementado
            print(f"[ERROR] AuthService: {error_msg}")
        except:
            print(f"[ERROR] AuthService: {error_msg}")


# Instância global do service
auth_service = AuthService()


def require_auth(f):
    """
    Decorator para proteger rotas que requerem autenticação
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Extrair token do header Authorization
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Token de acesso requerido'}), 401
        
        token = auth_header.split(' ')[1]
        
        # Validar token
        validation_result = auth_service.validate_token(token)
        if not validation_result.success:
            return jsonify({'error': validation_result.error}), 401
        
        # Adicionar dados do usuário ao request
        request.current_user = validation_result.user
        
        return f(*args, **kwargs)
    
    return decorated_function

