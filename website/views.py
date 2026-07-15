from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.utils.text import slugify
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
        initial = {}
        subject = request.GET.get('subject')
        if subject:
            initial['subject'] = subject
        form = ContactForm(initial=initial)
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

def earnedgov_view(request):
    """
    Render the Earned Governance Accelerator landing page.
    Self-contained page (own styles); assets under static/img/earnedgov/.
    The commitment wall is live LinkedTrust claims (see earnedgov_claims.py).
    """
    from . import earnedgov_claims
    from .models import EarnedgovCommitment
    committed_id = request.GET.get('committed')
    share = None
    if committed_id and committed_id.isdigit():
        share = earnedgov_claims.fetch_claim(committed_id, verbs=earnedgov_claims.WALL_VERBS)

    # Moderation: claims with a ledger row that is not approved stay off the
    # wall (walk-ups pending review, or explicitly hidden). No row = visible
    # (grandfathered pre-moderation claims).
    wall = earnedgov_claims.fetch_commitments()
    blocked = set(
        EarnedgovCommitment.objects.exclude(status='approved')
        .values_list('claim_id', flat=True)
    )
    if blocked and wall.get('groups'):
        groups = []
        for g in wall['groups']:
            members = [m for m in g['members'] if m['id'] not in blocked]
            if members:
                groups.append({**g, 'members': members})
        wall = {**wall, 'groups': groups}

    context = {
        'wall': wall,
        'committed_id': committed_id,
        'share': share,
        # "<Name> joined … as a mentor" — never "committed as" (language pin).
        'share_phrase': earnedgov_claims.ROLE_PHRASES.get(
            (share or {}).get('role'), 'is in the Earned Governance Accelerator'),
        # Absolute URLs built from the request so they follow the serving host
        # (linkedtrust.us/earnedgov today, workers.vc root when DNS lands).
        'card_url': request.build_absolute_uri(
            reverse('earnedgov_card', kwargs={'claim_id': share['id']})) if share else '',
        'share_link': request.build_absolute_uri(
            f"{reverse('earnedgov')}?committed={committed_id}") if committed_id else '',
        'lt_api': earnedgov_claims.LT_API,
        'dashboard_url': getattr(settings, 'EARNEDGOV_DASHBOARD_URL', ''),
        'pending': request.GET.get('pending'),
    }
    return render(request, 'earnedgov.html', context)


@csrf_protect
def earnedgov_commit_view(request):
    """
    The commitment / invitation page: someone joins the accelerator effort
    by making (or vouching for) a COMMITS_TO claim on LinkedTrust.
    ?upgrade=<claim_id> prefills from an existing second-hand claim so the
    person can replace it with their own self-attested (step-up) version.
    """
    from . import earnedgov_claims
    from .models import EarnedgovCommitment

    upgrade = None
    upgrade_id = request.GET.get('upgrade')
    if upgrade_id and upgrade_id.isdigit():
        upgrade = earnedgov_claims.fetch_claim(upgrade_id, verbs=earnedgov_claims.WALL_VERBS)

    adopt = None
    adopt_id = request.GET.get('adopt')
    if adopt_id and adopt_id.isdigit():
        adopt = earnedgov_claims.fetch_claim(adopt_id, verbs=(earnedgov_claims.OPP_VERB,))

    errors = []
    form = {
        'mode': 'self',
        'name': '', 'link': '', 'role': 'supporter', 'statement': '',
        'voucher_name': '', 'voucher_link': '', 'video_url': '',
    }
    if upgrade:
        form.update({
            'name': upgrade.get('name') or '',
            'link': upgrade.get('subject_uri') or '',
            'role': upgrade.get('role') or 'supporter',
            'statement': upgrade.get('statement') or '',
        })
    elif adopt:
        verb = 'Adopting' if adopt.get('adoptable', True) else 'Joining'
        form.update({
            'role': 'founder',
            'statement': f"{verb} the opportunity “{adopt.get('name') or ''}” "
                         f"({adopt.get('subject_uri')}): ",
        })

    if request.method == 'POST':
        for key in form:
            form[key] = (request.POST.get(key) or '').strip()
        name = form['name']
        statement = form['statement']
        role = form['role'] if form['role'] in earnedgov_claims.ROLES else 'supporter'
        self_attested = form['mode'] != 'vouch'
        link = form['link']
        video_url = form['video_url']

        if not name:
            errors.append("Please give the person's name.")
        if not statement:
            errors.append("Your declaration needs words — what was actually said.")
        if link and not link.startswith(('http://', 'https://')):
            link = 'https://' + link
        if not link:
            # Subject must be a URI; anchor unlinked people under the effort page.
            link = f"https://linkedtrust.us/earnedgov#{slugify(name)}"
        voucher_link = form['voucher_link']
        if voucher_link and not voucher_link.startswith(('http://', 'https://')):
            voucher_link = 'https://' + voucher_link
        if not self_attested and not form['voucher_name']:
            errors.append("Vouching: add your own name so the attestation says who heard it.")
        if video_url and not video_url.startswith(earnedgov_claims.LT_API):
            errors.append("Video URL doesn't look like a LinkedTrust upload.")

        if adopt and adopt.get('gate_type') and not request.POST.get('gate_agree'):
            errors.append(
                f"This opportunity has a {adopt['gate_type']} gate — you must "
                f"agree to its terms to join."
            )
        if not errors:
            statement_full = statement
            if not self_attested and form['voucher_name']:
                statement_full = f"{statement}\n\n— as told to {form['voucher_name']}"
            if adopt and adopt.get('gate_type') and request.POST.get('gate_agree'):
                statement_full += (
                    f"\n\n[Agreed to the opportunity's {adopt['gate_type']} gate: "
                    f"{adopt.get('gate_terms')}]"
                )
            try:
                claim = earnedgov_claims.create_commitment(
                    subject_uri=link,
                    name=name,
                    role=role,
                    statement=statement_full,
                    self_attested=self_attested,
                    voucher_uri=voucher_link or None,
                    photo_file=request.FILES.get('photo'),
                    video_url=video_url or None,
                )
                cid = claim.get('id')
                if cid:
                    # Walk-ups are held for review; only GovKit-invited commits
                    # (the /earnedgov/i/<code>/ page) auto-approve to the wall.
                    EarnedgovCommitment.objects.get_or_create(
                        claim_id=cid,
                        defaults={
                            'status': 'pending',
                            'invited': False,
                            'person_name': name,
                            'role': role,
                        },
                    )
                return redirect(f"{reverse('earnedgov')}?committed={cid}&pending=1#committed")
            except ValueError as e:
                errors.append(str(e))
            except Exception:
                logger.exception("earnedgov: claim creation failed")
                errors.append("Could not reach LinkedTrust to record your declaration — please try again in a minute.")

    return render(request, 'earnedgov_commit.html', {
        'form': form,
        'errors': errors,
        'upgrade': upgrade,
        'adopt': adopt,
        'roles': earnedgov_claims.ROLES,
        'lt_api': earnedgov_claims.LT_API,
    })


@csrf_protect
def earnedgov_invite_view(request, code):
    """
    Personal magic-link page for a GovKit-minted invite: greets the person by
    name, prefills the commitment the inviter drafted, and takes one click.
    The claim publishes to the wall instantly (possession of a valid code is
    the spam gate), GovKit is told, and the success screen hands the person
    GovKit's SSO accept link — commit, then straight to the dashboard.
    """
    from . import earnedgov_claims, earnedgov_govkit
    from .models import EarnedgovCommitment

    try:
        invite = earnedgov_govkit.resolve_invite(code)
    except earnedgov_govkit.GovKitUnavailable:
        return render(request, 'earnedgov_invite.html', {'state': 'unavailable'}, status=503)
    if invite is None or invite.get('status') == 'revoked':
        return render(request, 'earnedgov_invite.html', {'state': 'invalid'}, status=404)

    audience = invite.get('audience') or 'supporter'
    if audience not in earnedgov_claims.ROLES:
        audience = 'supporter'
    lt_api = earnedgov_claims.LT_API

    if invite.get('status') == 'accepted':
        return render(request, 'earnedgov_invite.html', {
            'state': 'accepted',
            'invite': invite,
            'dashboard_url': getattr(settings, 'GOVKIT_BASE_URL', ''),
        })

    # Already committed (GovKit knows), or just committed via the redirect
    # below. GovKit's accept works from 'created' too, so a failed callback
    # never strands the person — it only delays the status column.
    just_committed = request.GET.get('committed', '')
    claim_id = invite.get('committed_claim_id') or (
        just_committed if just_committed.isdigit() else None
    )
    if invite.get('status') == 'committed' or (just_committed and claim_id):
        return render(request, 'earnedgov_invite.html', {
            'state': 'committed',
            'invite': invite,
            'claim_id': claim_id,
            'accept_url': invite.get('accept_url', ''),
            'lt_api': lt_api,
        })

    errors = []
    form = {
        'name': invite.get('name') or '',
        'link': invite.get('link') or '',
        'statement': (invite.get('drafted_statement') or '').strip()
                     or earnedgov_govkit.AUDIENCE_STATEMENTS.get(audience, ''),
        'video_url': '',
    }

    if request.method == 'POST':
        for key in form:
            form[key] = (request.POST.get(key) or '').strip()
        name = form['name']
        statement = form['statement']
        link = form['link']
        video_url = form['video_url']

        if not name:
            errors.append("Please give your name.")
        if not statement:
            errors.append("Your declaration needs words — say it your way, a sentence is plenty.")
        if link and not link.startswith(('http://', 'https://')):
            link = 'https://' + link
        if not link:
            link = f"https://linkedtrust.us/earnedgov#{slugify(name)}"
        if video_url and not video_url.startswith(lt_api):
            errors.append("Video URL doesn't look like a LinkedTrust upload.")

        if not errors:
            try:
                claim = earnedgov_claims.create_commitment(
                    subject_uri=link,
                    name=name,
                    role=audience,
                    statement=statement,
                    self_attested=True,
                    photo_file=request.FILES.get('photo'),
                    video_url=video_url or None,
                )
                cid = claim.get('id')
                if cid:
                    EarnedgovCommitment.objects.get_or_create(
                        claim_id=cid,
                        defaults={
                            'status': 'approved',
                            'invited': True,
                            'inviter': 'govkit',
                            'person_name': name,
                            'role': audience,
                        },
                    )
                    earnedgov_govkit.report_committed(
                        code, claim_id=cid, statement=statement,
                        video_url=video_url or None,
                    )
                return redirect(f"{request.path}?committed={cid or ''}")
            except ValueError as e:
                errors.append(str(e))
            except Exception:
                logger.exception("earnedgov: invited claim creation failed")
                errors.append("Could not reach LinkedTrust to record your declaration — please try again in a minute.")

    return render(request, 'earnedgov_invite.html', {
        'state': 'form',
        'invite': invite,
        'audience': audience,
        # Per-audience language (2026-07-15 pin): founders share a launch,
        # mentors/advisors join, funders back — never "commit".
        'invite_lede': earnedgov_claims.ROLE_INVITE_LEDES.get(
            audience, 'Join the Earned Governance Accelerator.'),
        'button_label': earnedgov_claims.ROLE_INVITE_BUTTONS.get(
            audience, 'Count me in'),
        'form': form,
        'errors': errors,
        'lt_api': lt_api,
    })


def earnedgov_card_view(request, claim_id):
    """
    Server-rendered 1200x630 share card (PNG) for a commitment claim, used as
    og:image so a pasted wall link shows the person and their words.
    """
    from . import earnedgov_claims
    from django.core.cache import cache
    from django.http import HttpResponse, Http404

    cache_key = f"earnedgov_card_{claim_id}"
    png = cache.get(cache_key)
    if png is None:
        c = earnedgov_claims.fetch_claim(claim_id, verbs=earnedgov_claims.WALL_VERBS)
        if not c:
            raise Http404
        png = _render_commit_card(c)
        cache.set(cache_key, png, 600)
    return HttpResponse(png, content_type='image/png')


def _render_commit_card(c):
    from io import BytesIO
    from PIL import Image, ImageDraw, ImageFont

    W, H = 1200, 630
    img = Image.new('RGB', (W, H), (15, 17, 23))          # --bg-dark
    d = ImageDraw.Draw(img)
    # gradient bar (cyan -> purple), simple horizontal interpolation
    for x in range(W):
        t = x / W
        col = (int(0 + t * 102), int(178 - t * 52), int(229 + t * 5))
        d.line([(x, 0), (x, 10)], fill=col)

    fp = '/usr/share/fonts/truetype/dejavu/'
    f_label = ImageFont.truetype(fp + 'DejaVuSansMono.ttf', 28)
    f_name = ImageFont.truetype(fp + 'DejaVuSans-Bold.ttf', 64)
    f_role = ImageFont.truetype(fp + 'DejaVuSans-Bold.ttf', 34)
    f_quote = ImageFont.truetype(fp + 'DejaVuSans.ttf', 36)
    f_foot = ImageFont.truetype(fp + 'DejaVuSans.ttf', 26)

    d.text((70, 60), '// earned governance accelerator', font=f_label, fill=(0, 178, 229))
    d.text((70, 130), c['name'] or 'Someone new is in', font=f_name, fill=(240, 240, 240))
    from .earnedgov_claims import ROLE_CARD_LABELS
    d.text((70, 215), ROLE_CARD_LABELS.get(c['role'] or '', (c['role'] or '').title()).upper(), font=f_role, fill=(102, 126, 234))

    # word-wrapped quote, max 4 lines
    words = (c['statement'] or '').replace('\n', ' ').split()
    lines, cur = [], ''
    for w in words:
        trial = (cur + ' ' + w).strip()
        if d.textlength(trial, font=f_quote) > W - 180:
            lines.append(cur)
            cur = w
            if len(lines) == 4:
                cur += ' …'
                break
        else:
            cur = trial
    if cur:
        lines.append(cur)
    y = 300
    for ln in lines[:4]:
        d.text((70, y), ('“' if ln is lines[0] else '') + ln + ('”' if ln is lines[-1] else ''),
               font=f_quote, fill=(200, 200, 205))
        y += 52

    d.text((70, H - 70), 'linkedtrust.us/earnedgov — a verifiable declaration on LinkedTrust',
           font=f_foot, fill=(136, 136, 153))

    buf = BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()


@csrf_protect
def earnedgov_opps_view(request):
    """
    Adoptable opportunities: openings (ventures, projects, partnerships, grants,
    roles) that can turn into cohort things. Stored as OPPORTUNITY claims on
    LinkedTrust; anyone can post one; "Adopt this" routes into the commit flow.
    """
    from . import earnedgov_claims

    errors = []
    posted_id = None
    form = {'title': '', 'kind': 'project', 'statement': '', 'link': '', 'poster_link': '',
            'owner': '', 'owner_link': '', 'lead': '', 'ip': '', 'valuation': '',
            'gate_type': '', 'gate_terms': ''}

    if request.method == 'POST':
        for key in form:
            form[key] = (request.POST.get(key) or '').strip()
        if not form['title']:
            errors.append("The opportunity needs a short title.")
        if not form['statement']:
            errors.append("Describe the opportunity — what is it, and what would adopting it mean?")
        link = form['link']
        if link and not link.startswith(('http://', 'https://')):
            link = 'https://' + link
        poster = form['poster_link']
        if poster and not poster.startswith(('http://', 'https://')):
            poster = 'https://' + poster
        owner_link = form['owner_link']
        if owner_link and not owner_link.startswith(('http://', 'https://')):
            owner_link = 'https://' + owner_link
        valuation = form['valuation'].replace(',', '').replace('$', '')
        if valuation:
            try:
                valuation = float(valuation)
            except ValueError:
                errors.append("Valuation should be a number (USD).")
                valuation = None
        if form['gate_type'] and form['gate_type'] not in ('purpose', 'agreement'):
            form['gate_type'] = ''
        if form['gate_type'] and not form['gate_terms']:
            errors.append("A join gate needs its terms — what must a joiner agree to?")
        if not errors:
            try:
                claim = earnedgov_claims.create_opportunity(
                    title=form['title'],
                    kind=form['kind'],
                    statement=form['statement'],
                    link=link or None,
                    poster_uri=poster or None,
                    owner=form['owner'] or None,
                    owner_link=owner_link or None,
                    lead=form['lead'] or None,
                    ip=form['ip'] or None,
                    valuation=valuation or None,
                    gate_type=form['gate_type'] or None,
                    gate_terms=form['gate_terms'] or None,
                )
                return redirect(f"{reverse('earnedgov_opps')}?posted={claim.get('id', '')}")
            except Exception:
                logger.exception("earnedgov: opportunity creation failed")
                errors.append("Could not reach LinkedTrust — please try again in a minute.")

    return render(request, 'earnedgov_opps.html', {
        'board': earnedgov_claims.fetch_opportunities(),
        'form': form,
        'errors': errors,
        'posted_id': request.GET.get('posted'),
        'kinds': earnedgov_claims.OPP_KINDS,
        'lt_api': earnedgov_claims.LT_API,
    })

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
    all_items = EcosystemItem.objects.all()
    context = {
        'ecosystem_items': all_items,
        'ecosystem_standards': all_items.filter(sort_order__lte=1),
        'ecosystem_platforms': all_items.filter(sort_order__gte=2, sort_order__lte=8),
        'ecosystem_devtools': all_items.filter(sort_order__gte=9),
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

    # Dedicated landing pages for key services
    dedicated_templates = {
        'baremetal-migration': 'service_baremetal.html',
        'ai-integration': 'service_ai_integration.html',
        'global-adoption': 'service_global_adoption.html',
    }
    template = dedicated_templates.get(slug, 'service_detail.html')

    context = {
        'service': service,
        'example_projects': service.example_projects.all(),
    }
    return render(request, template, context)


def services_startups_view(request):
    """Landing page for startup services."""
    return render(request, 'services_startups.html')


def services_nonprofits_view(request):
    """Landing page for nonprofit services."""
    return render(request, 'services_nonprofits.html')


def services_launch_view(request):
    """Landing page for MVP/launch services."""
    return render(request, 'services_launch.html')