from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.core.mail import EmailMessage
from django.views.decorators.csrf import csrf_protect
from django.conf import settings
from django.views.decorators.http import require_http_methods
from .models import TeamMember, PortfolioProject, CaseStudy, Testimonial, EcosystemItem, ServicePackage, ContactInquiry
from .forms import ContactForm
import json
import logging

# Configure logging
logger = logging.getLogger(__name__)

def home_view(request):
    """
    Render the home page: hero + trust badges + featured work + services + trusted by.
    """
    context = {
        'featured_projects': PortfolioProject.objects.filter(featured=True)[:4],
        'hero_badges': Testimonial.objects.filter(placement='hero', linked_claim_id__gt='')[:2],
        'homepage_badges': Testimonial.objects.filter(placement='homepage', linked_claim_id__gt=''),
        'featured_testimonials': Testimonial.objects.filter(featured=True)[:3],
        'services': ServicePackage.objects.filter(is_active=True)[:4],
        'show_banner': True,
    }
    return render(request, 'index.html', context)

def about_view(request):
    """
    Render the about page with team members inline.
    """
    context = {
        'team_members': TeamMember.objects.all().order_by('created_at'),
    }
    return render(request, 'about.html', context)

def services_view(request):
    """
    Render the services overview page with all active service packages.
    """
    context = {
        'services': ServicePackage.objects.filter(is_active=True),
    }
    return render(request, 'services.html', context)

def getstarted_view(request):
    """
    Render the get started page.
    """
    return render(request, 'getstarted.html')

@csrf_protect
def contact_view(request):
    """
    Render the contact page and handle form submissions.
    """
    success = False
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            inquiry = form.save()
            # Send notification email
            try:
                subject = f"New Contact: {inquiry.get_subject_display()} — {inquiry.name or inquiry.email}"
                body = (
                    f"Name: {inquiry.name or '(not provided)'}\n"
                    f"Email: {inquiry.email}\n"
                    f"Subject: {inquiry.get_subject_display()}\n\n"
                    f"Message:\n{inquiry.message or '(no message)'}\n"
                )
                EmailMessage(
                    subject=subject,
                    body=body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=['connect@linkedtrust.us'],
                    reply_to=[inquiry.email],
                ).send(fail_silently=True)
            except Exception as e:
                logger.error(f"Contact email failed: {e}")
            success = True
            form = ContactForm()  # reset form after success
    else:
        form = ContactForm()
    return render(request, 'contact.html', {'form': form, 'success': success})

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

def interns_view(request):
    """
    Render the internships page.
    """
    return render(request, 'interns.html')


def linkedclaims_view(request):
    """LinkedClaims ecosystem page — cards for every app/spec/tool built on the standard."""
    context = {
        'ecosystem_items': EcosystemItem.objects.all(),
    }
    return render(request, 'linkedclaims.html', context)


# --- New portfolio & service views ---

def work_list_view(request):
    """Portfolio grid — all projects, optionally filtered by category."""
    category = request.GET.get('category')
    projects = PortfolioProject.objects.all()
    if category:
        projects = projects.filter(category=category)
    context = {
        'projects': projects,
        'categories': PortfolioProject.CATEGORY_CHOICES,
        'active_category': category,
    }
    return render(request, 'work_list.html', context)


def work_detail_view(request, slug):
    """Individual project detail page — the deep link you hand to a prospect."""
    project = get_object_or_404(PortfolioProject, slug=slug)
    context = {
        'project': project,
        'testimonials': project.testimonials.all(),
        'case_study': getattr(project, 'case_study', None),
    }
    return render(request, 'work_detail.html', context)


def case_study_view(request, slug):
    """Case study for a project — Problem → Solution → Result."""
    project = get_object_or_404(PortfolioProject, slug=slug)
    case_study = get_object_or_404(CaseStudy, project=project)
    context = {
        'project': project,
        'case_study': case_study,
    }
    return render(request, 'case_study.html', context)


def service_detail_view(request, slug):
    """Individual service detail page — deep link for a specific offering."""
    service = get_object_or_404(ServicePackage, slug=slug, is_active=True)
    context = {
        'service': service,
        'example_projects': service.example_projects.all(),
    }
    return render(request, 'service_detail.html', context)