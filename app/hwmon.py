import glob
import logging
import os
from typing import Dict, Iterable, List, Optional, Union

LOGGER = logging.getLogger(__name__)
HWMON_ROOT = "/sys/class/hwmon"


def get_hwmon_map(root: str = HWMON_ROOT) -> Dict[str, str]:
    """
    Scan hwmon devices and build a name -> path map.

    Args:
        root: Base hwmon directory, defaults to /sys/class/hwmon.

    Returns:
        Dict[str, str]: Mapping of hwmon name to absolute hwmon path.

    Raises:
        FileNotFoundError: If the hwmon root does not exist.
    """
    if not os.path.isdir(root):
        raise FileNotFoundError(f"hwmon root does not exist: {root}")

    hwmon_map: Dict[str, str] = {}
    for hwmon_dir in sorted(glob.glob(os.path.join(root, "hwmon*"))):
        name_file = os.path.join(hwmon_dir, "name")
        if not os.path.isfile(name_file):
            LOGGER.warning("Skipping %s: missing name file", hwmon_dir)
            continue

        with open(name_file, "r", encoding="utf-8") as f:
            name = f.read().strip().lower()

        if not name:
            LOGGER.warning("Skipping %s: empty name", hwmon_dir)
            continue

        if name in hwmon_map:
            LOGGER.warning(
                "Duplicate hwmon name '%s': keeping %s, ignoring %s",
                name,
                hwmon_map[name],
                hwmon_dir,
            )
            continue

        hwmon_map[name] = hwmon_dir
        LOGGER.debug("Discovered hwmon %s -> %s", name, hwmon_dir)

    LOGGER.info("Discovered %d hwmon devices", len(hwmon_map))
    return hwmon_map


def find_best_sensor(
    name_keywords: Union[str, Iterable[str]],
    root: str = HWMON_ROOT,
) -> str:
    """
    Return the best matching hwmon path for one or more keywords.

    Args:
        name_keywords: Single keyword or iterable of keywords.
        root: Base hwmon directory.

    Returns:
        str: Matched hwmon path.

    Raises:
        LookupError: If no matching hwmon device is found.
    """
    if isinstance(name_keywords, str):
        keywords: List[str] = [name_keywords]
    else:
        keywords = list(name_keywords)

    keywords = [k.lower() for k in keywords if k]
    if not keywords:
        raise ValueError("name_keywords must include at least one keyword")

    hwmon_map = get_hwmon_map(root=root)
    for keyword in keywords:
        for sensor_name, sensor_path in hwmon_map.items():
            if keyword in sensor_name:
                LOGGER.info("Matched keyword '%s' to %s", keyword, sensor_path)
                return sensor_path

    raise LookupError(f"No hwmon device matched keywords: {keywords}")


def get_temp(hwmon_path: str, sensor_keyword: Optional[str] = None) -> float:
    """
    Read a temperature (in Celsius) from a hwmon device path.

    The function prefers matching temp*_label against sensor_keyword.
    If no label match is found and sensor_keyword is None/empty, temp1_input
    (or the first available temp*_input) is used.

    Args:
        hwmon_path: Path such as /sys/class/hwmon/hwmon2.
        sensor_keyword: Optional keyword to match against temp labels.

    Returns:
        float: Temperature in Celsius.

    Raises:
        FileNotFoundError: If hwmon_path or temp input files are missing.
        LookupError: If no labeled temperature matches sensor_keyword.
        ValueError: If temperature file content is invalid.
    """
    if not os.path.isdir(hwmon_path):
        raise FileNotFoundError(f"hwmon path does not exist: {hwmon_path}")

    input_files = sorted(glob.glob(os.path.join(hwmon_path, "temp*_input")))
    if not input_files:
        raise FileNotFoundError(f"No temp*_input files found in {hwmon_path}")

    keyword = (sensor_keyword or "").strip().lower()
    target_input: Optional[str] = None

    if keyword:
        for input_file in input_files:
            base = input_file[:-len("_input")]
            label_file = f"{base}_label"
            if not os.path.isfile(label_file):
                continue

            with open(label_file, "r", encoding="utf-8") as f:
                label = f.read().strip().lower()

            if keyword in label:
                target_input = input_file
                LOGGER.info(
                    "Using labeled sensor '%s' from %s",
                    label,
                    target_input,
                )
                break

        if target_input is None:
            raise LookupError(
                f"No temp label matching '{sensor_keyword}' found in {hwmon_path}"
            )
    else:
        preferred = os.path.join(hwmon_path, "temp1_input")
        target_input = preferred if preferred in input_files else input_files[0]
        LOGGER.debug("Using default temperature input: %s", target_input)

    with open(target_input, "r", encoding="utf-8") as f:
        raw = f.read().strip()

    value = float(raw)
    # hwmon temps are normally in millidegrees C.
    temp_c = value / 1000.0 if value > 500.0 else value
    LOGGER.debug("Read temperature %.2fC from %s", temp_c, target_input)
    return temp_c


def _doctest_usage():
    """
    >>> import tempfile
    >>> from pathlib import Path
    >>> td = tempfile.TemporaryDirectory()
    >>> root = Path(td.name) / "hwmon"
    >>> h0 = root / "hwmon0"
    >>> h0.mkdir(parents=True)
    >>> _ = (h0 / "name").write_text("coretemp\\n", encoding="utf-8")
    >>> _ = (h0 / "temp1_label").write_text("Package id 0\\n", encoding="utf-8")
    >>> _ = (h0 / "temp1_input").write_text("42000\\n", encoding="utf-8")
    >>> get_hwmon_map(str(root))["coretemp"].endswith("hwmon0")
    True
    >>> p = find_best_sensor(["core", "asus"], root=str(root))
    >>> round(get_temp(p, "package"), 1)
    42.0
    >>> td.cleanup()
    """


if __name__ == "__main__":
    import doctest

    doctest.testmod()
