from django.urls import path
from .views import *

urlpatterns = [
    path('', home_view, name='home'),
    path('about', about_view, name='about'),
    path('services', services_view, name='services'),
    path('page4', page4_view, name='page4'),
    path('getstarted', getstarted_view, name='getstarted'),
]

# 