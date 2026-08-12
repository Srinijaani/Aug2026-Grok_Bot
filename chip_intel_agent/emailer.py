"""Email the generated briefing PDF via SMTP."""

from __future__ import annotations

import logging
import mimetypes
import os
import smtplib
import ssl
from dataclasses import dataclass
from email.message import EmailMessage
from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULT_TO = "sriniwas.gattani@gmail.com"


@dataclass
class EmailConfig:
    host: str
    port: int
    username: str
    password: str
    mail_from: str
    mail_to: str
    use_starttls: bool = True

    @classmethod
    def from_env(cls) -> "EmailConfig":
        host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        port = int(os.getenv("SMTP_PORT", "587"))
        username = os.getenv("SMTP_USER", "").strip()
        password = os.getenv("SMTP_PASSWORD", "").strip()
        mail_from = os.getenv("EMAIL_FROM", username).strip()
        mail_to = os.getenv("EMAIL_TO", DEFAULT_TO).strip()
        if not username or not password:
            raise RuntimeError(
                "SMTP_USER and SMTP_PASSWORD must be set to send email. "
                "For Gmail, create an App Password and put it in SMTP_PASSWORD."
            )
        return cls(
            host=host,
            port=port,
            username=username,
            password=password,
            mail_from=mail_from or username,
            mail_to=mail_to or DEFAULT_TO,
            use_starttls=port in (587, 25),
        )


def build_message(
    pdf_path: Path,
    mail_from: str,
    mail_to: str,
    generated_at: str,
    stats: dict[str, int] | None = None,
) -> EmailMessage:
    stats = stats or {}
    msg = EmailMessage()
    msg["Subject"] = f"Chip Design & Manufacturing Briefing — {generated_at}"
    msg["From"] = mail_from
    msg["To"] = mail_to
    body = (
        "Hello,\n\n"
        "Attached is your automated 3-slide briefing on chip design and manufacturing technologies:\n"
        "  1. Trends\n"
        "  2. Company Logos\n"
        "  3. Geopolitical Impact\n\n"
        f"Generated: {generated_at}\n"
        f"Articles scraped: {stats.get('articles', 'n/a')}\n"
        f"YouTube videos scraped: {stats.get('videos', 'n/a')}\n"
        f"Sources used: {stats.get('sources', 'n/a')}\n\n"
        "This briefing was produced by the Chip Intel Agent from Anastasi In Tech "
        "(https://www.youtube.com/@AnastasiInTech) only.\n\n"
        "Regards,\n"
        "Chip Intel Agent\n"
    )
    msg.set_content(body)

    pdf_path = Path(pdf_path)
    ctype, _ = mimetypes.guess_type(str(pdf_path))
    maintype, subtype = (ctype or "application/pdf").split("/", 1)
    msg.add_attachment(
        pdf_path.read_bytes(),
        maintype=maintype,
        subtype=subtype,
        filename=pdf_path.name,
    )
    return msg


def send_pdf(pdf_path: Path, generated_at: str, stats: dict[str, int] | None = None) -> str:
    config = EmailConfig.from_env()
    message = build_message(
        pdf_path=pdf_path,
        mail_from=config.mail_from,
        mail_to=config.mail_to,
        generated_at=generated_at,
        stats=stats,
    )

    logger.info("Sending briefing to %s via %s:%s", config.mail_to, config.host, config.port)
    if config.use_starttls:
        context = ssl.create_default_context()
        with smtplib.SMTP(config.host, config.port, timeout=45) as server:
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
            server.login(config.username, config.password)
            server.send_message(message)
    else:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(config.host, config.port, context=context, timeout=45) as server:
            server.login(config.username, config.password)
            server.send_message(message)

    logger.info("Email sent successfully to %s", config.mail_to)
    return config.mail_to
