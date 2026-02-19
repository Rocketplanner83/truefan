import os
import logging
from typing import Dict

LOGGER = logging.getLogger(__name__)

HWMON_ROOT = "/sys/class/hwmon"


def get_hwmon_map(root: str = HWMON_ROOT) -> Dict[str, str]:
    hwmon_map: Dict[str, str] = {}
    if not os.path.isdir(root):
        return hwmon_map

    for entry in sorted(os.listdir(root)):
        path = os.path.join(root, entry)
        if not os.path.isdir(path):
            continue

        name_file = os.path.join(path, "name")
        try:
            with open(name_file, "r", encoding="utf-8") as f:
                name = f.read().strip().lower()
        except OSError as e:
            LOGGER.debug("Skipping hwmon entry %s due to name read error: %s", path, e)
            continue

        if not name:
            continue

        key = name
        suffix = 2
        while key in hwmon_map:
            key = f"{name}_{suffix}"
            suffix += 1
        hwmon_map[key] = path

    return hwmon_map
