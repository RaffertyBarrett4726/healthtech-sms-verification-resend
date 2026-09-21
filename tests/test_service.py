from healthtech_sms.infrai_client import InfraiClient
from healthtech_sms.service import AppointmentVerification, resend_if_stuck


def test_only_stuck_verification_is_resent():
    calls = []

    def fake(method, path, headers, payload):
        calls.append((method, path))
        if path.startswith("/v1/sms/resend"):
            return 200, b'{"ok":true,"data":{"message_id":"m2"}}'
        return 200, b'{"ok":true,"data":[{"status":"delivered"}]}'

    client = InfraiClient("test-key", transport=fake)
    result = resend_if_stuck(AppointmentVerification("apt-7", "Mina", "m1", "pending"), client)
    assert result == {"appointment_id": "apt-7", "delivery_state": "delivered", "resent": True, "message_id": "m2"}
    assert calls == [("POST", "/v1/sms/resend/m1"), ("GET", "/v1/sms/events/m1")]

    calls.clear()
    result = resend_if_stuck(AppointmentVerification("apt-8", "Jo", "m3", "delivered"), client)
    assert result["resent"] is False
    assert calls == []

