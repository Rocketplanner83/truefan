import copy
import logging
import os

from flask import Flask, jsonify, render_template, request
from werkzeug.exceptions import HTTPException

from control import ReadOnlyModeError
from control import load_profile as control_load_profile
from control import set_profile as control_set_profile
from sensors import read_fan_rpms
from control_client import get_agent_health
from control_client import set_pwm as agent_set_pwm
from sensors import get_smart_capabilities
from temperature_sources import get_temperature_sources

app = Flask(__name__, static_folder="static", template_folder="templates")
LOGGER = logging.getLogger(__name__)

DEFAULT_SENSORS = [
    {"name": "cpu", "value": 0.0},
    {"name": "nvme", "value": 0.0},
    {"name": "hdd", "value": 0.0},
]

DEFAULT_STATUS = {
    "mode": "monitoring-only",
    "agent_available": False,
    "pwm_control_enabled": False,
    "agent": {"online": False, "status_code": 0, "error": "uninitialized", "age_seconds": 0.0},
    "sensors": copy.deepcopy(DEFAULT_SENSORS),
    "capabilities": {"smart_available": True},
    "fan": {"current_pwm": 0, "available_pwms": []},
    "system": {"profile": "unknown", "uptime": "0h 0m", "load": "0.00 / 0.00 / 0.00"},
}


def _default_sensors():
    return copy.deepcopy(DEFAULT_SENSORS)


def _default_status():
    return {
        "mode": "monitoring-only",
        "agent_available": False,
        "pwm_control_enabled": False,
        "agent": {"online": False, "status_code": 0, "error": "uninitialized", "age_seconds": 0.0},
        "sensors": _default_sensors(),
        "capabilities": {"smart_available": True},
        "fan": {"current_pwm": 0, "available_pwms": []},
        "system": {"profile": "unknown", "uptime": "0h 0m", "load": "0.00 / 0.00 / 0.00"},
    }


def _get_agent_control_state():
    try:
        health = get_agent_health(force=False)
        if health.get("online"):
            return {
                "mode": "full-control",
                "pwm_control_enabled": True,
                "agent_available": True,
                "agent": health,
            }
    except Exception:
        LOGGER.exception("Agent status check failed")

    return {
        "mode": "monitoring-only",
        "pwm_control_enabled": False,
        "agent_available": False,
        "agent": get_agent_health(force=False),
    }


def _build_status_payload() -> dict:
    payload = _default_status()
    control_state = _get_agent_control_state()

    payload["mode"] = control_state["mode"]
    payload["agent_available"] = control_state["agent_available"]
    payload["pwm_control_enabled"] = control_state["pwm_control_enabled"]
    payload["agent"] = control_state["agent"]
    payload["sensors"] = get_sensors_data() or _default_sensors()
    payload["fan"] = read_fan_rpms()
    payload["capabilities"] = get_smart_capabilities()
    payload["system"] = {
        "profile": get_profile() or DEFAULT_STATUS["system"]["profile"],
        "uptime": get_uptime() or DEFAULT_STATUS["system"]["uptime"],
        "load": get_cpu_load() or DEFAULT_STATUS["system"]["load"],
    }
    return payload


def _require_write_access():
    secret = os.getenv("TRUEFAN_AGENT_SECRET", "").strip() or os.getenv("CONTROL_AGENT_TOKEN", "").strip()
    header = request.headers.get("Authorization", "")
    if not secret:
        return False, "Write secret is not configured"
    if not header.startswith("Bearer "):
        return False, "Missing Bearer token"
    token = header[len("Bearer ") :].strip()
    if token != secret:
        return False, "Invalid token"

    health = get_agent_health(force=False)
    if not health.get("online"):
        return False, "Control agent unavailable; monitoring-only mode"
    return True, ""


def _api_result(ok: bool, error, data, status_code: int = 200):
    return jsonify({"ok": bool(ok), "error": error, "data": data}), status_code


def get_profile():
    try:
        profile = control_load_profile()
        return profile.lower() if profile else DEFAULT_STATUS["system"]["profile"]
    except Exception:
        LOGGER.exception("Failed to read profile")
        return DEFAULT_STATUS["system"]["profile"]


def get_sensors_data():
    try:
        sensors = get_temperature_sources(include_hdd=True)
        if not sensors:
            LOGGER.warning("No temperature sources detected; using defaults")
            return _default_sensors()
        return sensors
    except Exception:
        LOGGER.exception("Failed to read sensors; using defaults")
        return _default_sensors()


def get_uptime():
    try:
        with open("/proc/uptime", "r", encoding="utf-8") as f:
            uptime_seconds = float(f.readline().split()[0])
        hours = int(uptime_seconds // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        return f"{hours}h {minutes}m"
    except Exception:
        LOGGER.exception("Failed to read uptime")
        return DEFAULT_STATUS["system"]["uptime"]


def get_cpu_load():
    try:
        load1, load5, load15 = os.getloadavg()
        return f"{load1:.2f} / {load5:.2f} / {load15:.2f}"
    except Exception:
        LOGGER.exception("Failed to read CPU load")
        return DEFAULT_STATUS["system"]["load"]


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api")
def api_index():
    return jsonify(
        {
            "status": "ok",
            "message": "TrueFan API",
            "endpoints": ["/sensors", "/status", "/pwm/<value>", "/set/<profile>"],
        }
    )


@app.route("/sensors")
def sensors():
    try:
        return jsonify(get_sensors_data())
    except Exception:
        LOGGER.exception("Unexpected /sensors failure; returning defaults")
        return jsonify(_default_sensors())


@app.route("/pwm/<value>", methods=["POST"])
def set_pwm(value):
    try:
        allowed, reason = _require_write_access()
        if not allowed:
            return _api_result(False, reason, None, 403)

        resp = agent_set_pwm(int(value))
        if resp.get("ok"):
            return _api_result(True, None, {"pwm": (resp.get("data") or {}).get("pwm", int(value))}, 200)

        status_code = int(resp.get("status_code") or 503)
        if status_code == 0:
            status_code = 503
        return _api_result(False, "Control agent unavailable; monitoring-only mode", None, status_code)
    except ReadOnlyModeError as exc:
        LOGGER.exception("Write blocked in read-only mode")
        return _api_result(False, str(exc), None, 403)
    except Exception:
        LOGGER.exception("Failed to set PWM")
        return _api_result(False, "Failed to set PWM", None, 400)


@app.route("/set/<profile>", methods=["POST"])
def set_profile(profile):
    try:
        allowed, reason = _require_write_access()
        if not allowed:
            return _api_result(False, reason, None, 403)
        control_set_profile(profile)
        return _api_result(True, None, {"profile": profile}, 200)
    except ReadOnlyModeError as exc:
        LOGGER.exception("Write blocked in read-only mode")
        return _api_result(False, str(exc), None, 403)
    except Exception:
        LOGGER.exception("Failed to set profile")
        return _api_result(False, "Failed to set profile", None, 400)


@app.route("/restart-container", methods=["POST"])
def restart_container():
    allowed, reason = _require_write_access()
    if not allowed:
        return _api_result(False, reason, None, 403)
    return _api_result(False, "Disabled in core; use control agent host operations", None, 403)


@app.route("/shutdown-container", methods=["POST"])
def shutdown_container():
    allowed, reason = _require_write_access()
    if not allowed:
        return _api_result(False, reason, None, 403)
    return _api_result(False, "Disabled in core; use control agent host operations", None, 403)


@app.route("/status")
def status():
    try:
        return jsonify(_build_status_payload())
    except Exception:
        LOGGER.exception("Unexpected /status failure; returning defaults")
        return jsonify(_default_status())


@app.errorhandler(404)
def not_found(_err):
    return jsonify({"status": "error", "message": "Not Found"}), 404


@app.errorhandler(405)
def method_not_allowed(_err):
    return jsonify({"status": "error", "message": "Method Not Allowed"}), 405


@app.errorhandler(Exception)
def handle_unexpected_error(err):
    if isinstance(err, HTTPException):
        return jsonify({"status": "error", "message": err.description}), err.code
    LOGGER.exception("Unhandled server error")
    return jsonify({"status": "error", "message": "Internal Server Error"}), 500


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5002)
