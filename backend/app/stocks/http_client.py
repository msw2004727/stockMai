from __future__ import annotations

import json
import ssl
from urllib.error import URLError
from urllib.request import urlopen


def fetch_json(
    url: str,
    *,
    timeout: int = 8,
    allow_insecure_tls_fallback: bool = False,
) -> dict:
    try:
        with urlopen(url, timeout=timeout) as response:
            return json.load(response)
    except URLError as exc:
        if not allow_insecure_tls_fallback or not _is_tls_cert_verify_error(exc):
            raise

        # TWSE occasionally serves a cert chain that fails strict OpenSSL checks
        # (for example "Missing Subject Key Identifier"). Retry without cert
        # verification as a constrained compatibility fallback for public data.
        context = ssl._create_unverified_context()
        with urlopen(url, timeout=timeout, context=context) as response:
            return json.load(response)


def _is_tls_cert_verify_error(exc: URLError) -> bool:
    reason = str(getattr(exc, "reason", "") or "")
    text = f"{exc} {reason}".lower()
    return "certificate_verify_failed" in text or "missing subject key identifier" in text
