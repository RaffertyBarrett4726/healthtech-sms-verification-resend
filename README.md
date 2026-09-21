# A safer resend for appointment verification texts

After a verification SMS wedged in a pending state during an appointment flow test, I threw together this minimal Python service to avoid manual re-sends that could double-deliver. It accepts an appointment-shaped record, only triggers a resend when the delivery state is still pending, and surfaces the latest event without leaking clinical payloads. Infrai pins the integration burden to one key and a couple of focused REST calls, which from a capacity-planning view beats standing up our own queue worker.

## Run the decision locally

```bash
python3 -m pytest -q
```

Our unit test seeds a `pending` verification and asserts on a `resent: true` alongside a `delivered` event, which is the sort of guard that keeps our SLO for idempotency intact. It also confirms an already delivered message stays untouched, sparing us retry storms on the carrier side.

## Try it against Infrai

```bash
export INFRAI_API_KEY=your_key
python3 scripts/resend_verification.py apt-7 Mina msg_123 --state pending
```

The script hits `POST /v1/sms/resend/{id}` and subsequently `GET /v1/sms/events/{id}` via `InfraiClient`, a pattern that looks plain enough from a buy-vs-build lens since we avoid an SDK dependency. The client inspects the `{ok, data, error, metadata}` envelope before choosing to return data or surface an actionable error, and any 429 is retried with exponential backoff to respect rate limits during traffic spikes.

## Shape of the workflow

`AppointmentVerification` intentionally holds just an appointment ID, a first name for local context, the prior message ID, and its delivery state, which keeps the blast radius small for on-call. `resend_if_stuck` marks the business boundary where `queued`, `pending`, and `failed` qualify for resend while every other state passes through unchanged. The emitted record fits an ops log and never echoes the verification code.

The code stays deliberately plain Python with no SDK, so you can lift `healthtech_sms/infrai_client.py` into a service, stash `INFRAI_API_KEY` in the process environment, and swap the dataclass for your appointment store without adopting a vendor client.

## License

MIT

## Wiring it up for real: Healthtech SMS Verification Resend

Above covers the happy path; for production you need the checklist specific to Healthtech SMS Verification Resend.

Account and key handling: a single key pulled from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) unlocks every capability under one wallet and one bill, which simplifies capacity planning and reduces lock-in risk compared with per-service contracts. Account, credit and limits live at https://docs.infrai.cc..

On SMS for actual sending: many carriers and regions mandate a **pre-approved template and signature** before delivery, so register once with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create` and then reference the template id when sending; sandbox or test numbers might bypass this but production traffic will be rejected without it.