import glob
import json
import logging
import os
import subprocess
from typing import Any, Dict, Iterable, Optional, Union

LOGGER = logging.getLogger(__name__)
_SMART_DENIED = False
_SMART_DENIED_WARNED = False
HWMON_ROOT = "/sys/class/hwmon"

TEMP_ATTRIBUTE_NAMES = {
    "temperature_celsius",
    "temperature_case",
    "temperature_internal",
    "airflow_temperature_cel",
}


def _to_float(value: Any) -> Optional[float]:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _extract_from_attributes(data: Dict[str, Any]) -> Optional[float]:
    attrs = data.get("ata_smart_attributes", {}).get("table", [])
    if not isinstance(attrs, Iterable):
        return None

    for attr in attrs:
        if not isinstance(attr, dict):
            continue
        name = str(attr.get("name", "")).strip().lower()
        if name not in TEMP_ATTRIBUTE_NAMES and "temp" not in name:
            continue

        raw = attr.get("raw", {})
        if isinstance(raw, dict):
            temp = _to_float(raw.get("value"))
            if temp is not None:
                return temp

        temp = _to_float(attr.get("value"))
        if temp is not None:
            return temp

    return None


def _mark_smart_denied(device: str, stderr: str = "") -> None:
    global _SMART_DENIED, _SMART_DENIED_WARNED
    _SMART_DENIED = True
    if not _SMART_DENIED_WARNED:
        LOGGER.warning("SMART permission denied for %s: %s", device, stderr.strip() or "Permission denied")
        _SMART_DENIED_WARNED = True


def get_smart_capabilities() -> Dict[str, bool]:
    return {"smart_available": not _SMART_DENIED}


def read_fan_rpms():
    fans = {}
    for hwmon_path in glob.glob(os.path.join(HWMON_ROOT, "hwmon*")):
        try:
            name_file = os.path.join(hwmon_path, "name")
            with open(name_file, "r", encoding="utf-8") as f:
                name = f.read().strip().lower()

            if "nct" not in name and "asus" not in name:
                continue

            for fan_file in glob.glob(os.path.join(hwmon_path, "fan*_input")):
                label = os.path.basename(fan_file).replace("_input", "")
                try:
                    with open(fan_file, "r", encoding="utf-8") as f:
                        rpm = int(f.read().strip())
                    fans[label] = rpm
                except Exception:
                    continue
        except Exception:
            continue
    return fans


def read_smartctl_temperature(device: str) -> Union[float, Dict[str, bool], None]:
    """
    Read disk temperature using smartctl JSON output.

    Returns:
        float temperature in Celsius, or None if not available/supported.
    """
    try:
        proc = subprocess.run(
            ["smartctl", "--json", "-A", device],
            capture_output=True,
            text=True,
            check=False,
            timeout=3,
        )
    except FileNotFoundError:
        LOGGER.warning("smartctl binary not found; SMART unavailable for %s", device)
        return None
    except Exception:
        LOGGER.exception("smartctl execution failed for %s", device)
        return None

    if "permission denied" in (proc.stderr or "").lower():
        _mark_smart_denied(device, proc.stderr or "")
        return {"_smart_denied": True}

    if not proc.stdout:
        LOGGER.error("smartctl produced no JSON output for %s", device)
        return None

    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError:
        LOGGER.exception("Invalid smartctl JSON for %s", device)
        return None

    temp = _to_float(data.get("temperature", {}).get("current"))
    if temp is not None:
        return temp

    temp = _extract_from_attributes(data)
    if temp is not None:
        return temp

    LOGGER.info("Temperature not supported or unavailable for %s", device)
    return None
