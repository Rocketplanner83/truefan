import json
import logging
import os
import socket
import threading
import time
import urllib.error
import urllib.request
from typing import Any, Dict, Optional

LOGGER = logging.getLogger(__name__)

BASE_URL = "http://127.0.0.1:5088"
TOKEN_ENV_VAR = "CONTROL_AGENT_TOKEN"
TIMEOUT_SECONDS = 0.6
HEALTH_CACHE_TTL_SECONDS = 2.0

_CACHE_LOCK = threading.Lock()
_HEALTH_CACHE: Dict[str, Any] = {
    "online": False,
    "last_checked": 0.0,
    "status_code": 0,
    "error": "uninitialized",
}


def _result(ok: bool, status_code: int, data: Optional[Dict[str, Any]], error: str) -> Dict[str, Any]:
    return {
        "ok": ok,
        "status_code": status_code,
        "data": data or {},
        "error": error,
    }


def _build_headers() -> Dict[str, str]:
    token = os.getenv(TOKEN_ENV_VAR, "").strip()
    if not token:
        return {}
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


def _request(
    method: str,
    path: str,
    payload: Optional[Dict[str, Any]] = None,
    timeout: float = TIMEOUT_SECONDS,
) -> Dict[str, Any]:
    url = f"{BASE_URL}{path}"
    headers = _build_headers()
    body = None
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(url=url, data=body, headers=headers, method=method.upper())
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8").strip()
            parsed = json.loads(raw) if raw else {}
            return _result(True, resp.status, parsed, "")
    except urllib.error.HTTPError as exc:
        try:
            raw = exc.read().decode("utf-8").strip()
            parsed = json.loads(raw) if raw else {}
        except Exception as e:
            LOGGER.debug("Failed parsing control agent error payload for %s: %s", url, e)
            parsed = {}
        LOGGER.error("Control agent HTTP error %s for %s", exc.code, url)
        return _result(False, exc.code, parsed, f"HTTP {exc.code}")
    except (urllib.error.URLError, socket.timeout, ConnectionError) as exc:
        LOGGER.error("Control agent connection failed for %s: %s", url, exc)
        return _result(False, 0, {}, "connection_failed")
    except Exception as exc:
        LOGGER.exception("Unexpected control client error for %s", url)
        return _result(False, 0, {}, str(exc))


def get_status() -> Dict[str, Any]:
    return _request("GET", "/status")


def set_pwm(pwm: int) -> Dict[str, Any]:
    return _request("POST", "/set_pwm", {"pwm": pwm})


def _set_health_cache(online: bool, status_code: int, error: str) -> None:
    with _CACHE_LOCK:
        _HEALTH_CACHE["online"] = online
        _HEALTH_CACHE["last_checked"] = time.time()
        _HEALTH_CACHE["status_code"] = status_code
        _HEALTH_CACHE["error"] = error


def _get_health_cache() -> Dict[str, Any]:
    with _CACHE_LOCK:
        return dict(_HEALTH_CACHE)


def refresh_agent_health(timeout: float = TIMEOUT_SECONDS) -> Dict[str, Any]:
    resp = _request("GET", "/status", timeout=timeout)
    if resp.get("ok"):
        _set_health_cache(True, int(resp.get("status_code") or 200), "")
    else:
        _set_health_cache(False, int(resp.get("status_code") or 0), resp.get("error") or "unreachable")
    return get_agent_health(force=False, max_age_seconds=HEALTH_CACHE_TTL_SECONDS)


def get_agent_health(force: bool = False, max_age_seconds: float = HEALTH_CACHE_TTL_SECONDS) -> Dict[str, Any]:
    snapshot = _get_health_cache()
    age = time.time() - float(snapshot.get("last_checked") or 0.0)
    if force or age > max_age_seconds:
        try:
            refresh_agent_health()
            snapshot = _get_health_cache()
        except Exception:
            LOGGER.exception("Failed to refresh agent health")
            snapshot = _get_health_cache()

    snapshot["age_seconds"] = max(0.0, time.time() - float(snapshot.get("last_checked") or 0.0))
    return snapshot
