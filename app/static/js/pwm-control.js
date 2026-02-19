(() => {
  const SELECTORS = {
    slider: ["#pwm-slider", "#pwmSlider", "#pwm"],
    value: ["#pwm-value", "#pwmValue"],
    applyBtn: ["#apply-pwm", "#applyPWM", "[data-action='apply-pwm']"],
  };

  function pick(selectors) {
    for (const s of selectors) {
      const el = document.querySelector(s);
      if (el) return el;
    }
    return null;
  }

  function buildToast() {
    const toast = document.createElement("div");
    toast.setAttribute("aria-live", "polite");
    toast.style.position = "fixed";
    toast.style.right = "18px";
    toast.style.bottom = "18px";
    toast.style.padding = "10px 14px";
    toast.style.borderRadius = "8px";
    toast.style.background = "#1c1c1c";
    toast.style.color = "#d8ffe1";
    toast.style.border = "1px solid #2f5248";
    toast.style.boxShadow = "0 10px 30px rgba(0,0,0,0.35)";
    toast.style.fontFamily = '"Fira Mono","Source Code Pro",monospace';
    toast.style.opacity = "0";
    toast.style.transform = "translateY(8px)";
    toast.style.transition = "opacity 180ms ease, transform 180ms ease";
    toast.style.pointerEvents = "none";
    toast.style.zIndex = "9999";
    document.body.appendChild(toast);
    return toast;
  }

  const toast = buildToast();
  let toastTimer = null;

  function showToast(message, type = "ok") {
    toast.textContent = message;
    toast.style.borderColor = type === "error" ? "#7a2f2f" : "#2f5248";
    toast.style.color = type === "error" ? "#ffc8c8" : "#d8ffe1";
    toast.style.background = type === "error" ? "#2a1414" : "#1c1c1c";

    requestAnimationFrame(() => {
      toast.style.opacity = "1";
      toast.style.transform = "translateY(0)";
    });

    if (toastTimer) clearTimeout(toastTimer);
    toastTimer = setTimeout(() => {
      toast.style.opacity = "0";
      toast.style.transform = "translateY(8px)";
    }, 1800);
  }

  async function postPWM(value) {
    let res = await fetch(`/pwm/${value}`, { method: "POST" });
    if (res.status === 404 || res.status === 405) {
      res = await fetch(`/set/${value}`, { method: "POST" });
    }
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}`);
    }
    return res;
  }

  document.addEventListener("DOMContentLoaded", () => {
    const slider = pick(SELECTORS.slider);
    const valueEl = pick(SELECTORS.value);
    const applyBtn = pick(SELECTORS.applyBtn);

    if (!slider) return;

    const updateValue = () => {
      const val = Number(slider.value);
      if (valueEl) {
        valueEl.textContent = String(val);
      } else {
        // If no dedicated value node exists, keep label in sync.
        const label = document.querySelector(`label[for='${slider.id}']`);
        if (label) label.textContent = `PWM value: ${val}`;
      }
    };

    updateValue();
    slider.addEventListener("input", updateValue);

    if (!applyBtn) return;

    let inFlight = false;
    applyBtn.addEventListener("click", async () => {
      if (inFlight) return;
      const value = Number(slider.value);

      if (!Number.isInteger(value) || value < 0 || value > 255) {
        showToast("Invalid PWM value (0-255)", "error");
        return;
      }

      inFlight = true;
      slider.disabled = true;
      applyBtn.disabled = true;
      const oldText = applyBtn.textContent;
      applyBtn.textContent = "Applying...";

      try {
        await postPWM(value);
        showToast(`PWM set to ${value}`);
      } catch (err) {
        showToast(`PWM apply failed: ${err.message}`, "error");
      } finally {
        inFlight = false;
        slider.disabled = false;
        applyBtn.disabled = false;
        applyBtn.textContent = oldText;
      }
    });
  });
})();
