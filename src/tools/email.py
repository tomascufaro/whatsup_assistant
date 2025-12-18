"""
Email handling tool (SMTP integration).
"""

import os
import smtplib
from typing import Optional
import logging
import time
from langchain.tools import BaseTool
from pydantic import BaseModel, Field, ConfigDict
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from logging_setup import get_request_id


class EmailInput(BaseModel):
    """Input schema for email operations."""
    action: str = Field(description="Acción: 'send' para enviar un email")
    to: Optional[str] = Field(default=None, description="Email del destinatario (para enviar). Si no se proporciona, usa el email por defecto.")
    subject: Optional[str] = Field(default=None, description="Asunto del email (para enviar)")
    body: Optional[str] = Field(default=None, description="Cuerpo del email (para enviar)")


class EmailTool(BaseTool):
    """Tool for sending emails via SMTP."""
    
    name: str = "email"
    description: str = "Envía emails usando SMTP. Usa 'send' para enviar un email. Requiere: to (opcional, usa default si no se proporciona), subject, body."
    args_schema: type[BaseModel] = EmailInput
    
    model_config = ConfigDict(extra='allow')  # Allow extra fields for SMTP config
    
    def __init__(self):
        super().__init__()
        # Load SMTP configuration from environment
        # Use object.__setattr__ to bypass Pydantic validation for these
        # Accept both SMTP_HOST and SMTP_SERVER for compatibility
        object.__setattr__(self, 'smtp_host', os.getenv("SMTP_HOST") or os.getenv("SMTP_SERVER"))
        object.__setattr__(self, 'smtp_port', int(os.getenv("SMTP_PORT", "587")))
        object.__setattr__(self, 'smtp_user', os.getenv("SMTP_USER"))
        object.__setattr__(self, 'smtp_password', os.getenv("SMTP_PASSWORD"))
        # EMAIL_FROM is optional - defaults to SMTP_USER if not set
        smtp_user = os.getenv("SMTP_USER")
        object.__setattr__(self, 'email_from', os.getenv("EMAIL_FROM") or smtp_user)
        object.__setattr__(self, 'email_default_to', os.getenv("EMAIL_TO") or os.getenv("EMAIL_TO_DEFAULT"))
        
        # Validate configuration (but don't fail if missing - will fail when used)
        object.__setattr__(self, '_is_configured', all([
            self.smtp_host,
            self.smtp_user,
            self.smtp_password,
            self.email_from  # Will be set from SMTP_USER if EMAIL_FROM not provided
        ]))
    
    def _send_email(self, to: str, subject: str, body: str) -> str:
        """Send email via SMTP."""
        if not self._is_configured:
            missing = []
            if not self.smtp_host:
                missing.append("SMTP_HOST")
            if not self.smtp_user:
                missing.append("SMTP_USER")
            if not self.smtp_password:
                missing.append("SMTP_PASSWORD")
            if not self.email_from:
                missing.append("EMAIL_FROM o SMTP_USER")
            raise ValueError(
                f"SMTP no está configurado. Faltan: {', '.join(missing)}. "
                "Por favor configura las variables de entorno SMTP_* en Modal secrets."
            )
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = self.email_from
        msg['To'] = to
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # Send via SMTP
        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()  # Enable encryption
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            return f"Email enviado exitosamente a {to}"
        except smtplib.SMTPAuthenticationError as e:
            raise ValueError(f"Error de autenticación SMTP: {str(e)}")
        except smtplib.SMTPException as e:
            raise ValueError(f"Error al enviar email: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error inesperado: {str(e)}")
    
    def _run(self, action: str, to: Optional[str] = None,
             subject: Optional[str] = None, body: Optional[str] = None,
             query: Optional[str] = None) -> str:
        """Execute email operation."""
        log = logging.getLogger("tool")
        start = time.time()
        request_id = get_request_id()
        
        try:
            if action == "send":
                # Use default recipient if not provided
                recipient = to or self.email_default_to
                
                if not recipient:
                    return "Error: No se proporcionó destinatario y no hay email por defecto configurado. Usa 'to' o configura EMAIL_TO."
                
                if not subject:
                    return "Error: El asunto es requerido para enviar un email."
                
                if not body:
                    return "Error: El cuerpo del email es requerido."
                
                result = self._send_email(recipient, subject, body)
                
                log.info("tool_call", extra={
                    "stage": "tool_call",
                    "tool": self.name,
                    "request_id": request_id,
                    "action": action,
                    "to": recipient,
                    "duration_ms": int((time.time() - start) * 1000),
                })
                
                return result
            
            elif action == "read":
                return "La lectura de emails no está disponible con SMTP. Solo se puede enviar emails."
            
            else:
                return f"Acción desconocida: {action}. Usa 'send' para enviar un email."
        
        except ValueError as e:
            # Configuration or validation errors
            error_msg = str(e)
            log.warning("tool_config_error", extra={
                "stage": "tool_config_error",
                "tool": self.name,
                "request_id": request_id,
                "action": action,
                "error": error_msg,
            })
            return error_msg
        except Exception as e:
            log.error("tool_error", extra={
                "stage": "tool_error",
                "tool": self.name,
                "request_id": request_id,
                "action": action,
                "duration_ms": int((time.time() - start) * 1000),
                "error": str(e),
            })
            return f"Error: {str(e)}"
