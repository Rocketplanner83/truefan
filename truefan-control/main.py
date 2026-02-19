import logging
import os
from typing import Dict, List

from fastapi import Depends, FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from hwmon import get_hwmon_map
from pwm import discover_pwm_files, read_current_pwm, write_pwm_value
from security import require_bearer_token

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
LOGGER = logging.getLogger("truefan-control")

if not os.getenv("TRUEFAN_AGENT_SECRET", "").strip():
    raise RuntimeError("TRUEFAN_AGENT_SECRET is required at startup")

app = FastAPI(title="truefan-control")


class SetPwmBody(BaseModel):
    pwm: int = Field(..., ge=0, le=255)


def _status_payload() -> Dict[str, object]:
    hwmon_map = get_hwmon_map()
    available_pwms = discover_pwm_files()
    current_pwm = read_current_pwm(available_pwms)
    return {
        "available_pwms": available_pwms,
        "current_pwm": current_pwm,
        "hwmon_map": hwmon_map,
    }


@app.get("/status")
def status(_: None = Depends(require_bearer_token)):
    try:
        return _status_payload()
    except Exception:
        LOGGER.exception("Failed to build status")
        return {
            "available_pwms": [],
            "current_pwm": 0,
            "hwmon_map": {},
        }


@app.post("/set_pwm")
def set_pwm(body: SetPwmBody, _: None = Depends(require_bearer_token)):
    try:
        available_pwms: List[str] = discover_pwm_files()
        target = write_pwm_value(body.pwm, available_pwms)
        if target is None:
            return JSONResponse(
                status_code=404,
                content={
                    "status": "error",
                    "message": "No writable PWM files detected",
                    "available_pwms": available_pwms,
                },
            )

        return {
            "status": "ok",
            "pwm": body.pwm,
            "target": target,
            "available_pwms": available_pwms,
        }
    except Exception:
        LOGGER.exception("Failed to set PWM")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "Failed to set PWM",
                "available_pwms": [],
            },
        )


@app.exception_handler(Exception)
async def handle_unexpected(_request, exc: Exception):
    LOGGER.exception("Unhandled error: %s", exc)
    return JSONResponse(status_code=500, content={"status": "error", "message": "internal_error"})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=5088)
