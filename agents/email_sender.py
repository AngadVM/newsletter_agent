import smtplib
import os
import yaml
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def load_config():
    """Load configuration from both .env and config.yaml"""
    try:
        with open("config/config.yaml", "r") as f:
            config = yaml.safe_load(f)
    except Exception as e:
        print(f" Warning: Could not load config.yaml: {str(e)}")
        config = {}

    email_config = config.get("email", {})
    
    return {
        "smtp_server": os.getenv("SMTP_SERVER", email_config.get("smtp_server", "smtp.gmail.com")),
        "smtp_port": int(os.getenv("SMTP_PORT", str(email_config.get("port", "587")))),
        "email_user": os.getenv("EMAIL_SENDER", email_config.get("sender")),
        "email_pass": os.getenv("EMAIL_PASS"),
        "recipients": os.getenv("EMAIL_RECEIVER", email_config.get("receiver", "user@example.com")).split(","),
        "subject": email_config.get("subject", "Weekly Stack Overflow Insights")
    }

# Load configuration
CONFIG = load_config()

def send_email(recipient: str, subject: str, html_file: str) -> bool:
    """Sends newsletter via SMTP with proper SSL handling."""
    if not CONFIG["email_user"] or not CONFIG["email_pass"]:
        print(" Error: Email credentials not found in environment variables")
        return False
    
    # Read HTML content
    try:
        with open(html_file, "r") as file:
            html_content = file.read()
    except Exception as e:
        print(f" Error reading newsletter file: {str(e)}")
        return False

    msg = MIMEMultipart()
    msg["From"] = CONFIG["email_user"]
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.attach(MIMEText(html_content, "html"))

    # Secure the SMTP connection
    context = ssl.create_default_context()
    
    try:
        with smtplib.SMTP(CONFIG["smtp_server"], CONFIG["smtp_port"]) as server:
            server.starttls(context=context)  # Ensure secure connection
            server.login("apikey", CONFIG["email_pass"])  # Use "apikey" for SendGrid login
            server.send_message(msg)
            print(f" Email sent to {recipient}")
            return True
    except Exception as e:
        print(f" Error sending email: {str(e)}")
        return False

# Main execution
if __name__ == "__main__":
    for recipient in CONFIG["recipients"]:
        send_email(
            recipient=recipient.strip(),
            subject=CONFIG["subject"],
            html_file="data/output_newsletter/newsletter.html"
        )

