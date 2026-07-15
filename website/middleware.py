"""Custom middleware for LinkedTrust.

1. SecurityHeadersMiddleware
   Adds the response headers Django doesn't set natively (CSP, Permissions-Policy)
   plus RFC 8288 Link headers advertising agent resources. Native headers
   (HSTS, X-Content-Type-Options, Referrer-Policy, X-Frame-Options) are driven by
   settings via Django's SecurityMiddleware / XFrameOptionsMiddleware; we also
   stamp nosniff + frame-options here so static files (served by WhiteNoise) get
   them too. Placed near the top of MIDDLEWARE so it runs last on the response
   path and can decorate WhiteNoise/static responses.

2. MarkdownNegotiationMiddleware
   When an agent requests a page with `Accept: text/markdown`, returns a Markdown
   rendering of the page's <main> content. HTML stays the default for browsers.
"""
from html.parser import HTMLParser
import re

from django.utils.deprecation import MiddlewareMixin


# Content-Security-Policy. Permissive (keeps 'unsafe-inline' because the site
# uses inline gtag + inline styles/handlers) but scoped to the origins actually
# used. Tighten with nonces later if desired.
_CSP = "; ".join([
    "default-src 'self'",
    # cdn.tailwindcss.com: the earnedgov pages use the Tailwind play CDN
    # (swap for a built stylesheet when that design settles, then remove).
    "script-src 'self' 'unsafe-inline' https://www.googletagmanager.com "
    "https://www.google-analytics.com https://demos.linkedtrust.us "
    "https://cdn.tailwindcss.com "
    "https://www.clarity.ms https://*.clarity.ms",
    # Our own fonts are self-hosted; these origins are for the <linked-badge>
    # web component, which injects its own Google Fonts.
    # cdnjs.cloudflare.com: Font Awesome used by the earnedgov pages.
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com",
    "font-src 'self' data: https://fonts.gstatic.com https://cdnjs.cloudflare.com",
    "img-src 'self' data: https:",
    # <linked-badge> testimonial videos are served from Backblaze S3.
    "media-src 'self' https://*.backblazeb2.com https://*.linkedtrust.us",
    "connect-src 'self' https://www.google-analytics.com https://*.linkedtrust.us "
    "https://*.clarity.ms https://c.bing.com",
    "frame-src 'self' https://www.youtube.com https://docs.google.com https://www.google.com",
    "frame-ancestors 'self'",
    "base-uri 'self'",
    "form-action 'self'",
])

_PERMISSIONS_POLICY = "geolocation=(), microphone=(), camera=(), browsing-topics=()"

_LINK_HEADER = ", ".join([
    '</.well-known/api-catalog>; rel="api-catalog"',
    '</llms.txt>; rel="service-doc"; type="text/markdown"',
    '</sitemap.xml>; rel="sitemap"',
])


class HostRoutingMiddleware(MiddlewareMixin):
    """Serve the accelerator's own host (workers.vc) from this app.

    On an accelerator host, swap in the accelerator urlconf (landing at the
    root, matching URL names — see linkedtrust/urls_workersvc.py). Once
    WORKERSVC_LIVE is on, the old linkedtrust.us/earnedgov/* paths 301 to
    their workers.vc equivalents so every link already shared keeps working.
    Claims' effort URI is untouched by any of this — display domain moves,
    the semantic anchor doesn't.
    """

    def process_request(self, request):
        from django.conf import settings
        from django.http import HttpResponsePermanentRedirect

        host = request.get_host().split(':')[0].lower()
        if host in settings.ACCELERATOR_HOSTS:
            request.urlconf = 'linkedtrust.urls_workersvc'
            return None

        if settings.WORKERSVC_LIVE and request.path.startswith('/earnedgov'):
            rest = request.path[len('/earnedgov'):].lstrip('/')
            # /earnedgov/i/... etc. map 1:1 under the root; the landing maps to /.
            target = f"https://{settings.ACCELERATOR_HOSTS[0]}/{rest}"
            qs = request.META.get('QUERY_STRING')
            if qs:
                target = f"{target}?{qs}"
            return HttpResponsePermanentRedirect(target)
        return None


class SecurityHeadersMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        response.setdefault("Content-Security-Policy", _CSP)
        response.setdefault("Permissions-Policy", _PERMISSIONS_POLICY)
        # Belt-and-braces for static/WhiteNoise responses that bypass the
        # settings-driven headers.
        response.setdefault("X-Content-Type-Options", "nosniff")
        response.setdefault("X-Frame-Options", "SAMEORIGIN")

        # Keep static assets (CSS/JS) crawlable but out of the index.
        # Media (images) is intentionally left indexable for Google Images.
        if "/static/" in request.path:
            response.setdefault("X-Robots-Tag", "noindex")

        # Advertise agent resources on HTML pages (RFC 8288).
        ctype = response.get("Content-Type", "")
        if ctype.startswith("text/html"):
            existing = response.get("Link")
            response["Link"] = f"{existing}, {_LINK_HEADER}" if existing else _LINK_HEADER
        return response


# ---------------------------------------------------------------------------
# Markdown content negotiation
# ---------------------------------------------------------------------------
_SKIP_PREFIXES = ("/admin", "/static", "/media", "/.well-known")
_BLOCK_TAGS = {"p", "div", "section", "article", "header", "footer", "li",
               "tr", "br", "h1", "h2", "h3", "h4", "h5", "h6", "ul", "ol",
               "blockquote", "table"}
_DROP_TAGS = {"script", "style", "svg", "noscript", "nav", "footer", "form",
              "linked-badge", "iframe"}


class _MarkdownExtractor(HTMLParser):
    """Minimal, dependency-free HTML -> Markdown for page <main> content."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out = []
        self.skip_depth = 0
        self._href = None
        self._link_text = []
        self._in_link = False
        self._list_stack = []  # 'ul' | 'ol'
        self._ol_counter = []

    def handle_starttag(self, tag, attrs):
        if self.skip_depth:
            if tag in _DROP_TAGS:
                self.skip_depth += 1
            return
        if tag in _DROP_TAGS:
            self.skip_depth = 1
            return
        attrs = dict(attrs)
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.out.append("\n\n" + "#" * int(tag[1]) + " ")
        elif tag == "p":
            self.out.append("\n\n")
        elif tag == "br":
            self.out.append("  \n")
        elif tag == "blockquote":
            self.out.append("\n\n> ")
        elif tag in ("strong", "b"):
            self.out.append("**")
        elif tag in ("em", "i"):
            self.out.append("*")
        elif tag == "ul":
            self._list_stack.append("ul")
            self.out.append("\n")
        elif tag == "ol":
            self._list_stack.append("ol")
            self._ol_counter.append(0)
            self.out.append("\n")
        elif tag == "li":
            if self._list_stack and self._list_stack[-1] == "ol":
                self._ol_counter[-1] += 1
                self.out.append(f"\n{self._ol_counter[-1]}. ")
            else:
                self.out.append("\n- ")
        elif tag == "a":
            self._href = attrs.get("href")
            self._in_link = bool(self._href)
            self._link_text = []

    def handle_endtag(self, tag):
        if self.skip_depth:
            if tag in _DROP_TAGS:
                self.skip_depth -= 1
            return
        if tag in ("strong", "b"):
            self.out.append("**")
        elif tag in ("em", "i"):
            self.out.append("*")
        elif tag == "ul" and self._list_stack:
            self._list_stack.pop()
        elif tag == "ol" and self._list_stack:
            self._list_stack.pop()
            if self._ol_counter:
                self._ol_counter.pop()
        elif tag == "a" and self._in_link:
            text = "".join(self._link_text).strip()
            if text:
                self.out.append(f"[{text}]({self._href})")
            self._in_link = False
            self._href = None

    def handle_data(self, data):
        if self.skip_depth:
            return
        if self._in_link:
            self._link_text.append(data)
            return
        self.out.append(data)

    def get_markdown(self):
        text = "".join(self.out)
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip() + "\n"


def html_to_markdown(html):
    # Prefer the <main> region if present.
    m = re.search(r"<main\b[^>]*>(.*?)</main>", html, re.IGNORECASE | re.DOTALL)
    fragment = m.group(1) if m else html
    parser = _MarkdownExtractor()
    parser.feed(fragment)
    return parser.get_markdown()


def _wants_markdown(request):
    accept = request.META.get("HTTP_ACCEPT", "")
    return "text/markdown" in accept.lower()


class MarkdownNegotiationMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        if request.method != "GET" or response.status_code != 200:
            return response
        if not _wants_markdown(request):
            return response
        if request.path.startswith(_SKIP_PREFIXES):
            return response
        ctype = response.get("Content-Type", "")
        if not ctype.startswith("text/html"):
            return response
        if getattr(response, "streaming", False):
            return response
        try:
            html = response.content.decode(response.charset or "utf-8")
        except (UnicodeDecodeError, AttributeError):
            return response

        markdown = html_to_markdown(html)
        response.content = markdown.encode("utf-8")
        response["Content-Type"] = "text/markdown; charset=utf-8"
        response["Content-Length"] = str(len(response.content))
        existing_vary = response.get("Vary")
        response["Vary"] = f"{existing_vary}, Accept" if existing_vary else "Accept"
        return response
