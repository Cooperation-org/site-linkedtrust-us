# Console → ecosystem: plan

Golda's steer (Oct 6): the admin console should be **a view, not a silo**. Sign in through
LinkedTrust SSO, compose the other systems (Odoo CRM, Taiga, GovKit) rather than copying
their data, and express attestations (contacted, verdict, testimonials) as **LinkedClaims**,
not rows that live only in this Django DB. Reference model: `Cooperation-org/baobab`.

## What the ecosystem already provides (investigation, Oct 6)

- **IdP:** `https://live.linkedtrust.us` (OIDC). Endpoints: `/oauth/authorize`, `/oauth/token`,
  userinfo. Scopes `openid email profile trust`.
- **Django SSO package:** `Cooperation-org/django-linkedtrust-auth` (SPA/fragment flow) and,
  better for a server-rendered app, the **vendored session-based version in
  `govkit/apps/accounts/`** (`oidc.py`, `views.linkedtrust_start/callback`, a login page with
  LinkedTrust + Google buttons, logs the user into a Django session). This is the blueprint.
- **Baobab** (`Cooperation-org/baobab`): single sign-on at the top, configurable nav into
  everything, web components tied to their own backend, amebo as the cross-system agent.
  Existing systems join via `CONTRACT.md §12` (a layer over their API, not a data copy).
- **LinkedClaims** (`Cooperation-org/LinkedClaims`, `linked-claims-extractor`): vocabulary for
  third-party claims/attestations. `act` app stores "testimonials as LinkedClaims" — the pattern
  to copy. The site already embeds `<linked-badge>` from linkedtrust.us.
- **CRM/Taiga access:** Odoo via `ODOO_API_KEY` on vm200 (XML-RPC, used by outreach-command);
  Taiga at `taiga.linkedtrust.us`. `earnkit` stands the whole stack up with LinkedTrust SSO.

## Where our code lives

`Cooperation-org/site-linkedtrust-us`: `website/console_views.py`, `templates/console/panel.html`,
`website/classify.py`, `website/outreach.py`, `website/models.py` (ContactInquiry + verdict/
contacted/archived — the Django-owned state Golda flags).

## Phased plan (value first, each shippable, additive, never breaks the public site)

### Phase 1 — SSO (in progress)
Vendor govkit's session-based OIDC into this repo as a small `linkedtrust_auth` app: a
"Sign in with LinkedTrust" button on a login page that logs the user into a Django session,
then `staff_member_required` gates the console as now. **Additive: the existing /admin/ login
stays as a fallback, so no lockout** ([[feedback_replacing_login_locks_out_owner]]).
- Config from env: `LINKEDTRUST_URL`, `LINKEDTRUST_CLIENT_ID`, `LINKEDTRUST_CLIENT_SECRET`,
  `LINKEDTRUST_SCOPES`, redirect `https://linkedtrust.us/auth/linkedtrust/callback/`.
- The login button renders only when a client id is configured, so deploying the code before
  the client exists changes nothing visible.
- **External dependency:** register a confidential OIDC client at live.linkedtrust.us for that
  redirect_uri → client_id + secret (secret into prod `.env` / GitHub deploy secret). This is
  the one step that may need Golda; everything else ships without it.

### Phase 2 — Compose (view, not silo)
Pull the other systems into the console as read-only views and add a Baobab-style nav:
- Odoo CRM leads (XML-RPC, `ODOO_API_KEY`) alongside the site inquiries.
- Taiga tasks for the signed-in user.
- Join per Baobab `CONTRACT.md §12` (a layer over each API; no data copy).

### Phase 3 — Attestations as LinkedClaims
Write "contacted" / "verdict" / testimonials as LinkedClaims against linkedtrust.us instead of
Django booleans; the Django fields become a local cache/projection of those claims. Model on
`act`'s testimonials-as-LinkedClaims.

## Status
- Phase 1 code: building now on a branch, additive + tested, staged until the OIDC client exists.
- Phases 2–3: planned here; execute after Phase 1 lands.
