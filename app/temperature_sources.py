import logging
from typing import Iterable, Optional

from hwmon import find_best_sensor, get_temp
from sensors import read_smartctl_temperature

LOGGER = logging.getLogger(__name__)


def _read_temp_smartctl(device: str) -> Optional[float]:
    temp = read_smartctl_temperature(device)
    if isinstance(temp, dict) and temp.get("_smart_denied"):
        return None
    if temp is None:
        LOGGER.error("smartctl JSON temp unavailable for %s", device)
    return temp


def _read_temp_hwmon(
    source_name: str,
    hwmon_keywords: Iterable[str],
    sensor_keyword: Optional[str] = None,
) -> Optional[float]:
    try:
        hwmon_path = find_best_sensor(hwmon_keywords)
        return float(get_temp(hwmon_path, sensor_keyword))
    except Exception as exc:
        LOGGER.error("hwmon read failed for %s: %s", source_name, exc)
        return None


def get_temperature_sources(include_hdd: bool = False):
    sources = []

    cpu_temp = _read_temp_hwmon("cpu", ["coretemp", "k10temp", "cpu"], "package")
    if cpu_temp is None:
        cpu_temp = _read_temp_hwmon("cpu", ["coretemp", "k10temp", "cpu"])
    if cpu_temp is not None:
        sources.append({"name": "cpu", "value": cpu_temp})
    else:
        LOGGER.error("Skipping cpu source: no valid temperature")

    nvme_temp = _read_temp_hwmon("nvme", ["nvme"])
    if nvme_temp is None:
        nvme_temp = _read_temp_smartctl("/dev/nvme0")
    if nvme_temp is not None:
        sources.append({"name": "nvme", "value": nvme_temp})
    else:
        LOGGER.error("Skipping nvme source: no valid temperature")

    if include_hdd:
        hdd_temp = _read_temp_hwmon("hdd", ["drivetemp", "hdd", "ata"])
        if hdd_temp is None:
            hdd_temp = _read_temp_smartctl("/dev/sda")
        if hdd_temp is not None:
            sources.append({"name": "hdd", "value": hdd_temp})
        else:
            LOGGER.error("Skipping hdd source: no valid temperature")

    return sources
