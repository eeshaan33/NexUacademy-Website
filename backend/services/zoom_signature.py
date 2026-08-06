"""Zoom Meeting SDK JWT signature generator.

The Web Meeting SDK (v3+) authorises the browser client using an HS256 JWT
signed with the SDK Client Secret. The current (2026) payload format uses
`appKey` (SDK Client ID), `mn`, `role`, `iat`, `exp`, `tokenExp` — the legacy
`sdkKey` property is deprecated and must not be sent in `join()`.

Reference: https://developers.zoom.us/docs/meeting-sdk/auth/
"""
import os
import time
import logging

import jwt
from fastapi import HTTPException

logger = logging.getLogger(__name__)


def generate_meeting_signature(meeting_number: str, role: int = 0,
                               validity_seconds: int = 60 * 60 * 2) -> str:
    """Generate a Meeting SDK JWT.

    role: 0 = attendee (student), 1 = host (teacher)
    """
    if role not in (0, 1):
        raise HTTPException(status_code=400, detail="role must be 0 (attendee) or 1 (host)")
    sdk_key = os.environ.get("ZOOM_SDK_CLIENT_ID", "").strip()
    sdk_secret = os.environ.get("ZOOM_SDK_CLIENT_SECRET", "").strip()
    if not sdk_key or not sdk_secret:
        raise HTTPException(status_code=500, detail="Zoom Meeting SDK is not configured")

    iat = int(time.time()) - 30  # small clock-skew allowance
    exp = iat + max(1800, int(validity_seconds))  # min 1800s per Zoom rules

    payload = {
        "appKey": sdk_key,
        "sdkKey": sdk_key,  # keep for older SDK versions still reading it
        "mn": str(meeting_number),
        "role": role,
        "iat": iat,
        "exp": exp,
        "tokenExp": exp,
    }
    return jwt.encode(payload, sdk_secret, algorithm="HS256")
