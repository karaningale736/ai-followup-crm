import os
from dataclasses import dataclass
from datetime import datetime
from email.header import decode_header
from email.parser import Parser
from typing import Any, List, Optional


@dataclass
class InboxMessage:
    from_email: str
    subject: str
    body: str
    message_id: str
    received_at: Optional[datetime] = None


class InboxMonitorError(RuntimeError):
    pass


def _decode_header_value(value: Optional[str]) -> str:
    if not value:
        return ""
    decoded = []
    for part, encoding in decode_header(value):
        if isinstance(part, bytes):
            try:
                decoded.append(part.decode(encoding or "utf-8", errors="replace"))
            except Exception:
                decoded.append(part.decode("utf-8", errors="replace"))
        else:
            decoded.append(part)
    return "".join(decoded)


def _normalize_body(raw_message: Any) -> str:
    if hasattr(raw_message, "get_body"):
        try:
            text = raw_message.get_body(preferencelist=("plain", "html")).get_content()
            if text:
                return text.strip()
        except Exception:
            pass

    payload = raw_message
    if hasattr(payload, "get_payload") and isinstance(payload.get_payload(), list):
        text_parts = []
        for part in payload.get_payload():
            if part.get_content_type() == "text/plain":
                text_parts.append(part.get_payload(decode=True).decode(part.get_content_charset() or "utf-8", errors="replace"))
        if text_parts:
            return "\n".join(text_parts).strip()

    if hasattr(payload, "get_body"):
        try:
            return payload.get_body(preferencelist=("plain", "html")).get_content().strip()
        except Exception:
            pass

    if hasattr(payload, "get_payload"):
        raw = payload.get_payload(decode=True)
        if isinstance(raw, bytes):
            return raw.decode("utf-8", errors="replace").strip()

    return ""


def fetch_incoming_messages(config: Optional[dict] = None) -> List[InboxMessage]:
    """Fetch the latest incoming email messages from the configured IMAP mailbox.

    This is intentionally lightweight and works with any IMAP server that supports
    standard Python imaplib. If no mailbox config is present, it simply returns an
    empty list so the app can still run in mock mode.
    """
    cfg = config or {
        "imap_host": os.getenv("IMAP_HOST"),
        "imap_port": int(os.getenv("IMAP_PORT", "993")),
        "username": os.getenv("IMAP_USERNAME"),
        "password": os.getenv("IMAP_PASSWORD"),
        "mailbox": os.getenv("IMAP_MAILBOX", "INBOX"),
        "use_ssl": os.getenv("IMAP_USE_SSL", "true").lower() in {"1", "true", "yes", "on"},
    }

    if not cfg.get("imap_host") or not cfg.get("username") or not cfg.get("password"):
        return []

    try:
        import imaplib
    except ImportError as exc:
        raise InboxMonitorError("imaplib is not available") from exc

    try:
        smtp_class = imaplib.IMAP4_SSL if cfg.get("use_ssl", True) else imaplib.IMAP4
        with smtp_class(cfg["imap_host"], int(cfg.get("imap_port", 993))) as server:
            server.login(cfg["username"], cfg["password"])
            server.select(cfg.get("mailbox", "INBOX"))
            _, data = server.search(None, "ALL")
            msg_ids = [item.decode("utf-8") for item in data[0].split()] if data and data[0] else []

            messages: List[InboxMessage] = []
            for msg_id in reversed(msg_ids[-20:]):
                _, payload = server.fetch(msg_id.encode("utf-8"), "(RFC822)")
                raw_email = payload[0][1]
                if isinstance(raw_email, bytes):
                    email_message = Parser().parsestr(raw_email.decode("utf-8", errors="replace"))
                else:
                    email_message = Parser().parsestr(raw_email)

                from_value = _decode_header_value(email_message.get("From", ""))
                subject = _decode_header_value(email_message.get("Subject", ""))
                body = _normalize_body(email_message)
                message_id = _decode_header_value(email_message.get("Message-ID", "")) or msg_id
                received_at = None
                try:
                    received_at = datetime.strptime(email_message.get("Date", ""), "%a, %d %b %Y %H:%M:%S %z")
                except Exception:
                    try:
                        received_at = datetime.strptime(email_message.get("Date", ""), "%a, %d %b %Y %H:%M:%S")
                    except Exception:
                        received_at = datetime.utcnow()

                messages.append(
                    InboxMessage(
                        from_email=from_value,
                        subject=subject,
                        body=body,
                        message_id=message_id,
                        received_at=received_at,
                    )
                )

            return messages
    except Exception:
        return []
    
