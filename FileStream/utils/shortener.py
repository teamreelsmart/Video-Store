import base64
import hashlib
import hmac
import json
from urllib.parse import quote_plus

from FileStream.config import Server


class ShortenerError(Exception):
    pass


def _signed_payload(payload):
    secret = (Server.SHORTENER_SECRET or "").encode()
    if not secret:
        return None

    body = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    digest = hmac.new(secret, body, hashlib.sha256).digest()
    return base64.urlsafe_b64encode(body + b"." + digest).decode().rstrip("=")


def _verify_signed_payload(raw_payload):
    if not raw_payload:
        return None

    secret = (Server.SHORTENER_SECRET or "").encode()
    if not secret:
        return None

    padding = "=" * (-len(raw_payload) % 4)
    decoded = base64.urlsafe_b64decode((raw_payload + padding).encode())
    body, sent_digest = decoded.rsplit(b".", 1)
    expected = hmac.new(secret, body, hashlib.sha256).digest()
    if not hmac.compare_digest(sent_digest, expected):
        raise ShortenerError("Invalid payload signature")
    return json.loads(body.decode())


def create_short_link(long_url, context):
    provider = (Server.SHORTENER_PROVIDER or "direct").lower()

    if provider in {"direct", "none"}:
        return {"short_url": long_url}

    if provider == "template":
        template = (Server.SHORTENER_TEMPLATE or "").strip()
        if not template:
            raise ShortenerError("SHORTENER_TEMPLATE is required for template provider")

        payload = _signed_payload(
            {
                "uid": context.get("user_id"),
                "code": context.get("code"),
                "step": context.get("step", 1),
            }
        )
        short_url = (
            template.replace("{long_url}", quote_plus(long_url))
            .replace("{uid}", str(context.get("user_id", "")))
            .replace("{code}", str(context.get("code", "")))
            .replace("{payload}", quote_plus(payload or ""))
            .replace("{api_key}", quote_plus(Server.SHORTENER_API_KEY or ""))
            .replace("{domain}", quote_plus(Server.SHORTENER_DOMAIN or ""))
        )
        return {"short_url": short_url, "payload": payload}

    raise ShortenerError(f"Unsupported shortener provider: {provider}")


def resolve_return(payload):
    decoded = _verify_signed_payload(payload)
    if not decoded:
        return None
    return decoded
