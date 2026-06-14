"""Sitemap definitions for linkedtrust.us.

Served at /sitemap.xml (see linkedtrust/urls.py). Uses the request host for the
domain and forces https, so it works without django.contrib.sites / SITE_ID.
"""
from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import PortfolioProject, ServicePackage, CaseStudy


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


class CaseStudySitemap(Sitemap):
    protocol = "https"
    changefreq = "yearly"
    priority = 0.6

    def items(self):
        return CaseStudy.objects.select_related("project").all()

    def location(self, obj):
        return reverse("case_study", args=[obj.project.slug])

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
    "case_studies": CaseStudySitemap,
    "services": ServiceSitemap,
}
