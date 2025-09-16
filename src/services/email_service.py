"""
EmailService - Sistema de Notificações por Email

Este service gerencia envio de emails, templates e notificações
do sistema POLARIS.
"""

import os
import smtplib
import ssl
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from email.mime.base import MimeBase
from email import encoders
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import jinja2
import json

from src.services.logging_service import logging_service, LogLevel


class EmailType(Enum):
    """Tipos de email"""
    WELCOME = "welcome"
    PASSWORD_RESET = "password_reset"
    DOCUMENT_READY = "document_ready"
    SYSTEM_ALERT = "system_alert"
    AUDIT_REPORT = "audit_report"
    BACKUP_NOTIFICATION = "backup_notification"
    ERROR_NOTIFICATION = "error_notification"
    WEEKLY_REPORT = "weekly_report"


@dataclass
class EmailTemplate:
    """Template de email"""
    name: str
    subject: str
    html_content: str
    text_content: str
    variables: List[str]


@dataclass
class EmailAttachment:
    """Anexo de email"""
    filename: str
    content: bytes
    content_type: str = "application/octet-stream"


@dataclass
class EmailMessage:
    """Mensagem de email"""
    to_emails: List[str]
    subject: str
    html_content: str
    text_content: str = None
    from_email: str = None
    from_name: str = None
    reply_to: str = None
    cc_emails: List[str] = None
    bcc_emails: List[str] = None
    attachments: List[EmailAttachment] = None
    template_variables: Dict[str, Any] = None


class EmailService:
    """Service para envio de emails"""
    
    def __init__(self):
        # Configurações SMTP
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME', '')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.smtp_use_tls = os.getenv('SMTP_USE_TLS', 'true').lower() == 'true'
        
        # Configurações padrão
        self.default_from_email = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@polaris.com')
        self.default_from_name = os.getenv('DEFAULT_FROM_NAME', 'POLARIS')
        self.default_reply_to = os.getenv('DEFAULT_REPLY_TO', 'support@polaris.com')
        
        # Configurações de rate limiting
        self.max_emails_per_hour = int(os.getenv('MAX_EMAILS_PER_HOUR', '100'))
        self.max_emails_per_day = int(os.getenv('MAX_EMAILS_PER_DAY', '1000'))
        
        # Templates
        self.templates = {}
        self._load_templates()
        
        # Jinja2 environment
        self.jinja_env = jinja2.Environment(
            loader=jinja2.DictLoader({}),
            autoescape=jinja2.select_autoescape(['html', 'xml'])
        )
        
        # Estatísticas
        self.stats = {
            'emails_sent_today': 0,
            'emails_sent_hour': 0,
            'last_reset_day': datetime.utcnow().date(),
            'last_reset_hour': datetime.utcnow().hour,
            'total_sent': 0,
            'total_failed': 0
        }
    
    def send_email(self, message: EmailMessage) -> bool:
        """
        Enviar email
        
        Args:
            message: Mensagem de email
            
        Returns:
            True se enviado com sucesso
        """
        try:
            # Verificar rate limiting
            if not self._check_rate_limit():
                logging_service.warning(
                    "EmailService",
                    "RATE_LIMIT",
                    "Rate limit excedido para envio de emails"
                )
                return False
            
            # Validar configuração
            if not self._validate_config():
                logging_service.error(
                    "EmailService",
                    "CONFIG_ERROR",
                    "Configuração SMTP inválida"
                )
                return False
            
            # Preparar mensagem
            msg = self._prepare_message(message)
            if not msg:
                return False
            
            # Enviar via SMTP
            success = self._send_via_smtp(msg, message.to_emails)
            
            if success:
                self._update_stats(success=True)
                logging_service.info(
                    "EmailService",
                    "SEND_SUCCESS",
                    f"Email enviado para {len(message.to_emails)} destinatários",
                    metadata={
                        'to_emails': message.to_emails,
                        'subject': message.subject
                    }
                )
            else:
                self._update_stats(success=False)
            
            return success
            
        except Exception as e:
            self._update_stats(success=False)
            logging_service.error(
                "EmailService",
                "SEND_ERROR",
                f"Erro no envio de email: {str(e)}",
                error_details={'error': str(e)}
            )
            return False
    
    def send_template_email(self,
                           to_emails: List[str],
                           template_type: EmailType,
                           variables: Dict[str, Any] = None,
                           attachments: List[EmailAttachment] = None,
                           **kwargs) -> bool:
        """
        Enviar email usando template
        
        Args:
            to_emails: Lista de emails destinatários
            template_type: Tipo de template
            variables: Variáveis do template
            attachments: Anexos (opcional)
            **kwargs: Argumentos adicionais
            
        Returns:
            True se enviado com sucesso
        """
        try:
            # Obter template
            template = self._get_template(template_type)
            if not template:
                logging_service.error(
                    "EmailService",
                    "TEMPLATE_NOT_FOUND",
                    f"Template não encontrado: {template_type.value}"
                )
                return False
            
            # Renderizar template
            variables = variables or {}
            variables.update({
                'current_year': datetime.utcnow().year,
                'current_date': datetime.utcnow().strftime('%d/%m/%Y'),
                'system_name': 'POLARIS'
            })
            
            try:
                subject = self.jinja_env.from_string(template.subject).render(**variables)
                html_content = self.jinja_env.from_string(template.html_content).render(**variables)
                text_content = self.jinja_env.from_string(template.text_content).render(**variables)
            except Exception as e:
                logging_service.error(
                    "EmailService",
                    "TEMPLATE_RENDER_ERROR",
                    f"Erro na renderização do template: {str(e)}",
                    error_details={'template_type': template_type.value, 'error': str(e)}
                )
                return False
            
            # Criar mensagem
            message = EmailMessage(
                to_emails=to_emails,
                subject=subject,
                html_content=html_content,
                text_content=text_content,
                attachments=attachments,
                template_variables=variables,
                **kwargs
            )
            
            return self.send_email(message)
            
        except Exception as e:
            logging_service.error(
                "EmailService",
                "TEMPLATE_EMAIL_ERROR",
                f"Erro no envio de email template: {str(e)}",
                error_details={'template_type': template_type.value, 'error': str(e)}
            )
            return False
    
    def send_welcome_email(self, user_email: str, user_name: str) -> bool:
        """
        Enviar email de boas-vindas
        
        Args:
            user_email: Email do usuário
            user_name: Nome do usuário
            
        Returns:
            True se enviado com sucesso
        """
        return self.send_template_email(
            to_emails=[user_email],
            template_type=EmailType.WELCOME,
            variables={
                'user_name': user_name,
                'login_url': os.getenv('FRONTEND_URL', 'https://polaris.com')
            }
        )
    
    def send_password_reset_email(self, user_email: str, reset_token: str) -> bool:
        """
        Enviar email de reset de senha
        
        Args:
            user_email: Email do usuário
            reset_token: Token de reset
            
        Returns:
            True se enviado com sucesso
        """
        reset_url = f"{os.getenv('FRONTEND_URL', 'https://polaris.com')}/reset-password?token={reset_token}"
        
        return self.send_template_email(
            to_emails=[user_email],
            template_type=EmailType.PASSWORD_RESET,
            variables={
                'reset_url': reset_url,
                'reset_token': reset_token,
                'expiry_hours': 24
            }
        )
    
    def send_document_ready_email(self, user_email: str, document_name: str, download_url: str) -> bool:
        """
        Enviar email de documento pronto
        
        Args:
            user_email: Email do usuário
            document_name: Nome do documento
            download_url: URL de download
            
        Returns:
            True se enviado com sucesso
        """
        return self.send_template_email(
            to_emails=[user_email],
            template_type=EmailType.DOCUMENT_READY,
            variables={
                'document_name': document_name,
                'download_url': download_url,
                'expiry_days': 7
            }
        )
    
    def send_system_alert_email(self, admin_emails: List[str], alert_type: str, message: str) -> bool:
        """
        Enviar email de alerta do sistema
        
        Args:
            admin_emails: Lista de emails de administradores
            alert_type: Tipo de alerta
            message: Mensagem do alerta
            
        Returns:
            True se enviado com sucesso
        """
        return self.send_template_email(
            to_emails=admin_emails,
            template_type=EmailType.SYSTEM_ALERT,
            variables={
                'alert_type': alert_type,
                'alert_message': message,
                'timestamp': datetime.utcnow().strftime('%d/%m/%Y %H:%M:%S'),
                'system_url': os.getenv('FRONTEND_URL', 'https://polaris.com')
            }
        )
    
    def send_audit_report_email(self, admin_emails: List[str], report_data: Dict[str, Any]) -> bool:
        """
        Enviar email de relatório de auditoria
        
        Args:
            admin_emails: Lista de emails de administradores
            report_data: Dados do relatório
            
        Returns:
            True se enviado com sucesso
        """
        return self.send_template_email(
            to_emails=admin_emails,
            template_type=EmailType.AUDIT_REPORT,
            variables={
                'report_period': report_data.get('period', 'Última semana'),
                'total_actions': report_data.get('total_actions', 0),
                'unique_users': report_data.get('unique_users', 0),
                'failed_actions': report_data.get('failed_actions', 0),
                'top_actions': report_data.get('top_actions', []),
                'report_url': report_data.get('report_url', '')
            }
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Obter estatísticas de email
        
        Returns:
            Dict com estatísticas
        """
        try:
            # Atualizar contadores se necessário
            self._update_rate_limit_counters()
            
            return {
                'today': {
                    'sent': self.stats['emails_sent_today'],
                    'limit': self.max_emails_per_day,
                    'remaining': max(0, self.max_emails_per_day - self.stats['emails_sent_today'])
                },
                'current_hour': {
                    'sent': self.stats['emails_sent_hour'],
                    'limit': self.max_emails_per_hour,
                    'remaining': max(0, self.max_emails_per_hour - self.stats['emails_sent_hour'])
                },
                'total': {
                    'sent': self.stats['total_sent'],
                    'failed': self.stats['total_failed'],
                    'success_rate': (
                        self.stats['total_sent'] / (self.stats['total_sent'] + self.stats['total_failed']) * 100
                        if (self.stats['total_sent'] + self.stats['total_failed']) > 0 else 0
                    )
                },
                'templates': {
                    'available': list(self.templates.keys()),
                    'count': len(self.templates)
                },
                'config': {
                    'smtp_server': self.smtp_server,
                    'smtp_port': self.smtp_port,
                    'from_email': self.default_from_email,
                    'from_name': self.default_from_name,
                    'configured': self._validate_config()
                }
            }
            
        except Exception as e:
            logging_service.error(
                "EmailService",
                "GET_STATISTICS",
                f"Erro nas estatísticas: {str(e)}"
            )
            return {}
    
    def health_check(self) -> Dict[str, Any]:
        """
        Verificar saúde do sistema de email
        
        Returns:
            Dict com status do sistema
        """
        try:
            # Verificar configuração
            config_valid = self._validate_config()
            
            # Testar conexão SMTP
            smtp_status = "unknown"
            smtp_error = None
            
            if config_valid:
                try:
                    context = ssl.create_default_context()
                    with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                        if self.smtp_use_tls:
                            server.starttls(context=context)
                        server.login(self.smtp_username, self.smtp_password)
                        smtp_status = "healthy"
                except Exception as e:
                    smtp_status = "unhealthy"
                    smtp_error = str(e)
            else:
                smtp_status = "not_configured"
            
            # Verificar templates
            templates_status = "healthy" if len(self.templates) > 0 else "no_templates"
            
            # Verificar rate limiting
            rate_limit_status = "healthy"
            if self.stats['emails_sent_today'] >= self.max_emails_per_day:
                rate_limit_status = "daily_limit_reached"
            elif self.stats['emails_sent_hour'] >= self.max_emails_per_hour:
                rate_limit_status = "hourly_limit_reached"
            
            # Status geral
            overall_status = "healthy"
            if smtp_status == "unhealthy":
                overall_status = "unhealthy"
            elif smtp_status == "not_configured":
                overall_status = "not_configured"
            elif rate_limit_status != "healthy":
                overall_status = "rate_limited"
            elif templates_status == "no_templates":
                overall_status = "degraded"
            
            return {
                "status": overall_status,
                "smtp": {
                    "status": smtp_status,
                    "server": self.smtp_server,
                    "port": self.smtp_port,
                    "username": self.smtp_username,
                    "use_tls": self.smtp_use_tls,
                    "error": smtp_error
                },
                "templates": {
                    "status": templates_status,
                    "count": len(self.templates),
                    "available": list(self.templates.keys())
                },
                "rate_limiting": {
                    "status": rate_limit_status,
                    "today": f"{self.stats['emails_sent_today']}/{self.max_emails_per_day}",
                    "current_hour": f"{self.stats['emails_sent_hour']}/{self.max_emails_per_hour}"
                },
                "statistics": self.get_statistics(),
                "last_check": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "last_check": datetime.utcnow().isoformat()
            }
    
    # Métodos privados auxiliares
    
    def _validate_config(self) -> bool:
        """Validar configuração SMTP"""
        return bool(
            self.smtp_server and
            self.smtp_port and
            self.smtp_username and
            self.smtp_password and
            self.default_from_email
        )
    
    def _check_rate_limit(self) -> bool:
        """Verificar rate limiting"""
        self._update_rate_limit_counters()
        
        return (
            self.stats['emails_sent_today'] < self.max_emails_per_day and
            self.stats['emails_sent_hour'] < self.max_emails_per_hour
        )
    
    def _update_rate_limit_counters(self):
        """Atualizar contadores de rate limiting"""
        now = datetime.utcnow()
        
        # Reset contador diário
        if now.date() != self.stats['last_reset_day']:
            self.stats['emails_sent_today'] = 0
            self.stats['last_reset_day'] = now.date()
        
        # Reset contador horário
        if now.hour != self.stats['last_reset_hour']:
            self.stats['emails_sent_hour'] = 0
            self.stats['last_reset_hour'] = now.hour
    
    def _update_stats(self, success: bool):
        """Atualizar estatísticas"""
        self._update_rate_limit_counters()
        
        if success:
            self.stats['emails_sent_today'] += 1
            self.stats['emails_sent_hour'] += 1
            self.stats['total_sent'] += 1
        else:
            self.stats['total_failed'] += 1
    
    def _prepare_message(self, message: EmailMessage) -> Optional[MimeMultipart]:
        """Preparar mensagem MIME"""
        try:
            msg = MimeMultipart('alternative')
            
            # Headers
            msg['Subject'] = message.subject
            msg['From'] = f"{message.from_name or self.default_from_name} <{message.from_email or self.default_from_email}>"
            msg['To'] = ', '.join(message.to_emails)
            
            if message.reply_to:
                msg['Reply-To'] = message.reply_to
            elif self.default_reply_to:
                msg['Reply-To'] = self.default_reply_to
            
            if message.cc_emails:
                msg['Cc'] = ', '.join(message.cc_emails)
            
            # Conteúdo texto
            if message.text_content:
                text_part = MimeText(message.text_content, 'plain', 'utf-8')
                msg.attach(text_part)
            
            # Conteúdo HTML
            if message.html_content:
                html_part = MimeText(message.html_content, 'html', 'utf-8')
                msg.attach(html_part)
            
            # Anexos
            if message.attachments:
                for attachment in message.attachments:
                    part = MimeBase('application', 'octet-stream')
                    part.set_payload(attachment.content)
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {attachment.filename}'
                    )
                    msg.attach(part)
            
            return msg
            
        except Exception as e:
            logging_service.error(
                "EmailService",
                "PREPARE_MESSAGE_ERROR",
                f"Erro na preparação da mensagem: {str(e)}"
            )
            return None
    
    def _send_via_smtp(self, msg: MimeMultipart, to_emails: List[str]) -> bool:
        """Enviar via SMTP"""
        try:
            context = ssl.create_default_context()
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.smtp_use_tls:
                    server.starttls(context=context)
                
                server.login(self.smtp_username, self.smtp_password)
                
                # Enviar para todos os destinatários
                all_recipients = to_emails[:]
                if msg.get('Cc'):
                    all_recipients.extend(msg.get('Cc').split(', '))
                if msg.get('Bcc'):
                    all_recipients.extend(msg.get('Bcc').split(', '))
                
                server.send_message(msg, to_addrs=all_recipients)
                
            return True
            
        except Exception as e:
            logging_service.error(
                "EmailService",
                "SMTP_ERROR",
                f"Erro no envio SMTP: {str(e)}"
            )
            return False
    
    def _load_templates(self):
        """Carregar templates de email"""
        # Templates básicos (em produção, carregar de arquivos ou banco)
        self.templates = {
            EmailType.WELCOME.value: EmailTemplate(
                name="welcome",
                subject="Bem-vindo ao POLARIS - {{ user_name }}",
                html_content="""
                <h2>Bem-vindo ao POLARIS, {{ user_name }}!</h2>
                <p>Sua conta foi criada com sucesso.</p>
                <p>Acesse o sistema: <a href="{{ login_url }}">{{ login_url }}</a></p>
                <p>Atenciosamente,<br>Equipe POLARIS</p>
                """,
                text_content="""
                Bem-vindo ao POLARIS, {{ user_name }}!
                
                Sua conta foi criada com sucesso.
                Acesse o sistema: {{ login_url }}
                
                Atenciosamente,
                Equipe POLARIS
                """,
                variables=["user_name", "login_url"]
            ),
            
            EmailType.PASSWORD_RESET.value: EmailTemplate(
                name="password_reset",
                subject="Reset de Senha - POLARIS",
                html_content="""
                <h2>Reset de Senha</h2>
                <p>Você solicitou um reset de senha.</p>
                <p>Clique no link para redefinir: <a href="{{ reset_url }}">Redefinir Senha</a></p>
                <p>Este link expira em {{ expiry_hours }} horas.</p>
                <p>Se você não solicitou este reset, ignore este email.</p>
                """,
                text_content="""
                Reset de Senha
                
                Você solicitou um reset de senha.
                Acesse: {{ reset_url }}
                
                Este link expira em {{ expiry_hours }} horas.
                Se você não solicitou este reset, ignore este email.
                """,
                variables=["reset_url", "expiry_hours"]
            ),
            
            EmailType.DOCUMENT_READY.value: EmailTemplate(
                name="document_ready",
                subject="Documento Pronto - {{ document_name }}",
                html_content="""
                <h2>Seu documento está pronto!</h2>
                <p>O documento "{{ document_name }}" foi gerado com sucesso.</p>
                <p>Faça o download: <a href="{{ download_url }}">Download</a></p>
                <p>Este link expira em {{ expiry_days }} dias.</p>
                """,
                text_content="""
                Seu documento está pronto!
                
                O documento "{{ document_name }}" foi gerado com sucesso.
                Download: {{ download_url }}
                
                Este link expira em {{ expiry_days }} dias.
                """,
                variables=["document_name", "download_url", "expiry_days"]
            ),
            
            EmailType.SYSTEM_ALERT.value: EmailTemplate(
                name="system_alert",
                subject="Alerta do Sistema - {{ alert_type }}",
                html_content="""
                <h2>Alerta do Sistema</h2>
                <p><strong>Tipo:</strong> {{ alert_type }}</p>
                <p><strong>Mensagem:</strong> {{ alert_message }}</p>
                <p><strong>Timestamp:</strong> {{ timestamp }}</p>
                <p>Acesse o sistema: <a href="{{ system_url }}">{{ system_url }}</a></p>
                """,
                text_content="""
                Alerta do Sistema
                
                Tipo: {{ alert_type }}
                Mensagem: {{ alert_message }}
                Timestamp: {{ timestamp }}
                
                Acesse o sistema: {{ system_url }}
                """,
                variables=["alert_type", "alert_message", "timestamp", "system_url"]
            )
        }
    
    def _get_template(self, template_type: EmailType) -> Optional[EmailTemplate]:
        """Obter template por tipo"""
        return self.templates.get(template_type.value)


# Instância global do email service
email_service = EmailService()

