from django.shortcuts import render

# Create your views here.

def home_view(request):
    context = {
        'show_banner': True
    }
    return render(request, 'index.html', context)

def team_view(request):
    context = {
        'show_banner': False
    }
    return render(request, 'team.html', context)
def services_view(request):
    return render(request, 'services.html')

def getstarted_view(request):
    return render(request, 'getstarted.html')

def contact_view(request):
    return render(request, 'contact.html')

def press_view(request):
    return render(request, 'press.html')

def empty_view(request):
    return render(request, 'empty.html')
