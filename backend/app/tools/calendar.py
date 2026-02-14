from typing import List, Optional
from datetime import datetime, timedelta
from sqlmodel import select, Session
from langchain_core.tools import tool
from app.core.database.session import engine
from app.core.database.models import Appointment, Customer

@tool
def check_calendar_availability(agent_role: str, date_str: str) -> str:
    """
    Verifica disponibilidad en el calendario para un rol específico (sales/tech) en una fecha (YYYY-MM-DD).
    Retorna horarios ocupados.
    """
    try:
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return "Formato de fecha inválido. Usa YYYY-MM-DD."

    with Session(engine) as session:
        # Buscar citas ese día para ese rol
        statement = select(Appointment).where(
            Appointment.agent_role == agent_role,
            Appointment.datetime_slot >= datetime.combine(target_date, datetime.min.time()),
            Appointment.datetime_slot <= datetime.combine(target_date, datetime.max.time()),
            Appointment.status == "scheduled"
        )
        appointments = session.exec(statement).all()
        
        if not appointments:
            return f"Calendario de {agent_role} totalmente libre el {date_str} de 09:00 a 18:00."
            
        busy_slots = [apt.datetime_slot.strftime("%H:%M") for apt in appointments]
        return f"Horarios ocupados para {agent_role} el {date_str}: {', '.join(busy_slots)}. El resto está libre."

@tool
def schedule_appointment(client_email: str, agent_role: str, datetime_str: str, notes: str = "") -> str:
    """
    Agenda una cita. 
    datetime_str debe ser YYYY-MM-DD HH:MM.
    agent_role: 'sales' o 'tech'.
    """
    try:
        dt_slot = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")
    except ValueError:
        return "Formato inválido. Usa YYYY-MM-DD HH:MM"
        
    with Session(engine) as session:
        # 1. Validar cliente (Customer)
        customer = session.exec(select(Customer).where(Customer.email == client_email)).first()
        if not customer:
            return f"Error: No existe cliente con email {client_email}. Regístralo primero."
            
        # 2. Validar disponibilidad (simple)
        conflict = session.exec(select(Appointment).where(
            Appointment.agent_role == agent_role,
            Appointment.datetime_slot == dt_slot,
            Appointment.status == "scheduled"
        )).first()
        
        if conflict:
            return "Error: Ese horario ya está ocupado."
            
        # 3. Crear cita
        new_apt = Appointment(
            customer_id=customer.id,
            user_id=customer.user_id, # Asignar al mismo vendedor que el cliente
            agent_role=agent_role,
            datetime_slot=dt_slot,
            notes=notes
        )
        session.add(new_apt)
        session.commit()
        return f"Cita agendada exitosamente para {client_email} con {agent_role} el {datetime_str}."
