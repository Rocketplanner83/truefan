import logging
import os
import sys
import time
import subprocess
import json
from typing import Dict, Tuple, List

from control_client import get_agent_health, set_pwm as agent_set_pwm
from temperature_sources import get_temperature_sources

PROFILE_FILE = "fan_profile.conf"
LOGGER = logging.getLogger(__name__)


def load_profile() -> str:
    if not os.path.exists(PROFILE_FILE):
        return "cool"
    try:
        with open(PROFILE_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("profile="):
                    return line.strip().split("=", 1)[1]
    except OSError as e:
        LOGGER.debug("Failed reading profile file %s: %s", PROFILE_FILE, e)
    return "cool"


def set_profile(name: str) -> None:
    with open(PROFILE_FILE, "w", encoding="utf-8") as f:
        f.write(f"profile={name}\n")
    LOGGER.info("Profile set to: %s", name)


# -------------------------
# Temperature Handling
# -------------------------

def _temps_from_sources() -> Dict[str, float]:
    sources = get_temperature_sources(include_hdd=True)
    out = {"cpu": 0.0, "nvme": 0.0, "hdd": 0.0}

    for item in sources:
        name = str(item.get("name", "")).lower()
        value = item.get("value")
        try:
            if name in out and value is not None:
                out[name] = float(value)
        except (TypeError, ValueError) as e:
            LOGGER.debug("Invalid temperature value for %s: %s", name, e)

    return out


def read_all_temps() -> Tuple[float, float, float]:
    temps = _temps_from_sources()
    return temps["cpu"], temps["nvme"], temps["hdd"]


def determine_pwm(cpu_temp: float, profile: str) -> int:
    if profile == "quiet":
        if cpu_temp >= 80:
            return 180
        if cpu_temp >= 65:
            return 120
        return 70

    if profile == "cool":
        if cpu_temp >= 70:
            return 255
        if cpu_temp >= 55:
            return 180
        return 100

    if profile == "aggressive":
        if cpu_temp >= 50:
            return 255
        if cpu_temp >= 40:
            return 180
        return 130

    return 120


def get_status() -> Dict[str, float]:
    cpu, nvme, hdd = read_all_temps()
    profile = load_profile()
    return {
        "profile": profile,
        "cpu": cpu,
        "nvme": nvme,
        "hdd": hdd,
        "pwm": determine_pwm(cpu, profile),
    }


# -------------------------
# Control Loop
# -------------------------

def control_loop(interval_seconds: int = 5, iterations: int = 1):
    if iterations < 1:
        raise ValueError("iterations must be >= 1")

    latest = None
    for i in range(iterations):
        latest = get_status()
        LOGGER.info("Control loop status (no direct hardware write): %s", latest)
        if i < iterations - 1:
            time.sleep(interval_seconds)

    return latest


def set_pwm(pwm_value):
    health = get_agent_health(force=False)
    if not health.get("online"):
        raise RuntimeError("Control agent unavailable; monitoring-only mode")

    resp = agent_set_pwm(int(pwm_value))
    if not resp.get("ok"):
        raise RuntimeError(resp.get("error") or "Failed to set PWM via control agent")

    return (resp.get("data") or {}).get("pwm", int(pwm_value))


# -------------------------
# Drive Temperature Scanning
# -------------------------

def list_all_drives() -> List[str]:
    try:
        scan_out = subprocess.check_output(
            ["smartctl", "--scan"],
            encoding="utf-8"
        )
        return [line.split()[0] for line in scan_out.splitlines() if line.strip()]
    except Exception as e:
        LOGGER.debug("Drive scan failed: %s", e)
        return []


def get_drive_temperature(device: str) -> str:
    try:
        out = subprocess.check_output(
            ["smartctl", "-j", "-a", device],
            encoding="utf-8"
        )
        data = json.loads(out)

        # NVMe path
        if "nvme_smart_health_information_log" in data:
            temp = data["nvme_smart_health_information_log"].get("temperature")
            if temp is not None:
                return f"{temp} C"

        # ATA path
        if "temperature" in data:
            temp = data["temperature"].get("current")
            if temp is not None:
                return f"{temp} C"

    except Exception as e:
        LOGGER.debug("Failed reading temperature for %s: %s", device, e)

    return "N/A"


def drive_temperatures():
    drives = list_all_drives()
    if not drives:
        LOGGER.info("No drives found or unable to scan.")
        return

    for device in drives:
        temp = get_drive_temperature(device)
        LOGGER.info("%s: %s", device, temp)


# -------------------------
# CLI
# -------------------------

def print_usage() -> None:
    LOGGER.error(
        "Usage: fan.py "
        "[status|control|set <pwm>|set-profile <name>|get-profile|drive-temps]"
    )


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else None
    if not cmd:
        print_usage()
        sys.exit(1)

    if cmd == "status":
        LOGGER.info("Status: %s", get_status())
        return

    if cmd == "control":
        control_loop(iterations=1)
        return

    if cmd == "set":
        if len(sys.argv) != 3:
            print_usage()
            sys.exit(1)
        try:
            set_pwm(sys.argv[2])
        except Exception as exc:
            LOGGER.error("Failed to set PWM: %s", exc)
            sys.exit(1)
        return

    if cmd == "set-profile" and len(sys.argv) == 3:
        set_profile(sys.argv[2])
        return

    if cmd == "get-profile":
        sys.stdout.write(f"{load_profile()}\n")
        return

    if cmd == "drive-temps":
        drive_temperatures()
        return

    print_usage()
    sys.exit(1)


if __name__ == "__main__":
    main()