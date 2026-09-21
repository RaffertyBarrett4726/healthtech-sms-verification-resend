from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .infrai_client import InfraiClient


@dataclass(frozen=True)
class AppointmentVerification:
    appointment_id: str
    patient_first_name: str
    message_id: str
    delivery_state: str


def resend_if_stuck(appointment: AppointmentVerification, client: InfraiClient) -> dict[str, Any]:
    """Resend only a pending verification and return a patient-safe status."""
    if appointment.delivery_state.lower() not in {"queued", "pending", "failed"}:
        return {"appointment_id": appointment.appointment_id, "delivery_state": appointment.delivery_state, "resent": False}
    result = client.resend_sms(appointment.message_id)
    events = client.sms_events(appointment.message_id)
    return {
        "appointment_id": appointment.appointment_id,
        "delivery_state": (events[-1].get("status") if isinstance(events, list) and events else "queued"),
        "resent": True,
        "message_id": result.get("message_id", appointment.message_id) if isinstance(result, dict) else appointment.message_id,
    }

