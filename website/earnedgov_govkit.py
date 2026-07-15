"""GovKit invite client for the Earned Governance Accelerator doorway.

GovKit (the accelerator dashboard) mints and owns invites — one home per fact.
The doorway holds no invite state: it resolves an opaque code server-to-server,
renders the personalized commit page, and reports the commitment back. Contract
agreed between the doorway and dashboard sessions in govkit/scratch.md
(2026-07-13):

    GET  {base}/api/v1/orgs/{slug}/invites/{code}/            -> invite dict
    POST {base}/api/v1/orgs/{slug}/invites/{code}/committed/  -> mark committed

Both authenticated with `Authorization: Bearer GOVKIT_S2S_TOKEN`. The GET
payload includes `accept_url` (GovKit's SSO accept ceremony) — the doorway
never constructs GovKit URLs. Invite statuses: created -> committed ->
accepted, plus revoked.
"""
import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

_TIMEOUT = 8


class GovKitUnavailable(Exception):
    """GovKit could not be reached (network/5xx) — distinct from a bad code."""


def _api_base():
    base = getattr(settings, "GOVKIT_BASE_URL", "").rstrip("/")
    slug = getattr(settings, "GOVKIT_ORG_SLUG", "")
    token = getattr(settings, "GOVKIT_S2S_TOKEN", "")
    if not (base and slug and token):
        return None, None
    return f"{base}/api/v1/orgs/{slug}/invites", {"Authorization": f"Bearer {token}"}


def resolve_invite(code):
    """Return the invite dict for a code, or None if the code is not valid.

    Raises GovKitUnavailable when GovKit can't answer (so the page can say
    "try again in a minute" instead of telling a real invitee their link is bad).
    Returns None when the client is unconfigured — an unconfigured doorway has
    no valid invites, it doesn't have unreachable ones.
    """
    base, headers = _api_base()
    if base is None or not code:
        return None
    try:
        r = requests.get(f"{base}/{code}/", headers=headers, timeout=_TIMEOUT)
    except requests.RequestException as e:
        logger.warning("earnedgov: govkit resolve unreachable: %s", e)
        raise GovKitUnavailable() from e
    if r.status_code in (404, 410):
        return None
    if r.status_code != 200:
        # 401/403 is a token misconfiguration between the two sides — a real
        # invitee's link isn't bad, we are. Same for 5xx.
        logger.warning("earnedgov: govkit resolve returned %s", r.status_code)
        raise GovKitUnavailable()
    data = r.json()
    # `audience` is the wall vocabulary (advisor|mentor|partner|funder|founder|
    # supporter); tolerate older payloads that only send `role`.
    data.setdefault("audience", data.get("role", "supporter"))
    return data


def report_committed(code, *, claim_id, statement, video_url=None):
    """Tell GovKit the invitee committed (idempotent on their side).

    Returns True on success. Failure is logged, not raised — the claim is
    already on LinkedTrust and the wall; GovKit status catches up on retry
    (the success page re-reports if the invite still shows 'created').
    """
    base, headers = _api_base()
    if base is None:
        return False
    payload = {"claim_id": claim_id, "statement_as_published": statement}
    if video_url:
        payload["video_url"] = video_url
    try:
        r = requests.post(
            f"{base}/{code}/committed/", json=payload, headers=headers, timeout=_TIMEOUT
        )
    except requests.RequestException as e:
        logger.warning("earnedgov: govkit committed callback unreachable: %s", e)
        return False
    if r.status_code in (200, 201, 204):
        return True
    logger.warning("earnedgov: govkit committed callback returned %s", r.status_code)
    return False


# Factual, audience-scoped starter statements, used ONLY when the inviter left
# the drafted statement empty. The invitee is told these are replaceable with
# their own words — we never publish enthusiasm we invented. Language per the
# 2026-07-15 pin: joins/launch/backing, never "committing".
AUDIENCE_STATEMENTS = {
    "mentor": "I'm joining the Earned Governance Accelerator as a mentor.",
    "advisor": "I'm joining the Earned Governance Accelerator as an advisor.",
    "partner": "We're partnering with the Earned Governance Accelerator.",
    "funder": "I'm backing the Earned Governance Accelerator.",
    "founder": "We're taking our venture through the Earned Governance Accelerator.",
    "supporter": "I support the Earned Governance Accelerator.",
}
