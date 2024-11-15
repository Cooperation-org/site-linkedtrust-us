from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .models import TeamMember

# Create your views here.

def home_view(request):
    context = {
        'show_banner': True
    }
    return render(request, 'index.html', context)

def about_view(request):
    return render(request, 'about.html')

def services_view(request):
    return render(request, 'services.html')

def getstarted_view(request):
    return render(request, 'getstarted.html')

def contact_view(request):
    return render(request, 'contact.html')

def press_view(request):
    return render(request, 'press.html')

def team_view(request):
    team_members = TeamMember.objects.all().order_by('created_at')
    print(f"Found {team_members.count()} team members")
    return render(request, 'team.html', {'team_members': team_members})


def team_member_detail_view(request, member_id):
    print(f"Fetching details for member ID: {member_id}")
    try:
        member = get_object_or_404(TeamMember, id=member_id)
        print(f"Found member: {member.name}")  
        data = {
            'name': member.name,
            'title': member.title,
            'description': member.description,
            'image_url': member.image.url if member.image else '',
            'hourly_rate': str(member.hourly_rate),
        }
        return JsonResponse(data)
    except Exception as e:
        print(f"Error fetching member: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


def empty_view(request):
    return render(request, 'empty.html')



# Add to your views.py
from django.core.mail import send_mail
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
import json

@csrf_protect
def send_request_email(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_email = data.get('email')
            member_name = data.get('memberName')
            member_title = data.get('memberTitle')
            
            # Compose email message
            subject = f"New Service Request for {member_name}"
            message = f"""
Dear LinkedTrust Team,

A new service request has been received:

Requested Team Member: {member_name}
Service Type: {member_title}
Requester's Email: {user_email}

Best regards,
LinkedTrust Automated System
            """
            
            # Send email
            send_mail(
                subject,
                message,
                'noreply@linkedtrust.us',  # From email
                ['amos@linkedtrust.us'],    # To email
                fail_silently=False,
            )
            
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)