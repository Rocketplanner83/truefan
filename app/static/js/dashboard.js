(() => {
  const POLL_MS = 2000;

  const FALLBACK = {
    profile: "unknown",
    uptime: "0h 0m",
    load: "0.00 / 0.00 / 0.00",
    pwm: "--",
    pwm_control_enabled: false,
    capabilities: { smart_available: true },
    sensors: [
      { name: "cpu", value: 0 },
      { name: "nvme", value: 0 },
      { name: "hdd", value: 0 },
    ],
  };

  const els = {
    sensorList: document.querySelector("#sensor-list"),
    fanGraph: document.querySelector("#fan-graph"),
    profile: document.querySelector("#profile"),
    uptime: document.querySelector("#uptime"),
    load: document.querySelector("#load"),
    pwmValue: document.querySelector("#pwm-value"),
    pwmSlider: document.querySelector("#pwm-slider"),
    applyPwmBtn: document.querySelector("#apply-pwm"),
    smartWarning: document.querySelector("#smart-warning"),
    debugToggle: document.querySelector("#show-debug-json"),
    debugJson: document.querySelector("#debug-json"),
  };

  let firstLoad = true;
  let lastStatusPayload = null;

  function setText(el, value) {
    if (!el) return;
    el.textContent = String(value);
  }

  function normalizeStatus(payload) {
    const data = payload && typeof payload === "object" ? payload : {};
    const sensors = Array.isArray(data.sensors) && data.sensors.length
      ? data.sensors
      : FALLBACK.sensors;

    return {
      profile: data.profile || FALLBACK.profile,
      uptime: data.uptime || FALLBACK.uptime,
      load: data.load || FALLBACK.load,
      pwm: data.pwm ?? FALLBACK.pwm,
      pwm_control_enabled: data.pwm_control_enabled ?? FALLBACK.pwm_control_enabled,
      capabilities: {
        smart_available: data?.capabilities?.smart_available ?? FALLBACK.capabilities.smart_available,
      },
      sensors,
    };
  }

  function renderSensors(sensors) {
    if (!els.sensorList) return;
    els.sensorList.innerHTML = "";

    sensors.forEach((item) => {
      const li = document.createElement("li");
      const name = item?.name ?? "unknown";
      const value = item?.value ?? "--";
      li.textContent = `${name}: ${value}`;
      els.sensorList.appendChild(li);
    });
  }

  function render(data) {
    setText(els.profile, data.profile);
    setText(els.uptime, data.uptime);
    setText(els.load, data.load);
    setText(els.pwmValue, data.pwm);
    if (els.pwmSlider) {
      els.pwmSlider.disabled = !data.pwm_control_enabled;
      els.pwmSlider.title = data.pwm_control_enabled ? "" : "Monitoring-only mode: control agent unavailable";
    }
    if (els.applyPwmBtn) {
      els.applyPwmBtn.disabled = !data.pwm_control_enabled;
    }
    if (els.smartWarning) {
      els.smartWarning.style.display = data.capabilities.smart_available ? "none" : "block";
    }
    renderSensors(data.sensors);

    if (els.fanGraph) {
      const numeric = data.sensors
        .map((s) => Number(s?.value))
        .filter((v) => Number.isFinite(v));
      const max = numeric.length ? Math.max(...numeric) : 0;
      els.fanGraph.textContent = `Fan graph placeholder | max sensor: ${max}`;
    }
  }

  function updateDebugView() {
    if (!els.debugToggle || !els.debugJson) return;

    if (els.debugToggle.checked) {
      els.debugJson.style.display = "block";
      els.debugJson.textContent = JSON.stringify(lastStatusPayload ?? {}, null, 2);
    } else {
      els.debugJson.style.display = "none";
      els.debugJson.textContent = "";
    }
  }

  function showLoading() {
    setText(els.profile, "Loading...");
    setText(els.uptime, "Loading...");
    setText(els.load, "Loading...");
    setText(els.pwmValue, "Loading...");

    if (els.sensorList) {
      els.sensorList.innerHTML = "<li>Loading sensors...</li>";
    }

    if (els.fanGraph) {
      els.fanGraph.textContent = "Loading fan data...";
    }
  }

  function showError(err) {
    console.error("Dashboard update failed:", err);
    const fallback = normalizeStatus(null);
    render(fallback);
    lastStatusPayload = { error: String(err), fallback };
    updateDebugView();

    if (els.sensorList) {
      const li = document.createElement("li");
      li.textContent = "Error: failed to fetch /status";
      li.style.color = "#ff6b6b";
      els.sensorList.appendChild(li);
    }
  }

  async function tick() {
    try {
      const res = await fetch("/status", { cache: "no-store" });
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }
      const payload = await res.json();
      lastStatusPayload = payload;
      const data = normalizeStatus(payload);
      render(data);
      updateDebugView();
      firstLoad = false;
    } catch (err) {
      showError(err);
      firstLoad = false;
    }
  }

  document.addEventListener("DOMContentLoaded", () => {
    if (els.debugToggle) {
      els.debugToggle.addEventListener("change", updateDebugView);
    }
    if (firstLoad) showLoading();
    tick();
    window.setInterval(tick, POLL_MS);
  });
})();
