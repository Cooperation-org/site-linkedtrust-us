"""URLconf for the accelerator's own host (workers.vc).

The Earned Governance Accelerator's whole public surface lives at the root of
workers.vc (board: domain rev 3): landing, wall, commit, opportunities, share
cards, and magic invite links. The rest of the linkedtrust.us site is NOT
served on this host — the brands stay separate. URL *names* match the main
urlconf, so views and templates reverse the right path on either host.

Selected per-request by website.middleware.HostRoutingMiddleware.
"""
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from website.views import (
    earnedgov_view,
    earnedgov_commit_view,
    earnedgov_opps_view,
    earnedgov_card_view,
    earnedgov_invite_view,
)

urlpatterns = [
    path('', earnedgov_view, name='earnedgov'),
    path('commit/', earnedgov_commit_view, name='earnedgov_commit'),
    path('opportunities/', earnedgov_opps_view, name='earnedgov_opps'),
    path('card/<int:claim_id>.png', earnedgov_card_view, name='earnedgov_card'),
    path('i/<slug:code>/', earnedgov_invite_view, name='earnedgov_invite'),
]

# Static/media are served by WhiteNoise middleware in production regardless of
# urlconf; these dev-only routes mirror the main urlconf's behavior.
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
