"""Read-only view into the Odoo CRM (compose, don't own). The console shows recent
leads alongside the site's own inquiries. Guarded and defensive: with no ODOO_*
config it reports not-connected and returns nothing, and any Odoo/network failure
degrades to an empty list rather than breaking the console (never a bad experience).

Config (settings, from env):
    ODOO_URL       e.g. http://10.0.0.100:8069   (reachable from the app host)
    ODOO_DB        default "linkedtrust_crm"
    ODOO_USER
    ODOO_API_KEY
"""
from __future__ import annotations

import logging
import xmlrpc.client

from django.conf import settings

logger = logging.getLogger(__name__)
LEAD_FIELDS = ["name", "contact_name", "email_from", "user_id", "stage_id", "write_date"]


def configured() -> bool:
    return bool(getattr(settings, "ODOO_URL", "") and getattr(settings, "ODOO_USER", "")
                and getattr(settings, "ODOO_API_KEY", ""))


def recent_leads(limit: int = 50) -> list[dict]:
    if not configured():
        return []
    url = settings.ODOO_URL.rstrip("/")
    db = getattr(settings, "ODOO_DB", "linkedtrust_crm")
    user = settings.ODOO_USER
    key = settings.ODOO_API_KEY
    try:
        common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
        uid = common.authenticate(db, user, key, {})
        if not uid:
            logger.warning("Odoo CRM auth returned no uid")
            return []
        models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")
        rows = models.execute_kw(db, uid, key, "crm.lead", "search_read", [[]],
                                 {"fields": LEAD_FIELDS, "order": "id desc", "limit": limit})
    except Exception as exc:  # network, auth, XML-RPC — degrade, never raise
        logger.warning("Odoo CRM read failed: %s", exc)
        return []
    out = []
    for r in rows:
        out.append({
            "id": r["id"],
            "name": (r.get("contact_name") or r.get("name") or "").strip(),
            "title": (r.get("name") or "").strip(),
            "email": (r.get("email_from") or "").strip(),
            "owner": r["user_id"][1] if r.get("user_id") else "Unassigned",
            "stage": r["stage_id"][1] if r.get("stage_id") else "",
            "updated": (r.get("write_date") or "")[:10],
        })
    return out
