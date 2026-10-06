"""The new admin console: a staff-only dashboard that mirrors the classic Django
admin's reach with a modern surface, plus the bespoke contact-inquiry workspace.
Reads live data; the only writes are archive / mark-contacted / draft-generation,
which reuse the same logic as the tested admin actions. Never sends email."""
import json
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import (ContactInquiry, PortfolioProject, CaseStudy, Testimonial,
                     ServicePackage, TeamMember, EcosystemItem, EarnedgovCommitment,
                     LevelUpRegistration)
from . import outreach

SPAM = ("spam", "dupe", "test")
TYPE = {"lead": ("Lead", "green"), "jobseeker": ("Job seeker", "teal"),
        "other": ("Review", "gold"), "spam": ("Spam", "coral"),
        "dupe": ("Duplicate", "coral"), "test": ("Test", "coral"), "": ("Unreviewed", "gold")}


def _inbox_qs():
    # Real people: not archived, not classified as noise.
    return ContactInquiry.objects.exclude(archived=True).exclude(verdict__in=SPAM).order_by("-created_at")


def _row(inq):
    label, ck = TYPE.get(inq.verdict, ("Review", "gold"))
    return {"id": inq.id, "name": inq.name or "", "email": inq.email,
            "date": inq.created_at.strftime("%Y-%m-%d"),
            "msg": (inq.message or "").strip(), "type": label, "ck": ck,
            "contacted": inq.contacted, "has_draft": inq.verdict in ("lead", "other")}


MODEL_PATH = {"port": "portfolioproject", "case": "casestudy", "team": "teammember",
              "svc": "servicepackage", "test": "testimonial", "eco": "ecosystemitem",
              "lvl": "levelupregistration", "egov": "earnedgovcommitment"}
SECTION_MODEL = {"port": PortfolioProject, "case": CaseStudy, "team": TeamMember,
                 "svc": ServicePackage, "test": Testimonial, "eco": EcosystemItem,
                 "lvl": LevelUpRegistration, "egov": EarnedgovCommitment}


def _counts():
    return {"inq": ContactInquiry.objects.count()} | {
        k: M.objects.count() for k, M in SECTION_MODEL.items()}


def _section_items():
    """Read-only item lists so content sections browse inside the console.
    Editing a record still opens its classic-admin change page."""
    out = {}
    for key, Model in SECTION_MODEL.items():
        base = f"/admin/website/{MODEL_PATH[key]}/"
        out[key] = [{"id": o.id, "label": str(o)[:90], "url": f"{base}{o.id}/change/"}
                    for o in Model.objects.all()[:300]]
    return out


def console(request):
    # Auth handled here (not @staff_member_required) so anonymous visitors get the
    # console's own sign-in page with the LinkedTrust option, while the classic
    # admin login stays untouched. SSO is additive, never a replacement.
    from django.conf import settings
    lt = bool(getattr(settings, "LINKEDTRUST_CLIENT_ID", ""))
    if not request.user.is_authenticated:
        return render(request, "console/login.html", {"linkedtrust_enabled": lt})
    if not (request.user.is_staff and request.user.is_active):
        return render(request, "console/login.html", {"no_access": True, "linkedtrust_enabled": lt})
    c = _counts()
    inbox = [_row(i) for i in _inbox_qs()]
    leads = ContactInquiry.objects.filter(verdict="lead").count()
    filtered = ContactInquiry.objects.filter(archived=True).count() or \
        ContactInquiry.objects.filter(verdict__in=SPAM).count()
    leads_open = ContactInquiry.objects.filter(verdict="lead", contacted=False).count()
    spam_open = ContactInquiry.objects.filter(verdict__in=SPAM, archived=False).count()
    egov_pending = EarnedgovCommitment.objects.filter(status="pending").count()

    attention = []
    if leads_open:
        attention.append([f"{leads_open} lead{'s' if leads_open != 1 else ''} ready for outreach", "inq", "gold"])
    if spam_open:
        attention.append([f"{spam_open} spam and duplicates to archive", "inq", "coral"])
    if egov_pending:
        attention.append([f"{egov_pending} earned-governance item{'s' if egov_pending != 1 else ''} pending review", "egov", "gold"])
    if c["case"] < c["port"]:
        attention.append([f"Only {c['case']} case study across {c['port']} portfolio projects", "case", "teal"])
    if not attention:
        attention.append(["Nothing needs attention right now", "inq", "green"])

    total = ContactInquiry.objects.count()
    data = {
        "inbox": inbox,
        "recent": inbox[:5],
        "inq_stats": {"total": total, "real": len(inbox), "leads": leads,
                      "filtered": round(filtered / total * 100) if total else 0},
        "counts": {"inbox": len(inbox)},
        "sections": [
            ["inq", "Contact inquiries", c["inq"], "Inbox", "inq"],
            ["egov", "Earned governance", c["egov"], "Inbox", "egov"],
            ["port", "Portfolio", c["port"], "Content", "port"],
            ["case", "Case studies", c["case"], "Content", "case"],
            ["team", "Team", c["team"], "Content", "team"],
            ["svc", "Services", c["svc"], "Content", "svc"],
            ["test", "Testimonials", c["test"], "Content", "test"],
            ["eco", "Ecosystem", c["eco"], "Content", "eco"],
            ["lvl", "LevelUp registrations", c["lvl"], "Programs", "lvl"],
        ],
        "bars": [["Team", c["team"]], ["Portfolio", c["port"]], ["Ecosystem", c["eco"]],
                 ["Services", c["svc"]], ["LevelUp", c["lvl"]], ["Testimonials", c["test"]],
                 ["Case studies", c["case"]]],
        "attention": attention,
        # Classic-admin changelist URLs (per section) + the in-console item lists.
        "admin_urls": {"inq": "/admin/website/contactinquiry/",
                       **{k: f"/admin/website/{p}/" for k, p in MODEL_PATH.items()}},
        "section_items": _section_items(),
    }
    return render(request, "console/panel.html", {"data": data})


@staff_member_required
@require_POST
def console_draft(request, pk):
    inq = get_object_or_404(ContactInquiry, pk=pk)
    subject, body, resid, engine = outreach.draft_for(inq)
    cal = outreach._env("OUTREACH_CALENDAR", "")
    if cal:
        body = body.replace(outreach.CAL_TOKEN, cal)
    return JsonResponse({"subject": subject, "body": body, "engine": engine,
                         "bcc": outreach._env("OUTREACH_BCC", "gvelez17@gmail.com"),
                         "frm": outreach._env("OUTREACH_FROM", "amos@linkedtrust.us")})


@staff_member_required
def console_crm(request):
    """Read-only CRM leads composed from Odoo (not owned here). Degrades to a
    not-connected state when ODOO_* is unset or Odoo is unreachable."""
    from . import crm
    return JsonResponse({"configured": crm.configured(), "leads": crm.recent_leads(60)})


@staff_member_required
def console_taiga(request):
    """Read-only Taiga user stories composed in (not owned). Not-connected without
    TAIGA_* config; degrades to empty on any API/network failure."""
    from . import taiga
    return JsonResponse({"configured": taiga.configured(), "items": taiga.recent_items(40)})


@staff_member_required
@require_POST
def console_classify(request):
    """Classify the unreviewed, non-archived inquiries: rules archive the obvious
    spam; the model (if a key is set) splits the rest into lead/jobseeker/other.
    Anything still uncertain stays unreviewed for a human."""
    from . import classify
    archived = tagged = 0
    for inq in ContactInquiry.objects.filter(archived=False, verdict=""):
        if classify.spam_by_rules(inq.name, inq.message):
            ContactInquiry.objects.filter(pk=inq.pk).update(verdict="spam", archived=True)
            archived += 1
            continue
        v = classify.llm_verdict(inq)
        if not v:
            continue
        fields = {"verdict": v}
        if v in classify.SPAM:
            fields["archived"] = True
            archived += 1
        else:
            tagged += 1
        ContactInquiry.objects.filter(pk=inq.pk).update(**fields)
    return JsonResponse({"ok": True, "archived": archived, "tagged": tagged})


@staff_member_required
@require_POST
def console_action(request):
    try:
        payload = json.loads(request.body or "{}")
        action = payload["action"]
        ids = [int(i) for i in payload.get("ids", [])]
    except (ValueError, KeyError, TypeError):
        return HttpResponseBadRequest("bad request")
    qs = ContactInquiry.objects.filter(pk__in=ids)
    if action == "archive":
        n = qs.update(archived=True)
    elif action == "unarchive":
        n = qs.update(archived=False)
    elif action == "contacted":
        from . import linkedclaims
        who = request.user.get_username()
        now = timezone.now()
        n = 0
        for inq in qs:
            inq.contacted = True
            inq.contacted_at = now
            inq.contacted_by = who
            # Attestation as a LinkedClaim (no-op unless CONSOLE_PUBLISH_CLAIMS);
            # the Django flag is written regardless, so the console never depends on it.
            claim_id = linkedclaims.publish_contacted(inq, who)
            if claim_id:
                inq.contacted_claim_id = claim_id
            inq.save(update_fields=["contacted", "contacted_at", "contacted_by", "contacted_claim_id"])
            n += 1
    else:
        return HttpResponseBadRequest("unknown action")
    return JsonResponse({"ok": True, "updated": n})
