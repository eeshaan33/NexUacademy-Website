"""
Zoom Server-to-Server OAuth + Meeting API wrapper.

- Uses S2S OAuth app credentials for token exchange (ZOOM_S2S_*).
- Token cache with 60s early-refresh window.
- Wraps create/delete/get meeting + host ZAK fetch + participants report.
"""
import asyncio
import base64
import logging
import os
import time
from typing import Any, Optional

import httpx
from fastapi import HTTPException

logger = logging.getLogger(__name__)

_TOKEN: dict[str, Any] | None = None
_TOKEN_LOCK = asyncio.Lock()

ZOOM_API_BASE = "https://api.zoom.us/v2"
ZOOM_OAUTH_URL = "https://zoom.us/oauth/token"


def _cfg(name: str) -> str:
    val = os.environ.get(name, "").strip()
    if not val:
        raise HTTPException(status_code=500, detail=f"Zoom is not configured: missing {name}")
    return val


async def get_access_token() -> str:
    """Return a valid S2S OAuth access token; cache until ~60s before expiry."""
    global _TOKEN
    now = int(time.time())
    if _TOKEN and now < _TOKEN["expires_at"] - 60:
        return _TOKEN["access_token"]

    async with _TOKEN_LOCK:
        now = int(time.time())
        if _TOKEN and now < _TOKEN["expires_at"] - 60:
            return _TOKEN["access_token"]

        client_id = _cfg("ZOOM_S2S_CLIENT_ID")
        client_secret = _cfg("ZOOM_S2S_CLIENT_SECRET")
        account_id = _cfg("ZOOM_S2S_ACCOUNT_ID")

        basic = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.post(
                ZOOM_OAUTH_URL,
                headers={"Authorization": f"Basic {basic}"},
                data={"grant_type": "account_credentials", "account_id": account_id},
            )
        if r.status_code != 200:
            logger.error(f"Zoom OAuth failed: {r.status_code} {r.text[:400]}")
            raise HTTPException(status_code=502, detail="Zoom authorization failed")
        body = r.json()
        _TOKEN = {**body, "expires_at": now + int(body["expires_in"])}
        return _TOKEN["access_token"]


async def _zoom_request(method: str, path: str, **kwargs) -> Optional[dict]:
    token = await get_access_token()
    async with httpx.AsyncClient(base_url=ZOOM_API_BASE, timeout=20) as c:
        r = await c.request(
            method,
            path,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            **kwargs,
        )
    if r.status_code in (200, 201, 204):
        if r.content:
            try:
                return r.json()
            except Exception:
                return None
        return None
    if r.status_code == 404:
        raise HTTPException(status_code=404, detail="Zoom resource not found")
    logger.error(f"Zoom {method} {path} -> {r.status_code}: {r.text[:500]}")
    raise HTTPException(status_code=502, detail=f"Zoom API error: {r.text[:200]}")


async def create_meeting(topic: str, start_time_iso: str, duration_min: int,
                         host_email: Optional[str] = None) -> dict:
    """Create a scheduled meeting. Uses `/users/{host}/meetings` where host is
    the S2S app user (`me`) by default; caller may pass a teacher's Zoom email
    if that user exists in the Zoom account."""
    host = host_email or "me"
    payload = {
        "topic": topic,
        "type": 2,  # scheduled
        "start_time": start_time_iso,
        "duration": max(1, int(duration_min or 60)),
        "timezone": "Asia/Kolkata",
        "settings": {
            "host_video": True,
            "participant_video": False,
            "join_before_host": False,
            "mute_upon_entry": True,
            "waiting_room": False,
            "approval_type": 2,
            "audio": "both",
            "auto_recording": "none",
        },
    }
    try:
        return await _zoom_request("POST", f"/users/{host}/meetings", json=payload)
    except HTTPException as e:
        # Fallback: if host_email doesn't exist on the account, retry with `me`
        if host != "me" and (e.status_code in (404, 502)):
            logger.warning(f"Host {host_email} not found in Zoom account, retrying with /users/me")
            return await _zoom_request("POST", "/users/me/meetings", json=payload)
        raise


async def delete_meeting(meeting_id: str) -> None:
    await _zoom_request("DELETE", f"/meetings/{meeting_id}")


async def get_host_zak(host_email: Optional[str] = None) -> Optional[str]:
    """Fetch the ZAK token for the host user (required to start a meeting via Web SDK).
    Returns None if the API isn't available so the host flow can still open Zoom in a new tab."""
    host = host_email or "me"
    try:
        data = await _zoom_request("GET", f"/users/{host}/token", params={"type": "zak"})
        return (data or {}).get("token")
    except HTTPException:
        if host != "me":
            try:
                data = await _zoom_request("GET", "/users/me/token", params={"type": "zak"})
                return (data or {}).get("token")
            except HTTPException:
                return None
        return None


async def get_live_participants(meeting_id: str) -> list[dict]:
    """Return live participants via metrics/dashboard. Requires the dashboard scope
    and may 404 if the plan doesn't include it — we return [] on failure."""
    try:
        data = await _zoom_request(
            "GET", f"/metrics/meetings/{meeting_id}/participants",
            params={"type": "live", "page_size": 300},
        )
        return (data or {}).get("participants", [])
    except HTTPException:
        return []
