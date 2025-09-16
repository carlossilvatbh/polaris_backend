"""
LoggingService - Sistema de Logs e Auditoria

Este service gerencia logs estruturados, auditoria de ações
e monitoramento do sistema POLARIS.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import traceback
import functools

from src.models import db, AuditLog


class LogLevel(Enum):
    """Níveis de log"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ActionType(Enum):
    """Tipos de ação para auditoria"""
    CREATE = "CREATE"
    READ = "READ"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    UPLOAD = "UPLOAD"
    DOWNLOAD = "DOWNLOAD"
    GENERATE = "GENERATE"
    SEARCH = "SEARCH"
    SCRAPE = "SCRAPE"
    CACHE = "CACHE"
    API_CALL = "API_CALL"


@dataclass
class LogEntry:
    """Entrada de log estruturada"""
    timestamp: datetime
    level: LogLevel
    service: str
    action: str
    message: str
    user_id: Optional[int] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_id: Optional[str] = None
    duration_ms: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
    error_details: Optional[Dict[str, Any]] = None


@dataclass
class AuditEntry:
    """Entrada de auditoria"""
    timestamp: datetime
    user_id: int
    action_type: ActionType
    resource_type: str
    resource_id: Optional[str] = None
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class LoggingService:
    """Service para logging e auditoria"""
    
    def __init__(self):
        self.logs_dir = os.path.join(os.getcwd(), 'logs')
        os.makedirs(self.logs_dir, exist_ok=True)
        
        # Configurar logging padrão
        self._setup_logging()
        
        # Configurações
        self.max_log_file_size = 10 * 1024 * 1024  # 10MB
        self.max_log_files = 5
        self.log_retention_days = 30
        
        # Logger principal
        self.logger = logging.getLogger('polaris')
    
    def log(self, 
            level: LogLevel,
            service: str,
            action: str,
            message: str,
            user_id: int = None,
            session_id: str = None,
            ip_address: str = None,
            user_agent: str = None,
            request_id: str = None,
            duration_ms: float = None,
            metadata: Dict[str, Any] = None,
            error_details: Dict[str, Any] = None):
        """
        Registrar log estruturado
        
        Args:
            level: Nível do log
            service: Nome do service
            action: Ação executada
            message: Mensagem do log
            user_id: ID do usuário (opcional)
            session_id: ID da sessão (opcional)
            ip_address: Endereço IP (opcional)
            user_agent: User agent (opcional)
            request_id: ID da requisição (opcional)
            duration_ms: Duração em milissegundos (opcional)
            metadata: Metadados adicionais (opcional)
            error_details: Detalhes do erro (opcional)
        """
        try:
            entry = LogEntry(
                timestamp=datetime.utcnow(),
                level=level,
                service=service,
                action=action,
                message=message,
                user_id=user_id,
                session_id=session_id,
                ip_address=ip_address,
                user_agent=user_agent,
                request_id=request_id,
                duration_ms=duration_ms,
                metadata=metadata,
                error_details=error_details
            )
            
            # Log estruturado em JSON
            log_data = asdict(entry)
            log_data['timestamp'] = entry.timestamp.isoformat()
            log_data['level'] = level.value
            
            # Log usando logger padrão
            log_message = json.dumps(log_data, ensure_ascii=False)
            
            if level == LogLevel.DEBUG:
                self.logger.debug(log_message)
            elif level == LogLevel.INFO:
                self.logger.info(log_message)
            elif level == LogLevel.WARNING:
                self.logger.warning(log_message)
            elif level == LogLevel.ERROR:
                self.logger.error(log_message)
            elif level == LogLevel.CRITICAL:
                self.logger.critical(log_message)
            
        except Exception as e:
            # Fallback para log simples
            print(f"[{level.value}] {service}.{action}: {message}")
            print(f"[ERROR] LoggingService: {str(e)}")
    
    def audit(self,
              user_id: int,
              action_type: ActionType,
              resource_type: str,
              resource_id: str = None,
              old_values: Dict[str, Any] = None,
              new_values: Dict[str, Any] = None,
              ip_address: str = None,
              user_agent: str = None,
              session_id: str = None,
              success: bool = True,
              error_message: str = None,
              metadata: Dict[str, Any] = None):
        """
        Registrar entrada de auditoria
        
        Args:
            user_id: ID do usuário
            action_type: Tipo de ação
            resource_type: Tipo de recurso
            resource_id: ID do recurso (opcional)
            old_values: Valores antigos (opcional)
            new_values: Valores novos (opcional)
            ip_address: Endereço IP (opcional)
            user_agent: User agent (opcional)
            session_id: ID da sessão (opcional)
            success: Se a ação foi bem-sucedida
            error_message: Mensagem de erro (opcional)
            metadata: Metadados adicionais (opcional)
        """
        try:
            # Criar entrada de auditoria
            audit_entry = AuditEntry(
                timestamp=datetime.utcnow(),
                user_id=user_id,
                action_type=action_type,
                resource_type=resource_type,
                resource_id=resource_id,
                old_values=old_values,
                new_values=new_values,
                ip_address=ip_address,
                user_agent=user_agent,
                session_id=session_id,
                success=success,
                error_message=error_message,
                metadata=metadata
            )
            
            # Salvar no banco de dados
            audit_log = AuditLog(
                user_id=user_id,
                action_type=action_type.value,
                resource_type=resource_type,
                resource_id=resource_id,
                old_values=old_values or {},
                new_values=new_values or {},
                ip_address=ip_address,
                user_agent=user_agent,
                session_id=session_id,
                success=success,
                error_message=error_message,
                metadata=metadata or {}
            )
            
            db.session.add(audit_log)
            db.session.commit()
            
            # Log da auditoria
            self.log(
                level=LogLevel.INFO,
                service="AuditService",
                action=action_type.value,
                message=f"Audit: {action_type.value} {resource_type}",
                user_id=user_id,
                session_id=session_id,
                ip_address=ip_address,
                user_agent=user_agent,
                metadata={
                    'resource_type': resource_type,
                    'resource_id': resource_id,
                    'success': success
                }
            )
            
        except Exception as e:
            db.session.rollback()
            self.log(
                level=LogLevel.ERROR,
                service="AuditService",
                action="AUDIT_ERROR",
                message=f"Erro na auditoria: {str(e)}",
                user_id=user_id,
                error_details={'error': str(e), 'traceback': traceback.format_exc()}
            )
    
    def info(self, service: str, action: str, message: str, **kwargs):
        """Log de informação"""
        self.log(LogLevel.INFO, service, action, message, **kwargs)
    
    def warning(self, service: str, action: str, message: str, **kwargs):
        """Log de aviso"""
        self.log(LogLevel.WARNING, service, action, message, **kwargs)
    
    def error(self, service: str, action: str, message: str, **kwargs):
        """Log de erro"""
        self.log(LogLevel.ERROR, service, action, message, **kwargs)
    
    def debug(self, service: str, action: str, message: str, **kwargs):
        """Log de debug"""
        self.log(LogLevel.DEBUG, service, action, message, **kwargs)
    
    def critical(self, service: str, action: str, message: str, **kwargs):
        """Log crítico"""
        self.log(LogLevel.CRITICAL, service, action, message, **kwargs)
    
    def get_logs(self,
                 service: str = None,
                 level: LogLevel = None,
                 start_date: datetime = None,
                 end_date: datetime = None,
                 user_id: int = None,
                 limit: int = 100) -> List[Dict[str, Any]]:
        """
        Obter logs filtrados
        
        Args:
            service: Filtrar por service
            level: Filtrar por nível
            start_date: Data inicial
            end_date: Data final
            user_id: Filtrar por usuário
            limit: Limite de resultados
            
        Returns:
            Lista de logs
        """
        try:
            # Ler logs do arquivo (implementação simplificada)
            logs = []
            log_file = os.path.join(self.logs_dir, 'polaris.log')
            
            if not os.path.exists(log_file):
                return []
            
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        log_data = json.loads(line.strip())
                        
                        # Aplicar filtros
                        if service and log_data.get('service') != service:
                            continue
                        
                        if level and log_data.get('level') != level.value:
                            continue
                        
                        if user_id and log_data.get('user_id') != user_id:
                            continue
                        
                        # Filtros de data
                        log_timestamp = datetime.fromisoformat(log_data['timestamp'])
                        
                        if start_date and log_timestamp < start_date:
                            continue
                        
                        if end_date and log_timestamp > end_date:
                            continue
                        
                        logs.append(log_data)
                        
                        if len(logs) >= limit:
                            break
                            
                    except (json.JSONDecodeError, KeyError):
                        continue
            
            # Ordenar por timestamp (mais recentes primeiro)
            logs.sort(key=lambda x: x['timestamp'], reverse=True)
            
            return logs[:limit]
            
        except Exception as e:
            self.error("LoggingService", "GET_LOGS", f"Erro ao obter logs: {str(e)}")
            return []
    
    def get_audit_logs(self,
                       user_id: int = None,
                       action_type: ActionType = None,
                       resource_type: str = None,
                       start_date: datetime = None,
                       end_date: datetime = None,
                       limit: int = 100) -> List[Dict[str, Any]]:
        """
        Obter logs de auditoria
        
        Args:
            user_id: Filtrar por usuário
            action_type: Filtrar por tipo de ação
            resource_type: Filtrar por tipo de recurso
            start_date: Data inicial
            end_date: Data final
            limit: Limite de resultados
            
        Returns:
            Lista de logs de auditoria
        """
        try:
            query = AuditLog.query
            
            if user_id:
                query = query.filter_by(user_id=user_id)
            
            if action_type:
                query = query.filter_by(action_type=action_type.value)
            
            if resource_type:
                query = query.filter_by(resource_type=resource_type)
            
            if start_date:
                query = query.filter(AuditLog.created_at >= start_date)
            
            if end_date:
                query = query.filter(AuditLog.created_at <= end_date)
            
            audit_logs = query.order_by(
                AuditLog.created_at.desc()
            ).limit(limit).all()
            
            return [log.to_dict() for log in audit_logs]
            
        except Exception as e:
            self.error("LoggingService", "GET_AUDIT_LOGS", f"Erro ao obter logs de auditoria: {str(e)}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Obter estatísticas de logs
        
        Returns:
            Dict com estatísticas
        """
        try:
            # Estatísticas de auditoria
            total_audit_logs = AuditLog.query.count()
            
            # Por tipo de ação
            action_stats = db.session.query(
                AuditLog.action_type,
                db.func.count(AuditLog.id).label('count')
            ).group_by(AuditLog.action_type).all()
            
            # Por usuário (top 10)
            user_stats = db.session.query(
                AuditLog.user_id,
                db.func.count(AuditLog.id).label('count')
            ).group_by(AuditLog.user_id).order_by(
                db.func.count(AuditLog.id).desc()
            ).limit(10).all()
            
            # Logs de hoje
            today = datetime.utcnow().date()
            logs_today = AuditLog.query.filter(
                db.func.date(AuditLog.created_at) == today
            ).count()
            
            # Logs da semana
            week_ago = today - timedelta(days=7)
            logs_week = AuditLog.query.filter(
                db.func.date(AuditLog.created_at) >= week_ago
            ).count()
            
            # Erros recentes
            recent_errors = AuditLog.query.filter(
                AuditLog.success == False,
                AuditLog.created_at >= datetime.utcnow() - timedelta(hours=24)
            ).count()
            
            # Tamanho dos arquivos de log
            log_files_size = 0
            if os.path.exists(self.logs_dir):
                for filename in os.listdir(self.logs_dir):
                    file_path = os.path.join(self.logs_dir, filename)
                    if os.path.isfile(file_path):
                        log_files_size += os.path.getsize(file_path)
            
            return {
                'audit_logs': {
                    'total': total_audit_logs,
                    'today': logs_today,
                    'this_week': logs_week,
                    'recent_errors': recent_errors
                },
                'by_action_type': {action_type: count for action_type, count in action_stats},
                'top_users': [{'user_id': user_id, 'count': count} for user_id, count in user_stats],
                'log_files': {
                    'directory': self.logs_dir,
                    'total_size_mb': round(log_files_size / (1024 * 1024), 2)
                },
                'config': {
                    'max_log_file_size_mb': self.max_log_file_size / (1024 * 1024),
                    'max_log_files': self.max_log_files,
                    'retention_days': self.log_retention_days
                }
            }
            
        except Exception as e:
            self.error("LoggingService", "GET_STATISTICS", f"Erro nas estatísticas: {str(e)}")
            return {
                'audit_logs': {'total': 0, 'today': 0, 'this_week': 0, 'recent_errors': 0},
                'by_action_type': {},
                'top_users': [],
                'log_files': {'directory': self.logs_dir, 'total_size_mb': 0},
                'config': {}
            }
    
    def cleanup_old_logs(self) -> Dict[str, int]:
        """
        Limpar logs antigos
        
        Returns:
            Dict com estatísticas da limpeza
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=self.log_retention_days)
            
            # Limpar logs de auditoria antigos
            deleted_audit = AuditLog.query.filter(
                AuditLog.created_at < cutoff_date
            ).delete()
            
            db.session.commit()
            
            # Limpar arquivos de log antigos
            deleted_files = 0
            if os.path.exists(self.logs_dir):
                for filename in os.listdir(self.logs_dir):
                    file_path = os.path.join(self.logs_dir, filename)
                    if os.path.isfile(file_path):
                        file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                        if file_time < cutoff_date:
                            os.remove(file_path)
                            deleted_files += 1
            
            self.info(
                "LoggingService",
                "CLEANUP",
                f"Limpeza concluída: {deleted_audit} audit logs, {deleted_files} arquivos"
            )
            
            return {
                'deleted_audit_logs': deleted_audit,
                'deleted_files': deleted_files,
                'cutoff_date': cutoff_date.isoformat()
            }
            
        except Exception as e:
            db.session.rollback()
            self.error("LoggingService", "CLEANUP", f"Erro na limpeza: {str(e)}")
            return {
                'deleted_audit_logs': 0,
                'deleted_files': 0,
                'error': str(e)
            }
    
    def health_check(self) -> Dict[str, Any]:
        """
        Verificar saúde do sistema de logging
        
        Returns:
            Dict com status do sistema
        """
        try:
            # Verificar diretório de logs
            logs_dir_exists = os.path.exists(self.logs_dir)
            logs_dir_writable = os.access(self.logs_dir, os.W_OK) if logs_dir_exists else False
            
            # Testar escrita de log
            test_log_success = False
            try:
                self.debug("LoggingService", "HEALTH_CHECK", "Test log entry")
                test_log_success = True
            except:
                pass
            
            # Testar auditoria
            test_audit_success = False
            try:
                # Não salvar no banco, apenas testar criação do objeto
                test_audit = AuditLog(
                    user_id=0,
                    action_type="TEST",
                    resource_type="health_check",
                    success=True
                )
                test_audit_success = True
            except:
                pass
            
            # Verificar tamanho dos logs
            log_files_info = []
            total_size = 0
            
            if logs_dir_exists:
                for filename in os.listdir(self.logs_dir):
                    file_path = os.path.join(self.logs_dir, filename)
                    if os.path.isfile(file_path):
                        file_size = os.path.getsize(file_path)
                        total_size += file_size
                        log_files_info.append({
                            'filename': filename,
                            'size_mb': round(file_size / (1024 * 1024), 2),
                            'modified': datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
                        })
            
            # Estatísticas recentes
            stats = self.get_statistics()
            
            # Determinar status
            status = "healthy"
            if not logs_dir_writable:
                status = "unhealthy"
            elif not test_log_success or not test_audit_success:
                status = "degraded"
            elif total_size > 100 * 1024 * 1024:  # 100MB
                status = "warning"
            
            return {
                "status": status,
                "directories": {
                    "logs_dir": {
                        "path": self.logs_dir,
                        "exists": logs_dir_exists,
                        "writable": logs_dir_writable
                    }
                },
                "functionality": {
                    "logging": test_log_success,
                    "audit": test_audit_success
                },
                "log_files": {
                    "count": len(log_files_info),
                    "total_size_mb": round(total_size / (1024 * 1024), 2),
                    "files": log_files_info[:5]  # Mostrar apenas os 5 primeiros
                },
                "statistics": {
                    "total_audit_logs": stats['audit_logs']['total'],
                    "logs_today": stats['audit_logs']['today'],
                    "recent_errors": stats['audit_logs']['recent_errors']
                },
                "config": {
                    "retention_days": self.log_retention_days,
                    "max_file_size_mb": self.max_log_file_size / (1024 * 1024),
                    "max_files": self.max_log_files
                },
                "last_check": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "last_check": datetime.utcnow().isoformat()
            }
    
    # Métodos privados auxiliares
    
    def _setup_logging(self):
        """Configurar sistema de logging"""
        try:
            # Configurar logger principal
            logger = logging.getLogger('polaris')
            logger.setLevel(logging.DEBUG)
            
            # Remover handlers existentes
            for handler in logger.handlers[:]:
                logger.removeHandler(handler)
            
            # Handler para arquivo
            log_file = os.path.join(self.logs_dir, 'polaris.log')
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=self.max_log_file_size,
                backupCount=self.max_log_files,
                encoding='utf-8'
            )
            
            # Handler para console
            console_handler = logging.StreamHandler()
            
            # Formatter simples (JSON será adicionado pelo service)
            formatter = logging.Formatter('%(message)s')
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)
            
            # Adicionar handlers
            logger.addHandler(file_handler)
            logger.addHandler(console_handler)
            
            # Evitar propagação para root logger
            logger.propagate = False
            
        except Exception as e:
            print(f"[ERROR] LoggingService setup: {str(e)}")


# Decorador para logging automático
def log_action(action_type: ActionType, resource_type: str):
    """
    Decorador para logging automático de ações
    
    Args:
        action_type: Tipo de ação
        resource_type: Tipo de recurso
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = datetime.utcnow()
            service_name = func.__module__.split('.')[-1] if hasattr(func, '__module__') else 'unknown'
            
            try:
                # Executar função
                result = func(*args, **kwargs)
                
                # Calcular duração
                duration = (datetime.utcnow() - start_time).total_seconds() * 1000
                
                # Log de sucesso
                logging_service.log(
                    level=LogLevel.INFO,
                    service=service_name,
                    action=func.__name__,
                    message=f"Action completed: {action_type.value} {resource_type}",
                    duration_ms=duration,
                    metadata={
                        'action_type': action_type.value,
                        'resource_type': resource_type,
                        'function': func.__name__
                    }
                )
                
                return result
                
            except Exception as e:
                # Calcular duração
                duration = (datetime.utcnow() - start_time).total_seconds() * 1000
                
                # Log de erro
                logging_service.log(
                    level=LogLevel.ERROR,
                    service=service_name,
                    action=func.__name__,
                    message=f"Action failed: {action_type.value} {resource_type}",
                    duration_ms=duration,
                    error_details={
                        'error': str(e),
                        'traceback': traceback.format_exc()
                    },
                    metadata={
                        'action_type': action_type.value,
                        'resource_type': resource_type,
                        'function': func.__name__
                    }
                )
                
                raise
        
        return wrapper
    return decorator


# Instância global do logging service
logging_service = LoggingService()

