"""Real SMTP send — a genuine SMTP transaction happens (caught locally by
Mailpit in dev, never actually delivered externally). Swapping to a real
production SMTP relay is a config change (app.config.settings.smtp_host/
port, plus auth if the relay needs it), not a code change.
"""

import smtplib
from email.mime.text import MIMEText

from app.config import settings

FROM_ADDRESS = "no-reply@fdr-portal.aicte.example"


def send_email(*, to_address: str, subject: str, body: str) -> None:
    message = MIMEText(body, "plain", "utf-8")
    message["Subject"] = subject
    message["From"] = FROM_ADDRESS
    message["To"] = to_address

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as client:
        client.send_message(message)
