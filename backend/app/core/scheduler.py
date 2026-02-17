from datetime import datetime, timedelta, timezone
from apscheduler.schedulers.blocking import BlockingScheduler
from sqlmodel import Session, select
import httpx

from app.core.database.session import engine
from app.core.database.models import (
    User,
    Product,
    Invoice,
    Appointment,
    AuditLog,
    VendorAccessState,
    BillingEvent,
    VendorAccessAudit,
    VendorTelegramIntegration,
    VendorMtprotoSession,
)
from app.core.comm.notifications import dispatch_notifications
from app.core.security import decrypt_secret
from app.core.telegram_mtproto import mtproto_manager


INVOICE_DUE_DAYS = 3
APPOINTMENT_WINDOW_HOURS = 24
DEDUP_TTL_MINUTES = 60
TELEGRAM_HEALTH_RETRIES = 2


def _log_event(
    session: Session,
    user_id: int,
    action: str,
    details: str,
    dedup_key: str | None = None,
) -> None:
    now = datetime.now(timezone.utc)

    if dedup_key:
        cutoff = now - timedelta(minutes=DEDUP_TTL_MINUTES)
        existing = session.exec(
            select(AuditLog).where(
                AuditLog.user_id == user_id,
                AuditLog.action == action,
                AuditLog.details.contains(dedup_key),
                AuditLog.timestamp >= cutoff,
            )
        ).first()
        if existing:
            return

    log = AuditLog(
        user_id=user_id,
        agent_name="Scheduler",
        action=action,
        details=details,
        timestamp=now,
    )
    session.add(log)


def _check_low_stock(session: Session, user: User) -> None:
    products = session.exec(
        select(Product).where(
            Product.user_id == user.id,
            Product.status == "active",
            Product.stock != None,
            Product.min_stock_threshold != None,
            Product.stock <= Product.min_stock_threshold,
        )
    ).all()

    for product in products:
        dedup_key = f"product:{product.id}"
        details = (
            f"low_stock_alert|user_id={user.id}|product_id={product.id}|"
            f"name={product.name}|stock={product.stock}|"
            f"threshold={product.min_stock_threshold}"
        )
        _log_event(
            session=session,
            user_id=user.id,
            action="low_stock_alert",
            details=details,
            dedup_key=dedup_key,
        )


def _check_zero_stock_auto_pause(session: Session, user: User) -> None:
    """Pausa automáticamente productos con stock 0"""
    products = session.exec(
        select(Product).where(
            Product.user_id == user.id,
            Product.status == "active",
            Product.type == "physical",
            Product.stock == 0,
        )
    ).all()

    for product in products:
        # Pausar el producto
        product.status = "paused"
        session.add(product)
        
        dedup_key = f"auto_pause:{product.id}"
        details = (
            f"auto_pause_zero_stock|user_id={user.id}|product_id={product.id}|"
            f"name={product.name}|stock=0|action=paused_automatically"
        )
        _log_event(
            session=session,
            user_id=user.id,
            action="auto_pause_zero_stock",
            details=details,
            dedup_key=dedup_key,
        )
    
    if products:
        session.commit()


def _check_invoice_due(session: Session, user: User) -> None:
    now = datetime.now(timezone.utc)
    horizon = now + timedelta(days=INVOICE_DUE_DAYS)

    invoices = session.exec(
        select(Invoice).where(
            Invoice.user_id == user.id,
            Invoice.status == "pending",
            Invoice.due_date >= now,
            Invoice.due_date <= horizon,
        )
    ).all()

    for invoice in invoices:
        dedup_key = f"invoice:{invoice.id}"
        details = (
            f"invoice_due_soon|user_id={user.id}|invoice_id={invoice.id}|"
            f"amount={invoice.amount}|due_date={invoice.due_date.isoformat()}"
        )
        _log_event(
            session=session,
            user_id=user.id,
            action="invoice_due_soon",
            details=details,
            dedup_key=dedup_key,
        )


def _check_appointments(session: Session, user: User) -> None:
    now = datetime.now(timezone.utc)
    horizon = now + timedelta(hours=APPOINTMENT_WINDOW_HOURS)

    appointments = session.exec(
        select(Appointment).where(
            Appointment.user_id == user.id,
            Appointment.status == "scheduled",
            Appointment.datetime_slot >= now,
            Appointment.datetime_slot <= horizon,
        )
    ).all()

    for appointment in appointments:
        dedup_key = f"appointment:{appointment.id}"
        details = (
            f"appointment_upcoming|user_id={user.id}|appointment_id={appointment.id}|"
            f"role={appointment.agent_role}|datetime={appointment.datetime_slot.isoformat()}"
        )
        _log_event(
            session=session,
            user_id=user.id,
            action="appointment_upcoming",
            details=details,
            dedup_key=dedup_key,
        )


def _check_trial_expiration(session: Session, user: User) -> None:
    now = datetime.now(timezone.utc)
    state = session.exec(
        select(VendorAccessState).where(
            VendorAccessState.vendor_id == user.id
        )
    ).first()
    if not state:
        return
    if state.source == "trial" and state.valid_until and state.valid_until <= now:
        dedup_key = f"trial_expired:{user.id}"
        details = (
            f"trial_expired|user_id={user.id}|valid_until={state.valid_until.isoformat()}"
        )
        _log_event(
            session=session,
            user_id=user.id,
            action="trial_expired",
            details=details,
            dedup_key=dedup_key,
        )
        be = BillingEvent(
            vendor_id=user.id,
            event_type="trial_expired",
            mp_event_id=None,
            raw_payload=None,
            normalized={"vendor_id": user.id, "valid_until": state.valid_until.isoformat()},
            created_at=now,
        )
        session.add(be)
        vaa = VendorAccessAudit(
            vendor_id=user.id,
            actor_user_id=None,
            action="set_trial_expired",
            old_state={"source": "trial"},
            new_state={"source": "trial", "expired": True},
            created_at=now,
        )
        session.add(vaa)


def _telegram_health_check(session: Session) -> None:
    integrations = session.exec(
        select(VendorTelegramIntegration).where(
            VendorTelegramIntegration.is_active == True,
            VendorTelegramIntegration.state == "active",
        )
    ).all()
    for integration in integrations:
        try:
            token = decrypt_secret(integration.bot_token_encrypted)
        except Exception as e:
            error_msg = f"decrypt_error:{str(e)[:100]}"
            integration.last_error = error_msg
            session.add(integration)
            dedup_key = f"telegram_health:{integration.vendor_id}"
            details = (
                f"telegram_health_failed|user_id={integration.vendor_id}|"
                f"bot_username={integration.bot_username}|error={error_msg}"
            )
            _log_event(
                session=session,
                user_id=integration.vendor_id,
                action="telegram_integration_error",
                details=details,
                dedup_key=dedup_key,
            )
            continue

        ok = False
        error_msg = ""
        for attempt in range(TELEGRAM_HEALTH_RETRIES):
            try:
                with httpx.Client(timeout=5) as client:
                    resp = client.get(f"https://api.telegram.org/bot{token}/getMe")
                if resp.status_code == 200 and resp.json().get("ok"):
                    ok = True
                    break
                error_msg = f"telegram_health_status:{resp.status_code}"
            except httpx.HTTPError as e:
                error_msg = f"telegram_health_http_error:{str(e)[:100]}"

        if ok:
            if integration.last_error:
                integration.last_error = None
                session.add(integration)
            dedup_key = f"telegram_health_ok:{integration.vendor_id}"
            details = (
                f"telegram_integration_ok|user_id={integration.vendor_id}|"
                f"bot_username={integration.bot_username}"
            )
            _log_event(
                session=session,
                user_id=integration.vendor_id,
                action="telegram_integration_ok",
                details=details,
                dedup_key=dedup_key,
            )
        else:
            integration.last_error = error_msg[:500]
            session.add(integration)
            dedup_key = f"telegram_health_failed:{integration.vendor_id}"
            details = (
                f"telegram_health_failed|user_id={integration.vendor_id}|"
                f"bot_username={integration.bot_username}|error={error_msg}"
            )
            _log_event(
                session=session,
                user_id=integration.vendor_id,
                action="telegram_integration_error",
                details=details,
                dedup_key=dedup_key,
            )


def _mtproto_heartbeat(session: Session) -> None:
    records = session.exec(
        select(VendorMtprotoSession).where(VendorMtprotoSession.enabled == True)
    ).all()
    now = datetime.now(timezone.utc)
    for record in records:
        record.last_heartbeat_at = now
        record.status = record.status or "enabled"
        session.add(record)
        details = (
            f"mtproto_heartbeat|user_id={record.vendor_id}|status={record.status}"
        )
        _log_event(
            session=session,
            user_id=record.vendor_id,
            action="mtproto_heartbeat",
            details=details,
            dedup_key=f"mtproto_heartbeat:{record.vendor_id}",
        )
    if records:
        session.commit()


def _billing_sanitize(session: Session) -> None:
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=1)
    pending = session.exec(
        select(BillingEvent).where(
            BillingEvent.event_type == "unassigned_event",
            BillingEvent.created_at >= cutoff,
        )
    ).all()
    for ev in pending:
        details = f"billing_sanitize_pending|event_id={ev.id}|created_at={ev.created_at.isoformat()}"
        _log_event(
            session=session,
            user_id=ev.vendor_id or 0,
            action="billing_sanitize_pending",
            details=details,
        )


def _check_telegram_integrations(session: Session) -> None:
    integrations = session.exec(
        select(VendorTelegramIntegration).where(VendorTelegramIntegration.last_error != None)
    ).all()
    for integration in integrations:
        dedup_key = f"telegram_integration_error:{integration.vendor_id}"
        details = (
            f"telegram_integration_error|user_id={integration.vendor_id}|"
            f"bot_username={integration.bot_username}|last_error={integration.last_error}"
        )
        _log_event(
            session=session,
            user_id=integration.vendor_id,
            action="telegram_integration_error",
            details=details,
            dedup_key=dedup_key,
        )

def run_once() -> None:
    with Session(engine) as session:
        users = session.exec(select(User)).all()

        for user in users:
            _check_low_stock(session, user)
            _check_zero_stock_auto_pause(session, user)
            _check_invoice_due(session, user)
            _check_appointments(session, user)
            _check_trial_expiration(session, user)

        _billing_sanitize(session)
        _telegram_health_check(session)
        _check_telegram_integrations(session)
        _mtproto_heartbeat(session)
        session.commit()
        dispatch_notifications(session)
        session.commit()


def run_scheduler() -> None:
    scheduler = BlockingScheduler(timezone=timezone.utc)
    scheduler.add_job(
        run_once,
        "interval",
        minutes=5,
        id="business_rules_scheduler",
        max_instances=1,
        replace_existing=True,
    )
    scheduler.start()
