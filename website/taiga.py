"""Read-only view into Taiga (compose, don't own). The console shows recent user
stories/tasks beside the inquiries and CRM. Guarded and defensive like the CRM
view: with no TAIGA_* config it reports not-connected, and any API/network failure
degrades to an empty list rather than breaking the console.

Config (settings, from env):
    TAIGA_URL     default https://taiga.linkedtrust.us
    TAIGA_TOKEN   a bearer token for the Taiga API
"""
from __future__ import annotations

import json
import logging
from urllib.request import Request, urlopen

from django.conf import settings

logger = logging.getLogger(__name__)
TIMEOUT = 12


def configured() -> bool:
    return bool(getattr(settings, "TAIGA_URL", "") and getattr(settings, "TAIGA_TOKEN", ""))


def recent_items(limit: int = 40) -> list[dict]:
    if not configured():
        return []
    base = settings.TAIGA_URL.rstrip("/")
    url = f"{base}/api/v1/userstories?page_size={int(limit)}&order_by=-modified_date"
    req = Request(url, method="GET")
    req.add_header("Authorization", f"Bearer {settings.TAIGA_TOKEN}")
    req.add_header("Accept", "application/json")
    try:
        with urlopen(req, timeout=TIMEOUT) as resp:  # nosec B310 - fixed Taiga host
            rows = json.loads(resp.read().decode("utf-8"))
    except Exception as exc:  # network, auth, parse — degrade, never raise
        logger.warning("Taiga read failed: %s", exc)
        return []
    if not isinstance(rows, list):
        return []
    out = []
    for r in rows[:limit]:
        status = (r.get("status_extra_info") or {}).get("name", "")
        assignee = (r.get("assigned_to_extra_info") or {}).get("full_name_display", "")
        project = (r.get("project_extra_info") or {}).get("name", "")
        out.append({
            "id": r.get("id"),
            "ref": r.get("ref"),
            "subject": (r.get("subject") or "").strip(),
            "status": status,
            "assignee": assignee or "Unassigned",
            "project": project,
            "updated": (r.get("modified_date") or "")[:10],
        })
    return out
