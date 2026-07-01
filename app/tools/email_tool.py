import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from app.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AutoFIR_Email")

def send_fir_pdf_email(recipient_email: str, complainant_name: str, fir_number: str, pdf_bytes: bytes) -> bool:
    """
    Sends the generated FIR PDF as an attachment to the complainant.
    Fails safely if SMTP settings are not configured or face errors.
    """
    # 1. Check Configuration Presence
    if not settings.EMAIL_USER or not settings.EMAIL_PASS:
        logger.warning("SMTP Email credentials not configured. Skipping email dispatch.")
        return False
        
    try:
        # 2. Build MIME Email Message
        msg = MIMEMultipart()
        msg['From'] = settings.EMAIL_USER
        msg['To'] = recipient_email
        msg['Subject'] = f"[OFFICIAL COPY] First Information Report - {fir_number}"
        
        body = f"""Dear {complainant_name},

This is an automated copy of the First Information Report (FIR) that has been registered under your name at the jurisdictional police station using the AutoFIR AI System.

Please find attached the official legal-grade PDF copy of your report.

FIR Number: {fir_number}
Report Date: {smtp_time_format()}

This copy is protected with a cryptographic block integrity ledger hash to ensure document security and prevent tampering.

Sincerely,
State Police Department
Government of India
"""
        msg.attach(MIMEText(body, 'plain'))
        
        # Attach PDF bytes
        filename = f"Official_FIR_{fir_number.replace('/', '_')}.pdf"
        attachment = MIMEApplication(pdf_bytes, _subtype="pdf")
        attachment.add_header('Content-Disposition', 'attachment', filename=filename)
        msg.attach(attachment)
        
        # 3. Connect and Send Email
        logger.info(f"Connecting to SMTP server {settings.EMAIL_HOST}:{settings.EMAIL_PORT}...")
        server = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT, timeout=8)
        server.starttls()
        server.login(settings.EMAIL_USER, settings.EMAIL_PASS)
        server.send_message(msg)
        server.quit()
        
        logger.info(f"FIR PDF email successfully sent to {recipient_email}!")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email to {recipient_email}: {str(e)}")
        return False

def smtp_time_format():
    from datetime import datetime
    return datetime.now().strftime("%d-%m-%Y %H:%M")
