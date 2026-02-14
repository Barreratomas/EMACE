from datetime import datetime, timedelta, timezone
from apscheduler.schedulers.blocking import BlockingScheduler
from sqlmodel import Session, select

from app.core.database.session import engine
from app.core.database.models import (
    User,
    Product,
    Invoice,
    Appointment,
    AuditLog,
)
from app.core.comm.notifications import dispatch_notifications


INVOICE_DUE_DAYS = 3
APPOINTMENT_WINDOW_HOURS = 24
DEDUP_TTL_MINUTES = 60


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


def run_once() -> None:
    with Session(engine) as session:
        users = session.exec(select(User)).all()

        for user in users:
            _check_low_stock(session, user)
            _check_zero_stock_auto_pause(session, user)
            _check_invoice_due(session, user)
            _check_appointments(session, user)

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
