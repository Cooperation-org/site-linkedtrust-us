from django.shortcuts import render

# Create your views here.
def home_view(request):
    return render(request, 'index.html')

def about_view(request):
    return render(request, 'about.html')

def services_view(request):
    return render(request, 'services.html')

def page4_view(request):
    return render(request, 'page4.html')

def getstarted_view(request):
    return render(request, 'getstarted.html')

# 