"""Attestations as LinkedClaims (Golda's model: don't let them live only in the
Django DB). When a real inquiry is contacted, publish a 'contacted' LinkedClaim to
the trust graph; the Django contacted flag + contacted_claim_id become a local
cache/projection of that claim.

Publishing is OFF by default (CONSOLE_PUBLISH_CLAIMS) because it is an outward,
public action, and posting to EARNEDGOV_LT_API writes a real live claim. Flip it on
deliberately. It never raises: the Django flag is always written by the caller, so
the console works whether or not the claim went out.
"""
from __future__ import annotations

import logging
from datetime import date

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def _lt_api() -> str:
    return getattr(settings, "EARNEDGOV_LT_API", "https://live.linkedtrust.us").rstrip("/")


def publishing_enabled() -> bool:
    return bool(getattr(settings, "CONSOLE_PUBLISH_CLAIMS", False))


def publish_contacted(inquiry, by: str):
    """Publish a 'contacted' LinkedClaim for this inquiry. Returns the claim id, or
    None when disabled, un-addressable, or the API call fails (never raises)."""
    if not publishing_enabled():
        return None
    email = (getattr(inquiry, "email", "") or "").strip()
    if not email:
        return None
    payload = {
        "subject": f"mailto:{email}",
        "claim": "contacted",
        "object": "https://linkedtrust.us/",
        "statement": f"{by} reached out to this contact-form inquiry on behalf of LinkedTrust.",
        "howKnown": "FIRST_HAND",
        "sourceURI": "https://linkedtrust.us/console/",
        "effectiveDate": date.today().isoformat(),
        "confidence": 1.0,
    }
    try:
        r = requests.post(f"{_lt_api()}/api/claims", json=payload, timeout=20)
        r.raise_for_status()
        claim = r.json().get("claim", {}) or {}
        return str(claim.get("id") or "")
    except Exception as exc:
        logger.warning("contacted LinkedClaim publish failed: %s", exc)
        return None
