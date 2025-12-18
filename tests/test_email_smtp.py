"""Simple SMTP test without LangChain dependencies."""

import os
import sys
import smtplib
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()


def test_smtp_connection():
    """Test SMTP connection and email sending."""
    print("=" * 50)
    print("Testing SMTP Email Functionality")
    print("=" * 50)
    
    # Check environment variables
    print("\n1. Checking environment variables...")
    smtp_host = os.getenv("SMTP_HOST") or os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    email_from = os.getenv("EMAIL_FROM") or smtp_user
    email_to = os.getenv("EMAIL_TO")
    
    # Accept both SMTP_HOST and SMTP_SERVER
    smtp_host = smtp_host or os.getenv("SMTP_SERVER")
    required = {
        "SMTP_HOST/SMTP_SERVER": smtp_host,
        "SMTP_USER": smtp_user,
        "SMTP_PASSWORD": smtp_password,
    }
    
    missing = [key for key, value in required.items() if not value]
    
    if missing:
        print(f"❌ Missing: {', '.join(missing)}")
        return False
    
    print("✅ All required variables found")
    print(f"   SMTP_HOST: {smtp_host}")
    print(f"   SMTP_PORT: {smtp_port}")
    print(f"   SMTP_USER: {smtp_user}")
    print(f"   EMAIL_FROM: {email_from}")
    print(f"   EMAIL_TO: {email_to or 'Not set'}")
    
    # Test SMTP connection
    print("\n2. Testing SMTP connection...")
    try:
        server = smtplib.SMTP(smtp_host, smtp_port)
        server.starttls()
        print("✅ TLS connection established")
        
        print("3. Testing authentication...")
        server.login(smtp_user, smtp_password)
        print("✅ Authentication successful")
        
        # Test email sending
        print("\n4. Sending test email...")
        recipient = email_to or smtp_user
        print(f"   To: {recipient}")
        
        msg = MIMEMultipart()
        msg['From'] = email_from
        msg['To'] = recipient
        msg['Subject'] = "Test Email from WhatsApp Assistant"
        
        body = "Este es un email de prueba. Si recibes esto, el sistema de email funciona correctamente."
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        server.send_message(msg)
        server.quit()
        
        print(f"✅ Email sent successfully!")
        print(f"\n📧 Check your inbox at: {recipient}")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ Authentication failed: {e}")
        print("\nTip: For Gmail, make sure you're using an App Password, not your regular password.")
        return False
    except smtplib.SMTPException as e:
        print(f"❌ SMTP error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_smtp_connection()
    print("\n" + "=" * 50)
    if success:
        print("✅ SMTP test PASSED")
    else:
        print("❌ SMTP test FAILED")
    print("=" * 50)
    sys.exit(0 if success else 1)

