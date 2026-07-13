"""Personal invite links for the Earned Governance Accelerator.

An invite is a stateless signed token (same pattern GovKit uses): it encodes
who the person is (name, link), what they're being invited as (role), and who
invited them — so the commit page can greet them by name, prefill everything,
and publish their commitment to the wall instantly. Possession of a valid
link is what separates an invited commitment (auto-published) from a walk-up
(held for review) — that's the spam gate.
"""
from django.core import signing

SALT = "earnedgov.invite"
MAX_AGE = 60 * 60 * 24 * 30  # 30 days


def make_invite(*, name, link="", role="mentor", inviter="Golda", email=""):
    payload = {"n": name, "l": link, "r": role, "i": inviter}
    if email:
        payload["e"] = email
    return signing.dumps(payload, salt=SALT)


def read_invite(token):
    """Return the invite dict or None (invalid/expired)."""
    try:
        p = signing.loads(token, salt=SALT, max_age=MAX_AGE)
    except (signing.BadSignature, signing.SignatureExpired):
        return None
    return {
        "name": p.get("n", ""),
        "link": p.get("l", ""),
        "role": p.get("r", "mentor"),
        "inviter": p.get("i", "the team"),
        "email": p.get("e", ""),
    }


# Factual, role-scoped starter statements. The invitee is told these are
# replaceable with their own words — we never publish enthusiasm we invented.
ROLE_STATEMENTS = {
    "mentor": "I'm committing to mentor teams in the Earned Governance Accelerator.",
    "advisor": "I'm committing as an advisor to the Earned Governance Accelerator.",
    "partner": "We're committing as a partner of the Earned Governance Accelerator.",
    "funder": "I'm committing as a funder/supporter of the Earned Governance Accelerator.",
    "founder": "I'm committing to build in the Earned Governance Accelerator cohort.",
    "supporter": "I support the Earned Governance Accelerator.",
}
