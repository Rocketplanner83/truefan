import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "app"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

import hwmon  # noqa: E402
import server  # noqa: E402
import temperature_sources  # noqa: E402


def test_hwmon_discovery_returns_dict(tmp_path):
    hw_root = tmp_path / "hwmon"
    hw0 = hw_root / "hwmon0"
    hw0.mkdir(parents=True)
    (hw0 / "name").write_text("coretemp\n", encoding="utf-8")

    mapping = hwmon.get_hwmon_map(root=str(hw_root))

    assert isinstance(mapping, dict)
    assert mapping["coretemp"] == str(hw0)


def test_temperature_sources_returns_list(monkeypatch):
    monkeypatch.setattr(
        temperature_sources,
        "_read_temp_hwmon",
        lambda source_name, hwmon_keywords, sensor_keyword=None: {
            "cpu": 45.0,
            "nvme": 38.0,
            "hdd": 40.0,
        }.get(source_name),
    )
    monkeypatch.setattr(temperature_sources, "_read_temp_smartctl", lambda *args, **kwargs: None)

    sources = temperature_sources.get_temperature_sources(include_hdd=True)

    assert isinstance(sources, list)
    assert all(isinstance(item, dict) for item in sources)
    assert all("name" in item and "value" in item for item in sources)
    assert {item["name"] for item in sources} >= {"cpu", "nvme", "hdd"}


def test_status_endpoint_returns_valid_json(monkeypatch):
    monkeypatch.setattr(server, "get_profile", lambda: "cool")
    monkeypatch.setattr(server, "get_uptime", lambda: "1h 02m")
    monkeypatch.setattr(server, "get_cpu_load", lambda: "0.10 / 0.20 / 0.30")
    monkeypatch.setattr(
        server,
        "get_sensors_data",
        lambda: [{"name": "cpu", "value": 42.0}, {"name": "nvme", "value": 37.0}],
    )

    client = server.app.test_client()
    res = client.get("/status")

    assert res.status_code == 200
    payload = res.get_json()
    assert isinstance(payload, dict)
    assert isinstance(payload.get("profile"), str)
    assert isinstance(payload.get("uptime"), str)
    assert isinstance(payload.get("load"), str)
    assert isinstance(payload.get("sensors"), list)
    assert payload["sensors"]
    assert all("name" in item and "value" in item for item in payload["sensors"])
