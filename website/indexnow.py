"""IndexNow instant-indexing support.

IndexNow lets us push new/changed URLs straight to Bing and Yandex (and any
other participating engine) instead of waiting for a crawl. This is important
for AEO: ChatGPT Search and Microsoft Copilot are grounded in the Bing index,
so getting fresh URLs into Bing quickly improves answer-engine coverage.

How it works:
  1. We publish a key verification file at https://<host>/<KEY>.txt that returns
     the key as plain text (see `key_file` + linkedtrust/urls.py).
  2. We POST a JSON body listing changed URLs to https://api.indexnow.org/indexnow.
     The engine fetches the key file to confirm we own the host, then accepts
     the submission.

Submission is explicit — there are no post_save signals. Run it via the
`indexnow_ping` management command.

Uses only the Python standard library (urllib) — no new pip dependencies.
"""
import json
import logging
import re
import urllib.request
import urllib.error

from django.conf import settings

logger = logging.getLogger(__name__)

INDEXNOW_ENDPOINT = "https://api.indexnow.org/indexnow"
DEFAULT_HOST = "linkedtrust.us"


# ---------------------------------------------------------------------------
# Key verification file — served at https://<host>/<KEY>.txt
# ---------------------------------------------------------------------------
def key_file(request):
    """Return the IndexNow key as plain text so engines can verify ownership."""
    from django.http import HttpResponse
    return HttpResponse(settings.INDEXNOW_KEY, content_type="text/plain")


# ---------------------------------------------------------------------------
# Build the list of canonical URLs to submit
# ---------------------------------------------------------------------------
def all_site_urls(host=DEFAULT_HOST):
    """Build a list of absolute canonical URLs by reusing the sitemap classes.

    Iterates every Sitemap registered in website.sitemaps.sitemaps, calling
    items()/location() exactly the way /sitemap.xml does. Robust to empty
    sitemaps and individual sitemap failures.
    """
    from website.sitemaps import sitemaps

    base = f"https://{host}"
    urls = []
    seen = set()

    for name, sitemap in sitemaps.items():
        # Sitemap entries may be classes or instances; normalise to instance.
        sm = sitemap() if isinstance(sitemap, type) else sitemap
        try:
            items = list(sm.items())
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("indexnow: failed to read sitemap %r: %s", name, exc)
            continue

        for item in items:
            try:
                location = sm.location(item)
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("indexnow: failed to locate item in %r: %s", name, exc)
                continue
            if not location:
                continue
            url = location if location.startswith("http") else base + location
            if url not in seen:
                seen.add(url)
                urls.append(url)

    return urls


# ---------------------------------------------------------------------------
# Blog (Ghost) URLs — collected from the blog's own sitemap
# ---------------------------------------------------------------------------
def sitemap_urls(sitemap_url, _seen=None):
    """Recursively collect <loc> URLs from a sitemap or sitemap index."""
    _seen = _seen if _seen is not None else set()
    if sitemap_url in _seen:
        return []
    _seen.add(sitemap_url)
    req = urllib.request.Request(
        sitemap_url, headers={"User-Agent": "linkedtrust-indexnow"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            xml = resp.read().decode("utf-8", "ignore")
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("indexnow: failed to fetch sitemap %s: %s", sitemap_url, exc)
        return []

    locs = re.findall(r"<loc>\s*(.*?)\s*</loc>", xml)
    urls = []
    if "<sitemapindex" in xml:
        for child in locs:
            urls.extend(sitemap_urls(child, _seen))
    else:
        urls.extend(locs)
    return urls


def blog_urls(host=DEFAULT_HOST):
    """Collect blog (Ghost) URLs from /blog/sitemap.xml, filtered to this host.

    The blog is a separate system, so its URLs aren't in our Django sitemaps;
    this fetches the blog's own sitemap. URLs share the host, so the IndexNow
    key is valid for them.
    """
    base = f"https://{host}"
    return [u for u in sitemap_urls(f"{base}/blog/sitemap.xml")
            if u.startswith(base)]


# ---------------------------------------------------------------------------
# Submit URLs to IndexNow
# ---------------------------------------------------------------------------
def submit_urls(urls, host=DEFAULT_HOST):
    """POST the given URLs to the IndexNow API.

    Returns the HTTP status code on success, or None on error. Errors are
    logged rather than raised so callers (e.g. the management command) can
    keep going. Uses only urllib from the standard library.
    """
    urls = [u for u in (urls or []) if u]
    if not urls:
        logger.info("indexnow: no URLs to submit")
        return None

    payload = {
        "host": host,
        "key": settings.INDEXNOW_KEY,
        "keyLocation": f"https://{host}/{settings.INDEXNOW_KEY}.txt",
        "urlList": urls,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        INDEXNOW_ENDPOINT,
        data=data,
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "Accept": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            status = resp.getcode()
            logger.info("indexnow: submitted %d URLs, HTTP %s", len(urls), status)
            return status
    except urllib.error.HTTPError as exc:
        # IndexNow uses status codes (e.g. 200, 202, 400, 403, 422, 429) to
        # signal outcome; an HTTPError still tells us what happened.
        logger.warning("indexnow: HTTP %s submitting %d URLs: %s",
                       exc.code, len(urls), exc.reason)
        return exc.code
    except urllib.error.URLError as exc:
        logger.error("indexnow: network error submitting URLs: %s", exc.reason)
        return None
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("indexnow: unexpected error submitting URLs: %s", exc)
        return None
