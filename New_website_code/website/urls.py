from django.urls import path
from .views import *

urlpatterns = [
    path('', home_view, name='home'),
    path('contact', contact_view, name='contact'),
    path('getstarted', getstarted_view, name='getstarted'),
    path('press', press_view, name='press'),
    path('services', services_view, name='services'),
    path('team', team_view, name='team'),
    path('about', about_view, name='about'),

    # TBD views
    path('mission', empty_view, name='mission'),
]
