"""Outreach draft generation for contact inquiries.

The admin action "Generate outreach drafts" calls build_drafts_html(rows) and
hands the operator a downloadable HTML page of ready-to-copy replies. It NEVER
sends. A model (MiniMax, Anthropic-compatible endpoint) writes each draft; a
deterministic scrub then removes em dashes and AI-tell vocabulary, so the house
style holds no matter which model wrote it. With no API key configured it falls
back to a plain template, so the button always returns something.

Server config (put in .env, never in the repo):
    MINIMAX_API_KEY=...
    MINIMAX_ANTHROPIC_BASE_URL=https://api.minimax.io/anthropic
    MINIMAX_MODEL=MiniMax-M3
    OUTREACH_FROM=amos@linkedtrust.us
    OUTREACH_BCC=gvelez17@gmail.com
    OUTREACH_CALENDAR=https://your-scheduling-link
"""
import os, re, json, time, html, statistics, urllib.request

CAL_TOKEN = "SCHEDULE_LINK"

BANNED = ["i hope this email finds you well", "i hope this finds you well", "delve",
    "leverage", "synergy", "seamless", "excited to", "thrilled", "passionate about",
    "in today's fast-paced", "navigate the landscape", "game-changer", "cutting-edge",
    "at the intersection of", "resonate", "moreover", "furthermore", "additionally,",
    "it's worth noting", "needless to say", "as an ai"]


def _env(k, default=""):
    return os.environ.get(k, default)


def scrub(t):
    t = t.replace("—", ", ").replace("–", ", ")
    t = re.sub(r"\s+--\s+", ", ", t)
    t = t.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    t = re.sub(r"\s*,\s*,\s*", ", ", t)
    t = t.replace("!", ".")
    t = re.sub(r"[ \t]{2,}", " ", t)
    return t.strip()


def check(subject, body, contact_email):
    fails = []
    low = body.lower()
    for b in BANNED:
        if b in low:
            fails.append(f'banned phrase "{b}"')
    if contact_email and contact_email.lower() in low:
        fails.append("contact's email leaked into body")
    if "—" in body or "–" in body:
        fails.append("em/en dash present")
    w = len(body.split())
    if not 70 <= w <= 175:
        fails.append(f"word count {w}, need 70-175")
    if "!" in subject + body:
        fails.append("exclamation mark present")
    if CAL_TOKEN not in body:
        fails.append(f"missing {CAL_TOKEN} placeholder")
    if not re.search(r"\b(i've|i'm|you're|it's|don't|can't|there's|that's|i'd|we're|what's|we'll|you'll|we'd)\b", low):
        fails.append("no contractions, reads stiff")
    return fails


def _minimax(prompt, max_tokens=900):
    key = _env("MINIMAX_API_KEY")
    base = _env("MINIMAX_ANTHROPIC_BASE_URL", "https://api.minimax.io/anthropic").rstrip("/")
    model = _env("MINIMAX_MODEL", "MiniMax-M3")
    if not key:
        raise RuntimeError("no MINIMAX_API_KEY")
    body = json.dumps({"model": model, "max_tokens": max_tokens,
                       "messages": [{"role": "user", "content": prompt}]}).encode()
    req = urllib.request.Request(base + "/v1/messages", data=body, headers={
        "x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"})
    last = None
    for a in range(3):
        try:
            r = urllib.request.urlopen(req, timeout=90)
            d = json.loads(r.read())
            return " ".join(p.get("text", "") for p in d.get("content", []) if p.get("type") == "text").strip()
        except Exception as e:
            last = e
            time.sleep(1.5 * (a + 1))
    raise last


_STYLE = (
    "You are drafting a reply email FROM Amos at LinkedTrust (a software and AI consultancy) "
    "TO a person who submitted the site contact form. Write ONLY the email body, plain prose.\n"
    "Rules: warm, direct, human, 80 to 150 words, use contractions. Open by referencing "
    "specifically what they wrote. Ask what they're trying to achieve and what they need. "
    f"Offer a short call and include the exact token {CAL_TOKEN} where the scheduling link goes. "
    "Do not invent facts, prices, timelines, or promises. No em dashes, no exclamation marks, "
    "no bullet lists, no AI cliches. Sign off simply as: Amos, LinkedTrust. "
    "Do not include the recipient's email address in the body."
)


def _template(row):
    name = (row.name or "").strip() or "there"
    return (f"Hi {name},\n\n"
            f"Thanks for reaching out to LinkedTrust about your {row.get_subject_display().lower()} note. "
            "I'd like to help, and I want to make sure we point you at the right thing.\n\n"
            "Could you tell me a bit more about what you're trying to achieve and what you need from us? "
            "That way we don't waste your time on the wrong angle.\n\n"
            f"If it's easier to talk it through, grab a time that works for you here: {CAL_TOKEN}\n\n"
            "Amos, LinkedTrust")


def draft_for(row):
    """Return (subject, body, residual_fails, engine)."""
    subject = "Following up on your note to LinkedTrust"
    try:
        prompt = (f"{_STYLE}\n\nThe person's name: {row.name or 'there'}\n"
                  f"What they submitted (subject '{row.subject}'):\n\"\"\"\n{(row.message or '')[:800]}\n\"\"\"\n\n"
                  "Write the email body now.")
        body = scrub(_minimax(prompt))
        for _ in range(2):
            fails = check(subject, body, row.email)
            if not fails:
                break
            fix = (f"{_STYLE}\n\nRewrite this draft. It failed these checks: {'; '.join(fails)}. "
                   f"Keep the intent, fix every issue. Person's name: {row.name or 'there'}.\n\n"
                   f"Current draft:\n{body}\n\nReturn only the corrected body.")
            body = scrub(_minimax(fix))
        return subject, body, check(subject, body, row.email), "minimax"
    except Exception:
        body = scrub(_template(row))
        return subject, body, check(subject, body, row.email), "template"


def build_drafts_html(rows):
    frm = _env("OUTREACH_FROM", "amos@linkedtrust.us")
    bcc = _env("OUTREACH_BCC", "gvelez17@gmail.com")
    cal = _env("OUTREACH_CALENDAR", "")
    cards = []
    for row in rows:
        subject, body, resid, engine = draft_for(row)
        shown = body.replace(CAL_TOKEN, cal) if cal else body
        full = f"To: {row.email}\nBcc: {bcc}\nSubject: {subject}\n\n{shown}"
        resid_html = (f"<div class='resid'>check flags: {html.escape('; '.join(resid))}</div>") if resid else ""
        cards.append(f"""
    <article class="card">
      <header><span class="meta">#{row.id} · {html.escape(row.name or 'no name')} · {row.subject} · via {engine}</span></header>
      <div class="orig"><b>They wrote:</b> {html.escape((row.message or '')[:400])}</div>
      <div class="lines"><span><b>To</b> {html.escape(row.email)}</span><span><b>Bcc</b> {html.escape(bcc)}</span><span><b>Subject</b> {html.escape(subject)}</span></div>
      <pre class="body" id="b{row.id}">{html.escape(shown)}</pre>{resid_html}
      <button class="copy" data-t="b{row.id}">Copy body</button>
      <button class="copy2" data-full="{html.escape(full)}">Copy full</button>
    </article>""")
    warn = "" if cal else (f"<div class='note'>Set OUTREACH_CALENDAR in .env, or replace <code>{CAL_TOKEN}</code> "
                           "with your scheduling link before sending.</div>")
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>LinkedTrust outreach drafts</title>
<style>
:root{{--bg:#f7f7f5;--card:#fff;--ink:#1a1a1a;--mut:#666;--line:#e5e5e2}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 -apple-system,Segoe UI,Roboto,Arial,sans-serif;padding:24px 16px}}
.wrap{{max-width:820px;margin:0 auto}}h1{{font-size:22px;margin:0 0 4px}}.sub{{color:var(--mut);margin:0 0 8px}}
.note{{background:#fff8e1;border:1px solid #f0e0a0;padding:10px 12px;border-radius:8px;margin:12px 0;font-size:13.5px}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px;margin:14px 0}}
.meta{{color:var(--mut);font-size:12.5px}}
.orig{{font-size:13px;color:#444;background:#fafafa;border-left:3px solid var(--line);padding:8px 10px;border-radius:4px;margin:8px 0}}
.lines{{display:flex;flex-direction:column;gap:2px;font-size:13px;margin-bottom:8px}}.lines b{{color:var(--mut);min-width:52px;display:inline-block}}
pre.body{{white-space:pre-wrap;font:14px/1.55 ui-monospace,Menlo,Consolas,monospace;background:#fbfbfa;border:1px solid var(--line);border-radius:8px;padding:12px;margin:0 0 10px}}
.resid{{color:#8a6d00;font-size:12.5px;margin-bottom:8px}}
button{{font:600 13px inherit;border:1px solid var(--line);background:#fff;padding:8px 12px;border-radius:8px;cursor:pointer;margin-right:8px}}button:hover{{background:#f0f0ee}}button.ok{{background:#137333;color:#fff}}
</style></head><body><div class="wrap">
<h1>LinkedTrust outreach drafts</h1><p class="sub">{len(rows)} replies from {html.escape(frm)}, bcc {html.escape(bcc)}. Draft only, review then send yourself.</p>
{warn}{''.join(cards)}</div>
<script>
document.querySelectorAll('.copy').forEach(b=>b.onclick=()=>{{navigator.clipboard.writeText(document.getElementById(b.dataset.t).innerText).then(()=>{{b.textContent='Copied';b.classList.add('ok');setTimeout(()=>{{b.textContent='Copy body';b.classList.remove('ok')}},1200)}})}});
document.querySelectorAll('.copy2').forEach(b=>b.onclick=()=>{{navigator.clipboard.writeText(b.dataset.full).then(()=>{{b.textContent='Copied';b.classList.add('ok');setTimeout(()=>{{b.textContent='Copy full';b.classList.remove('ok')}},1200)}})}});
</script></body></html>"""
