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


def _counts():
    return {
        "inq": ContactInquiry.objects.count(),
        "egov": EarnedgovCommitment.objects.count(),
        "port": PortfolioProject.objects.count(),
        "case": CaseStudy.objects.count(),
        "team": TeamMember.objects.count(),
        "svc": ServicePackage.objects.count(),
        "test": Testimonial.objects.count(),
        "eco": EcosystemItem.objects.count(),
        "lvl": LevelUpRegistration.objects.count(),
    }


@staff_member_required
def console(request):
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
        # Classic-admin changelist URLs for the section tiles.
        "admin_urls": {
            "inq": "/admin/website/contactinquiry/", "egov": "/admin/website/earnedgovcommitment/",
            "port": "/admin/website/portfolioproject/", "case": "/admin/website/casestudy/",
            "team": "/admin/website/teammember/", "svc": "/admin/website/servicepackage/",
            "test": "/admin/website/testimonial/", "eco": "/admin/website/ecosystemitem/",
            "lvl": "/admin/website/levelupregistration/",
        },
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
        n = qs.update(contacted=True, contacted_at=timezone.now(),
                      contacted_by=request.user.get_username())
    else:
        return HttpResponseBadRequest("unknown action")
    return JsonResponse({"ok": True, "updated": n})
