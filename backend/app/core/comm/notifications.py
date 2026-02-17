from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta, timezone
from sqlmodel import Session, select
from app.core.database.models import AuditLog, User, Customer, Invoice, Product, Appointment
from app.core.config import settings
import re

def _safe_import_aiosmtplib():
    try:
        import aiosmtplib  # type: ignore
        return aiosmtplib
    except Exception:
        return None

def _send_email(to: List[str], subject: str, body: str) -> Tuple[bool, str]:
    if not settings.SMTP_ENABLED:
        return False, "smtp_disabled"
    if not (settings.SMTP_HOST and settings.SMTP_PORT and settings.SMTP_FROM):
        return False, "smtp_not_configured"
    aiosmtplib = _safe_import_aiosmtplib()
    if aiosmtplib is None:
        return False, "smtp_library_missing"
    from email.message import EmailMessage
    msg = EmailMessage()
    msg["From"] = settings.SMTP_FROM
    msg["To"] = ", ".join(to)
    msg["Subject"] = subject
    msg.set_content(body)
    try:
        coro = aiosmtplib.send(
            msg,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            start_tls=True,
        )
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(coro)
        loop.close()
        return True, "sent"
    except Exception as e:
        return False, f"smtp_error:{str(e)}"
 

def _extract_kv(detail: str, key: str) -> Optional[str]:
    m = re.search(rf"{key}=([^\|]+)", detail)
    return m.group(1) if m else None

def _render_template(action: str, payload: Dict[str, str]) -> Tuple[str, str]:
    if action == "low_stock_alert":
        subject = f"Alerta de stock bajo: {payload.get('name','')}"
        body = (
            f"Producto: {payload.get('name','')}\n"
            f"Stock actual: {payload.get('stock','')}\n"
            f"Umbral: {payload.get('threshold','')}\n"
        )
        return subject, body
    if action == "invoice_due_soon":
        subject = f"Factura próxima a vencer: #{payload.get('invoice_id','')}"
        body = (
            f"Monto: ${payload.get('amount','')}\n"
            f"Vence: {payload.get('due_date','')}\n"
        )
        return subject, body
    if action == "appointment_upcoming":
        subject = "Recordatorio de cita próxima"
        body = (
            f"Rol: {payload.get('role','')}\n"
            f"Fecha y hora: {payload.get('datetime','')}\n"
        )
        return subject, body
    return "Notificación", "\n".join([f"{k}: {v}" for k, v in payload.items()])

def dispatch_notifications(session: Session) -> int:
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(minutes=10)
    events = session.exec(
        select(AuditLog).where(
            AuditLog.timestamp >= cutoff,
            AuditLog.action.in_(["low_stock_alert", "invoice_due_soon", "appointment_upcoming"]),
        )
    ).all()
    sent_count = 0
    for ev in events:
        action = ev.action
        dedup_key = None
        if action == "low_stock_alert":
            dedup_key = _extract_kv(ev.details, "product_id")
        elif action == "invoice_due_soon":
            dedup_key = _extract_kv(ev.details, "invoice_id")
        elif action == "appointment_upcoming":
            dedup_key = _extract_kv(ev.details, "appointment_id")
        if not dedup_key:
            continue
        existing = session.exec(
            select(AuditLog).where(
                AuditLog.user_id == ev.user_id,
                AuditLog.action == "notification_sent",
                AuditLog.details.contains(f"action={action}"),
                AuditLog.details.contains(dedup_key),
            )
        ).first()
        if existing:
            continue
        channels = []
        recipients: List[str] = []
        subject = ""
        body = ""
        payload: Dict[str, str] = {}
        if action == "low_stock_alert":
            product_id = int(dedup_key)
            product = session.exec(select(Product).where(Product.id == product_id)).first()
            user = session.exec(select(User).where(User.id == ev.user_id)).first()
            if user and user.email:
                recipients.append(user.email)
            payload = {
                "name": product.name if product else "",
                "stock": str(product.stock) if product and product.stock is not None else "",
                "threshold": str(product.min_stock_threshold) if product and product.min_stock_threshold is not None else "",
            }
            subject, body = _render_template(action, payload)
        elif action == "invoice_due_soon":
            invoice_id = int(dedup_key)
            invoice = session.exec(select(Invoice).where(Invoice.id == invoice_id)).first()
            customer = session.exec(select(Customer).where(Customer.id == invoice.customer_id)).first() if invoice else None
            if customer and customer.email:
                recipients.append(customer.email)
            user = session.exec(select(User).where(User.id == ev.user_id)).first()
            if user and user.email:
                recipients.append(user.email)
            payload = {
                "invoice_id": str(invoice_id),
                "amount": str(invoice.amount) if invoice else "",
                "due_date": invoice.due_date.isoformat() if invoice else "",
            }
            subject, body = _render_template(action, payload)
        elif action == "appointment_upcoming":
            appointment_id = int(dedup_key)
            appointment = session.exec(select(Appointment).where(Appointment.id == appointment_id)).first()
            customer = session.exec(select(Customer).where(Customer.id == appointment.customer_id)).first() if appointment else None
            if customer and customer.email:
                recipients.append(customer.email)
            user = session.exec(select(User).where(User.id == ev.user_id)).first()
            if user and user.email:
                recipients.append(user.email)
            payload = {
                "role": appointment.agent_role if appointment else "",
                "datetime": appointment.datetime_slot.isoformat() if appointment else "",
            }
            subject, body = _render_template(action, payload)
        email_ok, email_msg = _send_email(recipients, subject, body) if recipients else (False, "no_recipients")
        if email_ok:
            channels.append("email")
        result = "sent" if email_ok else "dry_run"
        log = AuditLog(
            user_id=ev.user_id,
            agent_name="Notifier",
            action="notification_sent",
            details=f"action={action}|{dedup_key}|channels={channels}|email={email_msg}|recipients={','.join(recipients)}",
            timestamp=datetime.now(timezone.utc),
        )
        session.add(log)
        sent_count += 1
    return sent_count

def send_email_notification(session: Session, user_id: int, to: List[str], subject: str, body: str) -> str:
    ok, msg = _send_email(to, subject, body)
    log = AuditLog(
        user_id=user_id,
        agent_name="Notifier",
        action="notification_sent",
        details=f"manual_email|channels={[ 'email' if ok else 'dry_run' ]}|result={msg}|recipients={','.join(to)}",
        timestamp=datetime.now(timezone.utc),
    )
    session.add(log)
    return "Enviado" if ok else f"Dry-Run ({msg})"
