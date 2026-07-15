from django.urls import path
from django.views.generic import RedirectView
from .views import *

urlpatterns = [
    # Homepage
    path('', home_view, name='home'),

    # Portfolio — deep-linkable project pages
    # Alias: the blog nav links to /portfolio/ — 301 it to the real /work/ page.
    path('portfolio/', RedirectView.as_view(url='/work/', permanent=True)),
    path('portfolio', RedirectView.as_view(url='/work/', permanent=True)),
    path('work/', work_list_view, name='work_list'),
    path('work/<slug:slug>/', work_detail_view, name='work_detail'),
    path('work/<slug:slug>/case-study/', case_study_view, name='case_study'),

    # Services — deep-linkable service pages
    path('services/', services_view, name='services'),
    path('services/startups/', services_startups_view, name='services_startups'),
    path('services/nonprofits/', services_nonprofits_view, name='services_nonprofits'),
    path('services/launch/', services_launch_view, name='services_launch'),
    path('services/<slug:slug>/', service_detail_view, name='service_detail'),

    # LinkedClaims ecosystem
    path('linkedclaims/', linkedclaims_view, name='linkedclaims'),

    # Earned Governance Accelerator landing page + commitment (invite) page
    path('earnedgov/', earnedgov_view, name='earnedgov'),
    path('earnedgov', RedirectView.as_view(url='/earnedgov/', permanent=True)),
    path('earnedgov/commit/', earnedgov_commit_view, name='earnedgov_commit'),
    path('earnedgov/opportunities/', earnedgov_opps_view, name='earnedgov_opps'),
    path('earnedgov/card/<int:claim_id>.png', earnedgov_card_view, name='earnedgov_card'),
    # Magic invite links minted by GovKit (the accelerator dashboard) —
    # personalized one-click commit, then SSO into the dashboard.
    path('earnedgov/i/<slug:code>/', earnedgov_invite_view, name='earnedgov_invite'),

    # Core pages
    path('about/', about_view, name='about'),
    path('team/', team_view, name='team'),
    path('contact/', contact_view, name='contact'),
    path('press/', press_view, name='press'),
    path('privacy/', privacy_view, name='privacy'),
    path('interns/', interns_view, name='interns'),

    # Legacy no-slash paths → 301 redirect to the canonical trailing-slash URL
    # (avoids duplicate content; the slash version is the canonical one).
    path('contact', RedirectView.as_view(url='/contact/', permanent=True)),
    path('press', RedirectView.as_view(url='/press/', permanent=True)),
    path('privacy', RedirectView.as_view(url='/privacy/', permanent=True)),
    path('services', RedirectView.as_view(url='/services/', permanent=True)),
    path('about', RedirectView.as_view(url='/about/', permanent=True)),
    path('interns', RedirectView.as_view(url='/interns/', permanent=True)),
    # getstarted has no trailing-slash route; it is canonical as-is.
    path('getstarted', getstarted_view, name='getstarted'),

    # API endpoints
    path('team/member/<int:member_id>/', team_member_detail_view, name='team_member_detail'),
    path('send-request-email/', send_request_email, name='send_request_email'),

    # TBD
    path('mission', empty_view, name='mission'),
]