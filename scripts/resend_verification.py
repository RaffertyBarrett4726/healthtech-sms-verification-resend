import argparse
import json

from healthtech_sms.infrai_client import InfraiClient
from healthtech_sms.service import AppointmentVerification, resend_if_stuck


def main() -> None:
    parser = argparse.ArgumentParser(description="Resend a stuck appointment verification SMS")
    parser.add_argument("appointment_id")
    parser.add_argument("patient_first_name")
    parser.add_argument("message_id")
    parser.add_argument("--state", default="pending")
    args = parser.parse_args()
    appointment = AppointmentVerification(args.appointment_id, args.patient_first_name, args.message_id, args.state)
    print(json.dumps(resend_if_stuck(appointment, InfraiClient.from_environment()), indent=2))


if __name__ == "__main__":
    main()

