"""Agent- and crawler-facing endpoints served at the site root.

These are wired up in linkedtrust/urls.py (NOT website/urls.py) so they always
resolve at the true site root, regardless of FORCE_SCRIPT_NAME:

    /robots.txt
    /llms.txt
    /llms-full.txt
    /.well-known/api-catalog

Implements parts of the "is it agent ready?" checklist:
  - robots.txt with explicit AI-crawler rules + Content-Signal directives
  - llms.txt / llms-full.txt (llmstxt.org)
  - API catalog (RFC 9727, application/linkset+json)
"""
from django.http import HttpResponse, JsonResponse
from django.urls import reverse

from .models import PortfolioProject, ServicePackage, TeamMember, EcosystemItem


def _site_root(request):
    """https://host (no trailing slash, no SCRIPT_NAME)."""
    scheme = "https" if request.is_secure() else request.scheme
    return f"{scheme}://{request.get_host()}"


def _abs(request, name, *args):
    """Absolute URL for a named route."""
    return _site_root(request) + reverse(name, args=args)


# ---------------------------------------------------------------------------
# robots.txt
# ---------------------------------------------------------------------------
def robots_txt(request):
    root = _site_root(request)
    lines = [
        "# robots.txt for LinkedTrust",
        "# Crawl rules + AI content-usage signals (https://contentsignals.org/)",
        "",
        "User-agent: *",
        "Allow: /",
        "Disallow: /admin/",
        "Disallow: /send-request-email/",
        "Disallow: /team/member/",
        "",
        "# Content usage preferences for the default group above.",
        "# search = appear in search; ai-input = use as grounding/RAG; ai-train = train models.",
        "# Flip any value to 'no' to opt out of that use.",
        "Content-Signal: search=yes, ai-input=yes, ai-train=yes",
        "",
        "# --- AI crawlers (explicit, currently fully allowed) ---",
    ]
    ai_agents = [
        "GPTBot",          # OpenAI training
        "OAI-SearchBot",   # OpenAI search
        "ChatGPT-User",    # ChatGPT browsing
        "ClaudeBot",       # Anthropic
        "Claude-Web",      # Anthropic browsing
        "anthropic-ai",
        "Google-Extended", # Gemini / Vertex training
        "PerplexityBot",
        "Applebot-Extended",
        "CCBot",           # Common Crawl
        "Bytespider",
        "Meta-ExternalAgent",
    ]
    for agent in ai_agents:
        lines += [f"User-agent: {agent}", "Allow: /", ""]

    lines += [f"Sitemap: {root}/sitemap.xml", ""]
    return HttpResponse("\n".join(lines), content_type="text/plain; charset=utf-8")


def _oneline(text):
    """Collapse whitespace/newlines into a single line."""
    return " ".join((text or "").split())


_SUMMARY = (
    "LinkedTrust is a coop-style deep-tech studio that builds verified trust "
    "systems, civic-tech platforms, and AI-powered tools. We design, build, and "
    "run real software for organizations that care about doing things right — "
    "backed by publicly verifiable trust claims (LinkedClaims)."
)


# ---------------------------------------------------------------------------
# llms.txt — concise, link-first index (https://llmstxt.org/)
# Generated from the database so it always reflects live content.
# ---------------------------------------------------------------------------
def llms_txt(request):
    root = _site_root(request)
    L = [
        "# LinkedTrust", "",
        f"> {_SUMMARY}", "",
        "## Core pages", "",
        f"- [Home]({root}/): Services, featured work, and verified trust badges.",
        f"- [About]({root}/about/): Who we are, how the cooperative works, and our values.",
        f"- [Our Work]({root}/work/): Portfolio of client, open-source, and research projects.",
        f"- [Services]({root}/services/): What we build and roughly what it costs.",
        f"- [LinkedClaims Ecosystem]({root}/linkedclaims/): Apps, specs, and tools built on the standard.",
        f"- [Team]({root}/team/): The people you actually work with.",
        f"- [Contact]({root}/contact/): Get in touch / book a free 30-minute consultation.",
        "",
    ]

    services = ServicePackage.objects.filter(is_active=True)
    if services:
        L += ["## Services", ""]
        for s in services:
            L.append(f"- [{s.title}]({_abs(request, 'service_detail', s.slug)}): {_oneline(s.short_description)}")
        L.append("")

    projects = PortfolioProject.objects.all()
    if projects:
        L += ["## Work / Portfolio", ""]
        for p in projects:
            L.append(f"- [{p.title}]({_abs(request, 'work_detail', p.slug)}): {_oneline(p.short_description)}")
        L.append("")

    ecosystem = EcosystemItem.objects.all()
    if ecosystem:
        L += ["## LinkedClaims ecosystem", ""]
        for it in ecosystem:
            url = it.live_url or f"{root}/linkedclaims/"
            L.append(f"- [{it.name}]({url}): {_oneline(it.short_description)}")
        L.append("")

    team = TeamMember.objects.all().order_by("created_at")
    if team:
        L += ["## Team", "",
              f"The people you work with ([profiles]({root}/team/)):", ""]
        for m in team:
            L.append(f"- {m.name} — {m.title}")
        L.append("")

    L += ["## More", "",
          f"- [Press & Media]({root}/press/): Talks, podcasts, and articles.",
          f"- [Internships]({root}/interns/): Open internship program.",
          f"- [Privacy Policy]({root}/privacy/)", "",
          "## Optional", "",
          f"- [Full content (llms-full.txt)]({root}/llms-full.txt): Expanded descriptions of every project, service, and team member.",
          f"- [Sitemap]({root}/sitemap.xml): Machine-readable list of all canonical URLs.", ""]

    return HttpResponse("\n".join(L), content_type="text/markdown; charset=utf-8")


# ---------------------------------------------------------------------------
# llms-full.txt — expanded single-document version, generated from the DB.
# ---------------------------------------------------------------------------
def llms_full_txt(request):
    root = _site_root(request)
    L = [
        "# LinkedTrust — Full Reference", "",
        f"> {_SUMMARY}", "",
        "## What we do", "",
        "We design, build, and operate production software end-to-end: web "
        "platforms, APIs, data pipelines, AI/RAG integrations, and the "
        "infrastructure underneath them. We work as a cooperative — the people "
        "who do the work share in it — and we bias toward the real things: real "
        "projects, real impact, all verifiable.", "",
    ]

    # --- Services -----------------------------------------------------------
    services = ServicePackage.objects.filter(is_active=True)
    if services:
        L += [f"## Services ({root}/services/)", ""]
        for s in services:
            L.append(f"### {s.title} ({_abs(request, 'service_detail', s.slug)})")
            desc = _oneline(s.full_description) or _oneline(s.short_description)
            if desc:
                L.append(desc)
            if s.price_range:
                L.append(f"Pricing: {s.price_range}")
            examples = list(s.example_projects.all())
            if examples:
                L.append("Example projects: " + ", ".join(p.title for p in examples))
            L.append("")

    # --- Work / Portfolio ---------------------------------------------------
    projects = PortfolioProject.objects.all()
    if projects:
        L += [f"## Work / Portfolio ({root}/work/)", ""]
        for p in projects:
            L.append(f"### {p.title} ({_abs(request, 'work_detail', p.slug)})")
            meta = []
            if p.client_name:
                meta.append(f"Client: {p.client_name}")
            meta.append(f"Category: {p.get_category_display()}")
            L.append(" · ".join(meta))
            desc = _oneline(p.full_description) or _oneline(p.short_description)
            if desc:
                L.append(desc)
            tags = p.get_tech_list()
            if tags:
                L.append("Tech: " + ", ".join(tags))
            links = []
            if p.demo_url:
                links.append(f"[Live demo]({p.demo_url})")
            if p.repo_url:
                links.append(f"[Source]({p.repo_url})")
            if links:
                L.append("Links: " + " · ".join(links))
            case = getattr(p, "case_study", None)
            if case:
                L.append(f"Case study ({_abs(request, 'case_study', p.slug)}):")
                L.append(f"- Problem: {_oneline(case.problem_text)}")
                L.append(f"- Solution: {_oneline(case.solution_text)}")
                L.append(f"- Result: {_oneline(case.result_text)}")
                if case.metrics:
                    metrics = ", ".join(f"{k}: {v}" for k, v in case.metrics.items())
                    if metrics:
                        L.append(f"- Metrics: {metrics}")
            L.append("")

    # --- LinkedClaims ecosystem --------------------------------------------
    ecosystem = EcosystemItem.objects.all()
    if ecosystem:
        L += [f"## LinkedClaims Ecosystem ({root}/linkedclaims/)", "",
              "LinkedClaims is an open standard for portable, verifiable trust "
              "claims. The trust badges across this site are live LinkedClaims.", ""]
        for it in ecosystem:
            url = it.live_url or f"{root}/linkedclaims/"
            L.append(f"### {it.name} ({url})")
            L.append(f"Status: {it.get_status_display()}")
            if it.short_description:
                L.append(_oneline(it.short_description))
            L.append("")

    # --- Team ---------------------------------------------------------------
    team = TeamMember.objects.all().order_by("created_at")
    if team:
        L += [f"## Team ({root}/team/)", ""]
        for m in team:
            L.append(f"### {m.name} — {m.title}")
            if m.description:
                L.append(_oneline(m.description))
            L.append("")

    # --- Footer -------------------------------------------------------------
    L += [
        f"## Contact ({root}/contact/)", "",
        "Reach the team or book a free 30-minute consultation. The contact form "
        "routes directly to a human.", "",
        "## Trust & verification", "",
        "Testimonials and credentials on this site embed live LinkedTrust badges "
        "tied to claim IDs in the public trust graph, so they can be "
        "independently verified rather than taken on faith.", "",
        "## Machine-readable resources", "",
        f"- Sitemap: {root}/sitemap.xml",
        f"- Concise index: {root}/llms.txt",
        f"- API catalog: {root}/.well-known/api-catalog", "",
    ]

    return HttpResponse("\n".join(L), content_type="text/markdown; charset=utf-8")


# ---------------------------------------------------------------------------
# /.well-known/api-catalog (RFC 9727 — application/linkset+json, RFC 9264)
# ---------------------------------------------------------------------------
def api_catalog(request):
    root = _site_root(request)
    linkset = {
        "linkset": [
            {
                "anchor": f"{root}/team/member/",
                "service-doc": [
                    {"href": f"{root}/llms-full.txt", "title": "LinkedTrust site reference"}
                ],
                "describedby": [
                    {"href": f"{root}/llms.txt", "type": "text/markdown"}
                ],
                "status": [
                    {"href": f"{root}/", "title": "Site homepage"}
                ],
            }
        ]
    }
    return JsonResponse(linkset, content_type="application/linkset+json")
