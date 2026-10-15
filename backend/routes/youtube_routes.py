"""Fetch the latest public video from the NexUacademy YouTube channel via RSS.

RSS feed (`/feeds/videos.xml?channel_id=UC...`) is not bot-gated and returns
titles verbatim. No API key needed. Cached 1 hour.

Two-step lookup:
  1. Resolve channel_id from the @handle page (cached forever).
  2. Fetch RSS feed and read the first <entry>.
"""
import logging
import os
import re
import time
from typing import Optional

import httpx
from fastapi import APIRouter

router = APIRouter(prefix="/youtube", tags=["youtube"])
logger = logging.getLogger(__name__)

_CACHE = {"video_id": None, "title": None, "fetched_at": 0.0,
          "channel_id": None}
_TTL_SECONDS = 60 * 60  # 1 hour

UA = {"User-Agent": "Mozilla/5.0", "Accept-Language": "en-US,en;q=0.9"}


async def _resolve_channel_id(client: httpx.AsyncClient, handle: str) -> Optional[str]:
    if _CACHE.get("channel_id"):
        return _CACHE["channel_id"]
    r = await client.get(f"https://www.youtube.com/@{handle}")
    if r.status_code != 200:
        logger.warning(f"youtube handle page {r.status_code}")
        return None
    html = r.text
    m = (re.search(r'"channelId":"(UC[A-Za-z0-9_-]{22})"', html)
         or re.search(r'itemprop="identifier" content="(UC[A-Za-z0-9_-]{22})"', html))
    if not m:
        return None
    _CACHE["channel_id"] = m.group(1)
    return _CACHE["channel_id"]


async def _fetch_latest_from_rss(client: httpx.AsyncClient, channel_id: str) -> Optional[dict]:
    r = await client.get(f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}")
    if r.status_code != 200:
        logger.warning(f"youtube rss {r.status_code}")
        return None
    rss = r.text
    # First entry after the channel-level <title> is the newest upload.
    id_m = re.search(r"<yt:videoId>([A-Za-z0-9_-]{11})</yt:videoId>", rss)
    if not id_m:
        return None
    # Extract the title inside the SAME <entry> as this videoId.
    entry_m = re.search(
        r"<entry>(.*?)</entry>",
        rss,
        re.DOTALL,
    )
    title = None
    if entry_m:
        entry = entry_m.group(1)
        t_m = re.search(r"<title>([^<]+)</title>", entry)
        if t_m:
            # Decode a couple common HTML entities so &amp; / &#39; render nicely.
            title = (t_m.group(1)
                     .replace("&amp;", "&")
                     .replace("&#39;", "'")
                     .replace("&quot;", '"')
                     .replace("&lt;", "<")
                     .replace("&gt;", ">"))
    return {"video_id": id_m.group(1), "title": title}


@router.get("/latest")
async def latest_video():
    """Returns { success, video_id, title, embed_url } for the channel's most
    recent public upload. Cached 1 hour."""
    handle = os.environ.get("YOUTUBE_CHANNEL_HANDLE", "NexUacademypvtltd")
    now = time.time()

    if _CACHE["video_id"] and (now - _CACHE["fetched_at"]) < _TTL_SECONDS:
        vid = _CACHE["video_id"]
        return {"success": True, "video_id": vid, "title": _CACHE.get("title"),
                "embed_url": f"https://www.youtube.com/embed/{vid}", "cached": True}

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=8.0, headers=UA) as client:
            cid = await _resolve_channel_id(client, handle)
            data = await _fetch_latest_from_rss(client, cid) if cid else None
    except Exception as e:
        logger.warning(f"YouTube fetch failed: {e}")
        data = None

    if data:
        _CACHE["video_id"] = data["video_id"]
        _CACHE["title"] = data.get("title")
        _CACHE["fetched_at"] = now
        vid = data["video_id"]
        return {"success": True, "video_id": vid, "title": _CACHE["title"],
                "embed_url": f"https://www.youtube.com/embed/{vid}", "cached": False}

    vid = _CACHE.get("video_id")
    return {"success": bool(vid), "video_id": vid, "title": _CACHE.get("title"),
            "embed_url": f"https://www.youtube.com/embed/{vid}" if vid else None,
            "cached": True, "note": "Live fetch failed; returning last known video."}
