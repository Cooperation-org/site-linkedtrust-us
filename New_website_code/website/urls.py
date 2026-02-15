from django.urls import path
from .views import *

urlpatterns = [
    # Homepage
    path('', home_view, name='home'),

    # Portfolio — deep-linkable project pages
    path('work/', work_list_view, name='work_list'),
    path('work/<slug:slug>/', work_detail_view, name='work_detail'),
    path('work/<slug:slug>/case-study/', case_study_view, name='case_study'),

    # Services — deep-linkable service pages
    path('services/', services_view, name='services'),
    path('services/<slug:slug>/', service_detail_view, name='service_detail'),

    # Core pages
    path('about/', about_view, name='about'),
    path('team/', team_view, name='team'),
    path('contact/', contact_view, name='contact'),
    path('press/', press_view, name='press'),
    path('privacy/', privacy_view, name='privacy'),
    path('interns/', interns_view, name='interns'),

    # Keep old paths working (redirects not needed — Django handles trailing slash)
    path('contact', contact_view),
    path('getstarted', getstarted_view, name='getstarted'),
    path('press', press_view),
    path('privacy', privacy_view),
    path('services', services_view),
    path('about', about_view),
    path('interns', interns_view),

    # API endpoints
    path('team/member/<int:member_id>/', team_member_detail_view, name='team_member_detail'),
    path('send-request-email/', send_request_email, name='send_request_email'),

    # TBD
    path('mission', empty_view, name='mission'),
]