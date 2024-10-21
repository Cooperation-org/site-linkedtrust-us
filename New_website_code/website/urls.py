from django.urls import path
from .views import *

urlpatterns = [
    path('', home_view, name='home'),
    path('team', team_view, name='team'),
    path('services', services_view, name='services'),
    path('getstarted', getstarted_view, name='getstarted'),
]
