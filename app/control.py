import os

from control_client import get_agent_health, set_pwm as agent_set_pwm
from fan import control_loop, get_status, load_profile, set_profile as fan_set_profile


class ReadOnlyModeError(RuntimeError):
    pass


def get_truefan_mode():
    return os.getenv("TRUEFAN_MODE", "").strip().lower()


def is_read_only_mode():
    return get_truefan_mode() == "read-only"


def set_pwm(pwm_value):
    if is_read_only_mode():
        raise ReadOnlyModeError("TRUEFAN_MODE is read-only; PWM writes are disabled")
    health = get_agent_health(force=False)
    if not health.get("online"):
        raise ReadOnlyModeError("Control agent unavailable; monitoring-only mode")
    resp = agent_set_pwm(int(pwm_value))
    if not resp.get("ok"):
        raise ReadOnlyModeError(resp.get("error") or "Failed to set PWM")
    return (resp.get("data") or {}).get("pwm", int(pwm_value))


def set_profile(profile):
    if is_read_only_mode():
        raise ReadOnlyModeError("TRUEFAN_MODE is read-only; profile writes are disabled")
    return fan_set_profile(profile)


__all__ = [
    "ReadOnlyModeError",
    "control_loop",
    "get_status",
    "get_truefan_mode",
    "is_read_only_mode",
    "load_profile",
    "set_profile",
    "set_pwm",
]
