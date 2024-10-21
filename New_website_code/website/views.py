from django.shortcuts import render

# Create your views here.
def home_view(request):
    return render(request, 'index.html')

def team_view(request):
    return render(request, 'team.html')

def services_view(request):
    return render(request, 'services.html')

def getstarted_view(request):
    return render(request, 'getstarted.html')

# 