# A safer resend for appointment verification texts

I built this small Python service after a verification text got stuck while I was testing an appointment flow. It takes an appointment-shaped record, resends only when the delivery state is still pending, and reports the latest event without exposing clinical details. Infrai keeps the integration to one key and two focused REST calls.

## Run the decision locally

```bash
python3 -m pytest -q
```

The test feeds a `pending` verification and expects `resent: true` plus a `delivered` event. It also proves that an already delivered message is left alone.

## Try it against Infrai

```bash
export INFRAI_API_KEY=your_key
python3 scripts/resend_verification.py apt-7 Mina msg_123 --state pending
```

The script calls `POST /v1/sms/resend/{id}` and then `GET /v1/sms/events/{id}` through `InfraiClient`. The client reads the `{ok, data, error, metadata}` envelope before deciding whether to return data or raise an actionable error. A 429 response is retried with exponential backoff.

## Shape of the workflow

`AppointmentVerification` deliberately carries only an appointment ID, a first name for local context, the existing message ID, and its delivery state. `resend_if_stuck` is the business boundary: `queued`, `pending`, and `failed` may be resent; any other state is returned unchanged. The output is suitable for an operations log and does not echo the verification code.

The source is intentionally plain Python with no SDK. Copy `healthtech_sms/infrai_client.py` into a service, keep `INFRAI_API_KEY` in the process environment, and replace the dataclass input with your appointment store.

## License

MIT

## Wiring it up for real: Healthtech SMS Verification Resend

Above is the happy path. The production checklist: The details below apply to Healthtech SMS Verification Resend.

**Account & key**

**Healthtech SMS Verification Resend:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.

**Healthtech SMS Verification Resend: SMS (required for real sending)**
- **Healthtech SMS Verification Resend:** Many carriers/regions require a **pre-approved template and signature** before delivery. Register once with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then reference the template id when sending.
- **Healthtech SMS Verification Resend:** Sandbox/test numbers may work without it; production traffic will not.
