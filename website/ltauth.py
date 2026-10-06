"""LinkedTrust SSO for this site (server-side OIDC authorization-code flow).

Adapted from the vendored session flow in govkit/apps/accounts. It adds a
"Sign in with LinkedTrust" option ALONGSIDE the normal Django admin login, never
replacing it, so no one can be locked out. It is secure by default: the callback
only logs in a Django user that ALREADY exists and is active, matched by email,
and never creates an account or grants staff. Unknown emails are turned away.

Config (settings, from env; the button hides itself when CLIENT_ID is empty):
    LINKEDTRUST_URL            default https://live.linkedtrust.us
    LINKEDTRUST_CLIENT_ID      from env
    LINKEDTRUST_CLIENT_SECRET  from env
    LINKEDTRUST_SCOPES         default "openid email profile trust"
Register a confidential OIDC client at LINKEDTRUST_URL with redirect_uri
    https://linkedtrust.us/auth/linkedtrust/callback/
"""
from __future__ import annotations

import json
import logging
import secrets
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme

logger = logging.getLogger(__name__)
STATE_KEY = "lt_oauth_state"
NEXT_KEY = "lt_post_login_next"
TIMEOUT = 15


def _issuer():
    return getattr(settings, "LINKEDTRUST_URL", "https://live.linkedtrust.us").rstrip("/")


def _redirect_uri(request):
    return request.build_absolute_uri(reverse("ltauth_callback"))


def _get_json(url, headers=None):
    req = Request(url, method="GET", headers=headers or {})
    req.add_header("Accept", "application/json")
    with urlopen(req, timeout=TIMEOUT) as r:  # nosec B310 - fixed IdP host
        return json.loads(r.read().decode("utf-8"))


def _post_form(url, data):
    body = urlencode({k: v for k, v in data.items() if v is not None}).encode()
    req = Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    req.add_header("Accept", "application/json")
    with urlopen(req, timeout=TIMEOUT) as r:  # nosec B310 - fixed IdP host
        return json.loads(r.read().decode("utf-8"))


def _safe_next(request, raw):
    if raw and url_has_allowed_host_and_scheme(raw, {request.get_host()}, require_https=request.is_secure()):
        return raw
    return None


def start(request):
    """Begin the OIDC flow: stash state + next, redirect to the IdP."""
    if not getattr(settings, "LINKEDTRUST_CLIENT_ID", ""):
        messages.error(request, "LinkedTrust sign-in is not configured yet.")
        return redirect(settings.LOGIN_URL if hasattr(settings, "LOGIN_URL") else "/admin/login/")
    state = secrets.token_urlsafe(24)
    request.session[STATE_KEY] = state
    request.session[NEXT_KEY] = _safe_next(request, request.GET.get("next")) or "/console/"
    params = urlencode({
        "response_type": "code",
        "client_id": settings.LINKEDTRUST_CLIENT_ID,
        "redirect_uri": _redirect_uri(request),
        "scope": getattr(settings, "LINKEDTRUST_SCOPES", "openid email profile trust"),
        "state": state,
    })
    return redirect(f"{_issuer()}/oauth/authorize?{params}")


def callback(request):
    """Handle the IdP redirect: verify state, exchange code, resolve an EXISTING
    active user by email, log them into the session. Never provisions or elevates."""
    login_url = "/admin/login/"
    expected = request.session.pop(STATE_KEY, None)
    next_url = request.session.pop(NEXT_KEY, "/console/")
    if not expected or request.GET.get("state") != expected:
        messages.error(request, "Sign-in expired or was tampered with. Try again.")
        return redirect(login_url)
    code = request.GET.get("code")
    if not code:
        messages.error(request, "LinkedTrust did not return an authorization code.")
        return redirect(login_url)
    try:
        tokens = _post_form(f"{_issuer()}/oauth/token", {
            "grant_type": "authorization_code", "code": code,
            "redirect_uri": _redirect_uri(request),
            "client_id": settings.LINKEDTRUST_CLIENT_ID,
            "client_secret": getattr(settings, "LINKEDTRUST_CLIENT_SECRET", ""),
        })
        info = _get_json(f"{_issuer()}/oauth/userinfo",
                         headers={"Authorization": f"Bearer {tokens.get('access_token', '')}"})
    except (HTTPError, URLError, json.JSONDecodeError, ValueError) as exc:
        logger.error("LinkedTrust SSO failed: %s", exc)
        messages.error(request, "Could not complete LinkedTrust sign-in. Use your password for now.")
        return redirect(login_url)

    email = (info.get("email") or "").strip().lower()
    User = get_user_model()
    user = User.objects.filter(email__iexact=email, is_active=True).first() if email else None
    if not user:
        messages.error(request,
            "No account here matches that LinkedTrust email yet. Sign in with your password, "
            "or ask an admin to set your email, then LinkedTrust sign-in will work.")
        return redirect(login_url)
    login(request, user)
    if not _safe_next(request, next_url):
        next_url = "/console/"
    return redirect(next_url)
