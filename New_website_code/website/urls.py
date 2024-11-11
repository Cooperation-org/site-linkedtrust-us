from django.urls import path
from .views import *

urlpatterns = [
    path('', home_view, name='home'),
    path('team', team_view, name='team'),
    path('services', services_view, name='services'),
    path('getstarted', getstarted_view, name='getstarted'),
    path('contact', contact_view, name='contact'),


    # TBD views
    path('mission', empty_view, name='mission'),
    path('press', empty_view, name='press'),
]