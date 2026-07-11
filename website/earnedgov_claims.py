"""LinkedTrust claim plumbing for the Earned Governance Accelerator pages.

The accelerator's data spine is LinkedTrust: a commitment is a claim
    <person-uri>  COMMITS_TO  https://linkedtrust.us/earnedgov
with the role in `aspect`, the person's words in `statement`, and
howKnown FIRST_HAND (they said it themselves) or SECOND_HAND (someone
they told is vouching).  This module is the only place the site talks
to the LinkedTrust API.

No local storage: the wall is rebuilt from the API on a short cache.
"""
import base64
import logging
from datetime import date

import requests
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

LT_API = getattr(settings, "EARNEDGOV_LT_API", "https://live.linkedtrust.us")
EFFORT_URI = "https://linkedtrust.us/earnedgov"
# Older anchor claims used the demos URL for the same effort.
EFFORT_URIS = {EFFORT_URI, "https://demos.linkedtrust.us/earnedgov"}
COMMIT_VERB = "COMMITS_TO"
OPP_VERB = "OPPORTUNITY"
OPP_KINDS = ["venture", "project", "partnership", "grant", "role"]
ROLES = ["advisor", "mentor", "partner", "founder", "supporter"]
ROLE_LABELS = {
    "advisor": "Advisors",
    "mentor": "Mentors",
    "partner": "Partners",
    "founder": "Founders",
    "supporter": "Supporters",
}
_CACHE_KEY = "earnedgov_commitments_v1"
_TIMEOUT = 8


def _get(path, **params):
    r = requests.get(f"{LT_API}{path}", params=params or None, timeout=_TIMEOUT)
    r.raise_for_status()
    return r.json()


def _claim_url(claim_id):
    return f"{LT_API}/claims/{claim_id}"


def _subject_display(detail):
    """Pull the person's display name / image out of the claim's graph nodes."""
    claim = detail.get("claim", detail)
    subject_uri = claim.get("subject", "")
    name, image = None, None
    for edge in claim.get("edges", []):
        for key in ("startNode", "endNode"):
            node = edge.get(key) or {}
            if node.get("nodeUri") == subject_uri:
                name = name or node.get("name")
                image = image or node.get("image") or node.get("thumbnail")
    return name, image


def _media(detail):
    """Return (image_url, video_url) for a claim detail response."""
    image_url, video_url = None, None
    for img in detail.get("images", []) or []:
        url = img.get("url") or ""
        is_video = (img.get("metadata") or {}).get("type") == "video" or url.endswith(".webm")
        if url.startswith("data:") and img.get("id"):
            url = f"{LT_API}/api/images/{img['id']}"
        if is_video and not video_url:
            video_url = url
        elif not is_video and not image_url:
            image_url = url
    return image_url, video_url


def fetch_commitments():
    """All COMMITS_TO claims for the accelerator, grouped by role.

    Per subject, a FIRST_HAND (self-attested) claim wins over SECOND_HAND
    vouches — that's the "step up" rule: when someone replaces a vouch
    with their own signed words, the wall shows their version.
    """
    cached = cache.get(_CACHE_KEY)
    if cached is not None:
        return cached

    try:
        feed = _get("/api/feed", query="linkedtrust.us/earnedgov", limit=100)
        ids = [
            e["id"]
            for e in feed.get("entries", [])
            if e.get("claim") == COMMIT_VERB
            and (e.get("object") or {}).get("uri") in EFFORT_URIS
        ]
        by_subject = {}
        for cid in ids:
            try:
                detail = _get(f"/api/claims/{cid}")
            except Exception:
                logger.warning("earnedgov: failed to fetch claim %s", cid)
                continue
            claim = detail.get("claim", detail)
            name, node_image = _subject_display(detail)
            image_url, video_url = _media(detail)
            item = {
                "id": cid,
                "subject_uri": claim.get("subject"),
                "name": name or claim.get("subject", "").rstrip("/").split("/")[-1].replace("-", " ").title(),
                "role": (claim.get("aspect") or "supporter").lower(),
                "statement": claim.get("statement") or "",
                "how_known": claim.get("howKnown"),
                "self_attested": claim.get("howKnown") == "FIRST_HAND",
                "source_uri": claim.get("sourceURI"),
                "date": (claim.get("effectiveDate") or "")[:10],
                "image": image_url or node_image,
                "video": video_url,
                "claim_url": _claim_url(cid),
            }
            prev = by_subject.get(item["subject_uri"])
            if prev is None or _wins(item, prev):
                by_subject[item["subject_uri"]] = item

        groups = []
        for role in ROLES:
            members = sorted(
                (i for i in by_subject.values() if i["role"] == role),
                key=lambda i: i["date"],
                reverse=True,
            )
            if members:
                groups.append({"role": role, "label": ROLE_LABELS[role], "members": members})
        result = {"groups": groups, "count": len(by_subject)}
    except Exception:
        logger.exception("earnedgov: commitment wall fetch failed")
        result = {"groups": [], "count": 0, "error": True}

    cache.set(_CACHE_KEY, result, 60)
    return result


def _wins(a, b):
    if a["self_attested"] != b["self_attested"]:
        return a["self_attested"]
    return a["date"] > b["date"]


def fetch_opportunities():
    """OPPORTUNITY claims on the effort: adoptable openings for the cohort.

    Shape: <opportunity-uri> OPPORTUNITY <effort-uri>; title in the node name,
    kind in `aspect`, description in `statement`.
    """
    cache_key = _CACHE_KEY + "_opps"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached
    try:
        feed = _get("/api/feed", query="linkedtrust.us/earnedgov", limit=100)
        ids = [
            e["id"]
            for e in feed.get("entries", [])
            if e.get("claim") == OPP_VERB
            and (e.get("object") or {}).get("uri") in EFFORT_URIS
        ]
        opps = []
        for cid in ids:
            try:
                detail = _get(f"/api/claims/{cid}")
            except Exception:
                continue
            claim = detail.get("claim", detail)
            name, _img = _subject_display(detail)
            opps.append({
                "id": cid,
                "subject_uri": claim.get("subject"),
                "title": name or claim.get("subject", "").split("#")[-1].replace("-", " ").title(),
                "kind": (claim.get("aspect") or "project").lower(),
                "statement": claim.get("statement") or "",
                "source_uri": claim.get("sourceURI"),
                "date": (claim.get("effectiveDate") or "")[:10],
                "claim_url": _claim_url(cid),
            })
        opps.sort(key=lambda o: o["date"], reverse=True)
        result = {"opps": opps, "count": len(opps)}
    except Exception:
        logger.exception("earnedgov: opportunities fetch failed")
        result = {"opps": [], "count": 0, "error": True}
    cache.set(cache_key, result, 60)
    return result


def create_opportunity(*, title, kind, statement, link=None, poster_uri=None):
    """Create an OPPORTUNITY claim. The opportunity's URI is its own link if it
    has one, else an anchor under the effort page."""
    from django.utils.text import slugify
    subject = link or f"{EFFORT_URI}#opp-{slugify(title)}"
    payload = {
        "subject": subject,
        "claim": OPP_VERB,
        "object": EFFORT_URI,
        "statement": statement,
        "aspect": kind if kind in OPP_KINDS else "project",
        "name": title,
        "howKnown": "FIRST_HAND",
        "sourceURI": poster_uri or EFFORT_URI,
        "effectiveDate": date.today().isoformat(),
        "confidence": 1.0,
    }
    r = requests.post(f"{LT_API}/api/claims", json=payload, timeout=30)
    r.raise_for_status()
    cache.delete(_CACHE_KEY + "_opps")
    return r.json().get("claim", {})


def fetch_claim(claim_id, verbs=(COMMIT_VERB, OPP_VERB)):
    """One claim, for step-up/adopt prefills. Returns None if unavailable."""
    try:
        detail = _get(f"/api/claims/{int(claim_id)}")
        claim = detail.get("claim", detail)
        if claim.get("claim") not in verbs:
            return None
        name, _ = _subject_display(detail)
        return {
            "id": claim.get("id"),
            "verb": claim.get("claim"),
            "subject_uri": claim.get("subject"),
            "name": name,
            "role": (claim.get("aspect") or "supporter").lower(),
            "statement": claim.get("statement") or "",
            "how_known": claim.get("howKnown"),
        }
    except Exception:
        logger.warning("earnedgov: could not fetch claim %s for upgrade", claim_id)
        return None


def create_commitment(
    *,
    subject_uri,
    name,
    role,
    statement,
    self_attested,
    voucher_uri=None,
    photo_file=None,
    video_url=None,
):
    """Create the COMMITS_TO claim on LinkedTrust. Returns the new claim dict.

    Raises requests.HTTPError / requests.RequestException on failure —
    callers surface that as a form error, nothing is stored locally.
    """
    payload = {
        "subject": subject_uri,
        "claim": COMMIT_VERB,
        "object": EFFORT_URI,
        "statement": statement,
        "aspect": role,
        "name": name,
        "subjectEntityType": "PERSON",
        "howKnown": "FIRST_HAND" if self_attested else "SECOND_HAND",
        "sourceURI": (voucher_uri if not self_attested else subject_uri) or subject_uri,
        "effectiveDate": date.today().isoformat(),
        "confidence": 1.0,
    }
    if video_url:
        payload["videoUrl"] = video_url
    if photo_file is not None:
        raw = photo_file.read()
        if len(raw) > 10 * 1024 * 1024:
            raise ValueError("Photo is larger than 10MB")
        payload["images"] = [
            {
                "filename": photo_file.name,
                "contentType": photo_file.content_type or "image/jpeg",
                "base64": base64.b64encode(raw).decode("ascii"),
                "metadata": {"description": f"Photo of {name}"},
                "effectiveDate": date.today().isoformat(),
            }
        ]

    r = requests.post(f"{LT_API}/api/claims", json=payload, timeout=30)
    r.raise_for_status()
    cache.delete(_CACHE_KEY)
    return r.json().get("claim", {})
