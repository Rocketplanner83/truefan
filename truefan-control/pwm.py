import glob
import logging
import os
import re
from typing import List, Optional

from hwmon import HWMON_ROOT

LOGGER = logging.getLogger(__name__)
PWM_BASENAME_RE = re.compile(r"^pwm[0-9]+$")


def _normalize(path: str) -> str:
    return os.path.realpath(os.path.abspath(path))


def _is_safe_pwm_path(path: str, root: str = HWMON_ROOT) -> bool:
    norm_root = _normalize(root)
    norm_path = _normalize(path)
    base = os.path.basename(norm_path)
    return (
        norm_path.startswith(norm_root + os.sep)
        and PWM_BASENAME_RE.match(base) is not None
        and os.path.isfile(norm_path)
    )


def discover_pwm_files(root: str = HWMON_ROOT) -> List[str]:
    try:
        pattern = f"{root}/hwmon*/pwm[0-9]*"
        files = sorted(glob.glob(pattern))
        safe_files = []
        for f in files:
            if "_enable" in f:
                continue
            if _is_safe_pwm_path(f, root=root):
                safe_files.append(_normalize(f))
        return safe_files
    except Exception:
        LOGGER.exception("Failed to discover PWM files")
        return []


def read_current_pwm(pwm_files: List[str]) -> int:
    for pwm_file in pwm_files:
        try:
            with open(pwm_file, "r", encoding="utf-8") as f:
                return int(f.read().strip())
        except Exception:
            LOGGER.exception("Failed reading PWM value from %s", pwm_file)
            continue
    return 0


def write_pwm_value(pwm: int, pwm_files: List[str]) -> Optional[str]:
    discovered_now = discover_pwm_files()
    if not discovered_now:
        return None

    discovered_set = set(discovered_now)
    target = None

    # Write only to paths that are both caller-listed and currently discovered.
    for candidate in pwm_files:
        norm = _normalize(candidate)
        if norm in discovered_set and _is_safe_pwm_path(norm):
            target = norm
            break

    # Fallback to first safe discovered path if caller list is stale/empty.
    if target is None:
        target = next((p for p in discovered_now if _is_safe_pwm_path(p)), None)
    if target is None:
        return None

    if not os.path.exists(target):
        LOGGER.error("PWM target does not exist: %s", target)
        return None

    enable_file = f"{target}_enable"
    try:
        try:
            if os.path.isfile(enable_file):
                with open(enable_file, "w", encoding="utf-8") as f:
                    # 1 means manual control on most hwmon drivers.
                    f.write("1")
        except OSError as e:
            LOGGER.debug("Failed to set manual mode for %s: %s", enable_file, e)

        with open(target, "w", encoding="utf-8") as f:
            f.write(str(pwm))
        return target
    except Exception:
        LOGGER.exception("Failed writing PWM value to %s", target)
        return None
