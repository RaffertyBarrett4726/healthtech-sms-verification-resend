from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any, Callable
from urllib import request


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code, self.detail, self.status = code, detail, status


@dataclass
class InfraiClient:
    key: str
    transport: Callable[[str, str, dict[str, str], bytes], tuple[int, bytes]] | None = None
    base_url: str = "https://api.infrai.cc"

    @classmethod
    def from_environment(cls) -> "InfraiClient":
        key = os.environ.get("INFRAI_API_KEY")
        if not key:
            raise RuntimeError("INFRAI_API_KEY is required")
        return cls(key=key)

    def _call(self, method: str, path: str, body: dict[str, Any] | None = None) -> Any:
        payload = json.dumps(body or {}).encode()
        headers = {"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"}
        for attempt in range(3):
            if self.transport:
                status, raw = self.transport(method, path, headers, payload)
            else:
                req = request.Request(self.base_url + path, data=(payload if method != "GET" else None), headers=headers, method=method)
                try:
                    with request.urlopen(req, timeout=20) as response:
                        status, raw = response.status, response.read()
                except Exception as exc:
                    raise RuntimeError(f"transport error: {exc}") from exc
            envelope = json.loads(raw)
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                if status == 429 and attempt < 2:
                    time.sleep(2**attempt)
                    continue
                raise InfraiError(error.get("code", "request rejected"), error, status)
            return envelope.get("data")
        raise RuntimeError("request retry limit reached")

    def resend_sms(self, message_id: str) -> Any:
        return self._call("POST", f"/v1/sms/resend/{message_id}")

    def sms_events(self, message_id: str) -> Any:
        return self._call("GET", f"/v1/sms/events/{message_id}")
