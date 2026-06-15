"""Sitemap definitions for linkedtrust.us.

Served at /sitemap.xml (see linkedtrust/urls.py). Uses the request host for the
domain and forces https, so it works without django.contrib.sites / SITE_ID.
"""
from django.contrib.sitemaps import Sitemap
from django.shortcuts import render
from django.urls import reverse

from .models import PortfolioProject, ServicePackage


class StaticViewSitemap(Sitemap):
    """Top-level, hand-maintained pages (no model behind them)."""
    protocol = "https"
    changefreq = "monthly"

    # (url name, priority)
    PAGES = [
        ("home", 1.0),
        ("about", 0.8),
        ("work_list", 0.8),
        ("services", 0.8),
        ("services_startups", 0.6),
        ("services_nonprofits", 0.6),
        ("services_launch", 0.6),
        ("linkedclaims", 0.7),
        ("team", 0.6),
        ("contact", 0.7),
        ("press", 0.5),
        ("interns", 0.5),
        ("privacy", 0.3),
        ("getstarted", 0.6),
    ]

    def items(self):
        return self.PAGES

    def location(self, item):
        return reverse(item[0])

    def priority(self, item):
        return item[1]


class PortfolioSitemap(Sitemap):
    protocol = "https"
    changefreq = "monthly"
    priority = 0.7

    def items(self):
        return PortfolioProject.objects.all()

    def location(self, obj):
        return reverse("work_detail", args=[obj.slug])

    def lastmod(self, obj):
        return obj.updated_at


class ServiceSitemap(Sitemap):
    protocol = "https"
    changefreq = "monthly"
    priority = 0.7

    def items(self):
        return ServicePackage.objects.filter(is_active=True)

    def location(self, obj):
        return reverse("service_detail", args=[obj.slug])

    def lastmod(self, obj):
        return obj.updated_at


sitemaps = {
    "static": StaticViewSitemap,
    "portfolio": PortfolioSitemap,
    "services": ServiceSitemap,
}


def sitemap_index_view(request):
    """Custom sitemap index.

    Unlike Django's built-in index view, this lets us include an external
    sitemap (the Ghost blog) alongside our section sitemaps.
    """
    scheme = "https" if request.is_secure() else request.scheme
    root = f"{scheme}://{request.get_host()}"
    children = [
        root + "/sitemap-pages.xml",
        root + "/sitemap-work.xml",
        root + "/sitemap-services.xml",
        root + "/blog/sitemap.xml",
    ]
    return render(
        request,
        "sitemap_index_styled.xml",
        {"children": children},
        content_type="application/xml",
    )
