from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.core.mail import EmailMessage
from django.views.decorators.csrf import csrf_protect
from django.conf import settings
from django.views.decorators.http import require_http_methods
from .models import TeamMember
import json
import logging

# Configure logging
logger = logging.getLogger(__name__)

def home_view(request):
    """
    Render the home page with banner.
    """
    return render(request, 'index.html', {'show_banner': True})

def about_view(request):
    """
    Render the about page.
    """
    return render(request, 'about.html')

def services_view(request):
    """
    Render the services page.
    """
    return render(request, 'services.html')

def getstarted_view(request):
    """
    Render the get started page.
    """
    return render(request, 'getstarted.html')

def contact_view(request):
    """
    Render the contact page.
    """
    return render(request, 'contact.html')

def press_view(request):
    """
    Render the press page.
    """
    return render(request, 'press.html')

def privacy_view(request):
    """
    Render the privacy policy page.
    """
    return render(request, 'privacy.html')

def team_view(request):
    """
    Render the team page with all team members.
    """
    try:
        team_members = TeamMember.objects.all().order_by('created_at')
        logger.info(f"Retrieved {team_members.count()} team members")
        return render(request, 'team.html', {'team_members': team_members})
    except Exception as e:
        logger.error(f"Error retrieving team members: {str(e)}")
        return render(request, 'team.html', {'team_members': [], 'error': 'Unable to load team members'})

@require_http_methods(["GET"])
def team_member_detail_view(request, member_id):
    """
    API endpoint to get detailed information about a specific team member.
    """
    try:
        logger.info(f"Fetching details for member ID: {member_id}")
        member = get_object_or_404(TeamMember, id=member_id)
        
        data = {
            'name': member.name,
            'title': member.title,
            'description': member.description,
            'image_url': member.image.url if member.image else '',
            'hourly_rate': str(member.hourly_rate),
        }
        logger.info(f"Successfully retrieved details for member: {member.name}")
        return JsonResponse(data)
    
    except TeamMember.DoesNotExist:
        logger.warning(f"Team member not found with ID: {member_id}")
        return JsonResponse({
            'error': 'Team member not found'
        }, status=404)
    
    except Exception as e:
        logger.error(f"Error fetching team member {member_id}: {str(e)}")
        return JsonResponse({
            'error': 'Internal server error'
        }, status=500)

@csrf_protect
@require_http_methods(["POST"])
def send_request_email(request):
    """
    Handle service request emails from team member profiles.
    """
    try:
        # Parse request data
        data = json.loads(request.body)
        user_email = data.get('email')
        member_name = data.get('memberName')
        member_title = data.get('memberTitle')
        member_id = data.get('memberId')

        # Validate required fields
        if not all([user_email, member_name, member_title, member_id]):
            return JsonResponse({
                'status': 'error',
                'message': 'Missing required fields'
            }, status=400)

        # Verify team member exists
        member = get_object_or_404(TeamMember, id=member_id)

        # Prepare email content
        subject = f"New Service Request for {member_name}"
        message = f"""
        Dear LinkedTrust Team,

        A new service request has been received:

        Requested Team Member: {member_name}
        Service Type: {member_title}
        Requester's Email: {user_email}
        Team Member ID: {member_id}

        Best regards,
        LinkedTrust Automated System
                """

        # Create and send email
        email = EmailMessage(
            subject=subject,
            body=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=['amos@linkedtrust.us'],
            reply_to=[user_email]
        )
        
        email.send(fail_silently=False)
        
        # Log success
        logger.info(f"Service request email sent successfully for {member_name} from {user_email}")
        
        return JsonResponse({
            'status': 'success',
            'message': 'Request sent successfully'
        })

    except TeamMember.DoesNotExist:
        logger.warning(f"Service request failed - Team member not found with ID: {member_id}")
        return JsonResponse({
            'status': 'error',
            'message': 'Team member not found'
        }, status=404)
        
    except json.JSONDecodeError:
        logger.error("Invalid JSON in request body")
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid request format'
        }, status=400)
        
    except Exception as e:
        logger.error(f"Error sending service request email: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': 'Failed to send request. Please try again later.'
        }, status=500)

def empty_view(request):
    """
    Render the empty template page.
    """
    return render(request, 'empty.html')