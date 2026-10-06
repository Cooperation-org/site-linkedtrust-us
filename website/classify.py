"""Contact-inquiry spam detection. Pure functions, no Django imports, so the
post_save signal and the console button share one source of truth.

spam_by_rules is deliberately CONSERVATIVE: it only returns True when a message
is clearly junk (links, known pitches, gibberish, the repeated price probes).
It never guesses that something is a lead, so it can run on form submit without
ever archiving a real person. The LLM tier (llm_verdict) is optional and only
splits the uncertain remainder when a model key is configured.
"""
import os
import re

SPAM = ("spam", "dupe", "test")

_URL = re.compile(r"https?://|www\.|t\.me/|telegra\.ph|bit\.ly|sho\.cat|xrum|directoryinspector|\.ru\b", re.I)
_KW = re.compile(
    r"\b(seo|backlink|back link|link building|guest post|rank (?:higher|on google)|"
    r"slot games?|casino|rolls[- ]?royce|web archives?|wayback|crypto|bitcoin|forex|"
    r"viagra|cialis|make money|paid ads|lead lists?|outreach software|cold email|"
    r"mass mail(?:er)?|limited[- ]?time (?:loan|offer))\b", re.I)
_PRICE = re.compile(r"\b(price|prix|precio|preis|pr[aä]is|prezzo|cijen[au])\b", re.I)
_NONLATIN = re.compile(r"[Ͱ-ϿЀ-ӿ԰-֏֐-׿؀-ۿႠ-ჿ一-鿿]")
_PROBE = re.compile(r"contact me by email\W+contact linkedtrust", re.I)


def _gibberish(s):
    s = (s or "").strip()
    if len(s) < 10 or " " in s:
        return False
    letters = [c for c in s if c.isalpha()]
    if not letters:
        return False
    vowel_ratio = sum(c.lower() in "aeiou" for c in letters) / len(letters)
    uppers = sum(c.isupper() for c in s)
    has_digit = any(c.isdigit() for c in s)
    return vowel_ratio < 0.18 or (has_digit and uppers >= 6)


def spam_by_rules(name, message):
    """True only for high-confidence junk. Never True for a plausible real person."""
    name = name or ""
    message = message or ""
    blob = name + "\n" + message
    if _URL.search(blob):
        return True
    if _KW.search(blob):
        return True
    if _PROBE.search(message):
        return True
    if _gibberish(name) or _gibberish(message):
        return True
    short = len(message.strip()) <= 90
    if short and (_PRICE.search(message) or _NONLATIN.search(message)):
        return True
    return False


def llm_verdict(inq):
    """Split an uncertain inquiry into lead / jobseeker / other / spam using the
    configured model. Returns a verdict string, or None when no key is set or the
    call fails (caller then leaves it unreviewed for a human)."""
    if not os.environ.get("MINIMAX_API_KEY"):
        return None
    from . import outreach
    prompt = (
        "Classify this website contact-form submission for LinkedTrust, a software "
        "and AI consultancy. Reply with ONE word only: lead (a potential client or "
        "customer), jobseeker (someone wanting a job or internship), spam (pitch, "
        "promotion, scam, bot), or other (real person, unclear intent). "
        f"\n\nName: {inq.name}\nEmail: {inq.email}\nMessage: {(inq.message or '')[:600]}\n\nOne word:")
    try:
        out = outreach._minimax(prompt, max_tokens=8).strip().lower()
    except Exception:
        return None
    for v in ("jobseeker", "lead", "spam", "other"):
        if v in out:
            return v
    return None
