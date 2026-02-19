import os

from fastapi import Header, HTTPException


def require_bearer_token(authorization: str = Header(default="")) -> None:
    expected = os.getenv("TRUEFAN_AGENT_SECRET", "").strip()
    if not expected:
        raise HTTPException(status_code=503, detail="TRUEFAN_AGENT_SECRET is not configured")

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")

    token = authorization[len("Bearer ") :].strip()
    if token != expected:
        raise HTTPException(status_code=403, detail="Invalid token")
