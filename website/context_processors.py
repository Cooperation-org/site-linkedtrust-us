"""Template context processors for site-wide values."""
from django.conf import settings


def site_meta(request):
    """Expose site-wide verification/meta tokens to all templates."""
    return {
        "gsc_verification": getattr(settings, "GSC_VERIFICATION", ""),
    }
