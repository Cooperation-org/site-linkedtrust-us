"""LevelUp workshop registration: /levelup/ form, pricing tiers, access codes,
Stripe handoff, emails, and the thanks page."""
import hashlib
import hmac
import json
from pathlib import Path
import tempfile
import time

from unittest.mock import patch

from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from .forms import LevelUpRegistrationForm
from .models import LevelUpAccessCode, LevelUpRegistration
from .views import _levelup_send_access


def payload(**over):
    base = {
        'name': 'Ada Example',
        'email': 'ada@example.org',
        'organization': 'Ada Labs',
        'link': 'https://adalabs.example',
        'help_with': 'deploy',
        'help_with_other': '',
        'wants_checkin': 'on',
        'tier': 'free_nonprofit',
        'session': 'oct21',
        'code': '',
        'company_fax': '',
    }
    base.update(over)
    return base


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
                   LEVELUP_STRIPE_PAYMENT_LINK='', LEVELUP_STRIPE_WEBHOOK_SECRET='whsec_test',
                   LEVELUP_VIDEO_URL='', LEVELUP_NOTIFY_EMAIL='team@example.org')
class LevelUpPageTests(TestCase):
    def test_page_renders_with_form(self):
        r = self.client.get('/levelup/')
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Save your seat')
        self.assertContains(r, 'name="help_with"')
        self.assertContains(r, 'Where did you hear about us?')
        self.assertContains(r, 'Wednesday, October 21, 2026')
        self.assertContains(r, 'multipart/form-data')
        self.assertContains(r, 'levelup-banner-1200x627.png')
        self.assertContains(r, 'levelup-qr.png')

    def test_heard_from_saves_and_is_optional(self):
        self.client.post('/levelup/', payload(heard_from='A flyer at the cafe'))
        self.assertEqual(LevelUpRegistration.objects.get().heard_from, 'A flyer at the cafe')
        LevelUpRegistration.objects.all().delete()
        self.client.post('/levelup/', payload(email='second@example.org'))
        self.assertEqual(LevelUpRegistration.objects.get().heard_from, '')

    def test_no_slash_redirects(self):
        self.assertEqual(self.client.get('/levelup').status_code, 301)
        self.assertEqual(self.client.get('/levelup/register/').status_code, 301)

    def test_free_registration_saves_and_emails(self):
        r = self.client.post('/levelup/', payload())
        self.assertRedirects(r, '/levelup/thanks/', fetch_redirect_response=False)
        reg = LevelUpRegistration.objects.get()
        self.assertEqual(reg.help_with, 'deploy,scale')
        self.assertEqual(reg.help_with_labels(), ['Deployment, infrastructure and DevOps', 'Reliability and scalability'])
        self.assertTrue(reg.wants_checkin)
        self.assertEqual(reg.payment_status, 'free')
        self.assertEqual(len(mail.outbox), 2)
        team, attendee = mail.outbox
        self.assertEqual(team.to, ['team@example.org'])
        self.assertIn('Ada Labs', team.subject)
        self.assertIn('1-1 check-in: yes', team.body)
        self.assertEqual(attendee.to, ['ada@example.org'])
        self.assertIn('7:00 to 9:00 am PT', attendee.body)
        self.assertIn('1-1 check-in', attendee.body)
        self.assertEqual(len(attendee.attachments), 1)
        calendar_name, calendar_body, calendar_type = attendee.attachments[0]
        self.assertEqual(calendar_name, 'levelup-oct21.ics')
        if isinstance(calendar_body, bytes):
            calendar_body = calendar_body.decode()
        self.assertIn('DTSTART:20261021T140000Z', calendar_body)
        self.assertIn('text/calendar', calendar_type)

    def test_thanks_page_uses_session(self):
        self.client.post('/levelup/', payload())
        r = self.client.get('/levelup/thanks/')
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'You are in, Ada.')
        self.assertContains(r, 'ada@example.org')
        self.assertContains(r, 'check-in')
        self.assertContains(r, 'noindex')

    def test_thanks_without_session_redirects_home(self):
        self.assertRedirects(self.client.get('/levelup/thanks/'), '/levelup/', fetch_redirect_response=False)

    def test_paid_without_stripe_is_pending(self):
        r = self.client.post('/levelup/', payload(tier='paid'))
        self.assertRedirects(r, '/levelup/thanks/', fetch_redirect_response=False)
        reg = LevelUpRegistration.objects.get()
        self.assertEqual(reg.payment_status, 'pending')
        self.assertIn('$49', mail.outbox[1].body)
        r = self.client.get('/levelup/thanks/')
        self.assertContains(r, 'payment link')

    @override_settings(LEVELUP_STRIPE_PAYMENT_LINK='https://buy.stripe.com/test_abc')
    def test_payment_link_goes_in_the_email_not_a_redirect(self):
        r = self.client.post('/levelup/', payload(tier='paid'))
        reg = LevelUpRegistration.objects.get()
        self.assertRedirects(r, '/levelup/thanks/', fetch_redirect_response=False)
        body = mail.outbox[1].body
        self.assertIn('https://buy.stripe.com/test_abc?', body)
        self.assertIn('prefilled_email=ada%40example.org', body)
        self.assertIn(f'client_reference_id=levelup-{reg.pk}', body)
        self.assertEqual(reg.payment_status, 'pending')
        self.assertEqual(self.client.session['levelup_registered'], reg.pk)

    @override_settings(LEVELUP_STRIPE_BUY_BUTTON_ID='buy_btn_test',
                       LEVELUP_STRIPE_PUBLISHABLE_KEY='pk_live_test')
    def test_buy_button_is_on_the_thanks_page_for_an_unpaid_seat(self):
        self.client.post('/levelup/', payload(tier='paid'))
        reg = LevelUpRegistration.objects.get()
        r = self.client.get('/levelup/thanks/')
        self.assertContains(r, 'https://js.stripe.com/v3/buy-button.js')
        self.assertContains(r, 'buy-button-id="buy_btn_test"')
        self.assertContains(r, f'client-reference-id="levelup-{reg.pk}"')
        self.assertContains(r, 'customer-email="ada@example.org"')
        self.assertIn('https://js.stripe.com', r['Content-Security-Policy'])

    @override_settings(LEVELUP_STRIPE_BUY_BUTTON_ID='buy_btn_test',
                       LEVELUP_STRIPE_PUBLISHABLE_KEY='pk_live_test')
    def test_no_buy_button_for_a_free_seat(self):
        self.client.post('/levelup/', payload(tier='free_nonprofit'))
        r = self.client.get('/levelup/thanks/')
        self.assertNotContains(r, 'buy-button-id')
        self.assertNotContains(r, 'buy-button.js')

    def test_paid_query_parameter_cannot_spoof_payment(self):
        self.client.post('/levelup/', payload(tier='paid'))
        r = self.client.get('/levelup/thanks/?paid=1')
        self.assertNotContains(r, 'Payment received')
        self.assertContains(r, 'payment link')

    def test_optional_attachment_is_saved(self):
        upload = SimpleUploadedFile('project-brief.pdf', b'%PDF-1.4 test')
        with tempfile.TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            r = self.client.post('/levelup/', {**payload(), 'attachment': upload})
            self.assertRedirects(r, '/levelup/thanks/', fetch_redirect_response=False)
            registration = LevelUpRegistration.objects.get()
            self.assertEqual(Path(registration.attachment.name).name, 'project-brief.pdf')
            self.assertTrue(Path(registration.attachment.path).exists())
            self.assertIn('project-brief.pdf', mail.outbox[0].body)

    def test_attachment_size_is_limited(self):
        upload = SimpleUploadedFile('too-large.pdf', b'x' * (10 * 1024 * 1024 + 1))
        form = LevelUpRegistrationForm(payload(), files={'attachment': upload})
        self.assertFalse(form.is_valid())
        self.assertIn('under 10 MB', form.errors['attachment'][0])

    def test_attachment_extension_is_limited(self):
        upload = SimpleUploadedFile('payload.html', b'<script>alert(1)</script>')
        form = LevelUpRegistrationForm(payload(), files={'attachment': upload})
        self.assertFalse(form.is_valid())
        self.assertIn('attachment', form.errors)

    def test_access_code_makes_paid_free_and_counts_use(self):
        code = LevelUpAccessCode.objects.create(code='builders', label='Slack channel', max_uses=1)
        self.assertEqual(code.code, 'BUILDERS')
        r = self.client.post('/levelup/', payload(tier='paid', code=' builders '))
        self.assertRedirects(r, '/levelup/thanks/', fetch_redirect_response=False)
        reg = LevelUpRegistration.objects.get()
        self.assertEqual(reg.payment_status, 'free')
        self.assertEqual(reg.access_code, code)
        code.refresh_from_db()
        self.assertEqual(code.uses, 1)
        self.assertFalse(code.usable)
        # Exhausted code is rejected
        r = self.client.post('/levelup/', payload(email='b@example.org', code='BUILDERS'))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'no longer active')
        self.assertEqual(LevelUpRegistration.objects.count(), 1)

    def test_unknown_code_rejected(self):
        r = self.client.post('/levelup/', payload(code='NOPE'))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'not recognised')
        self.assertEqual(LevelUpRegistration.objects.count(), 0)

    def test_inactive_code_rejected(self):
        LevelUpAccessCode.objects.create(code='OLD', active=False)
        r = self.client.post('/levelup/', payload(code='old'))
        self.assertContains(r, 'no longer active')

    def test_help_with_is_optional(self):
        r = self.client.post('/levelup/', payload(help_with=''))
        self.assertEqual(r.status_code, 302)
        self.assertEqual(LevelUpRegistration.objects.get().help_with, '')

    def test_help_with_other_keeps_the_free_text(self):
        self.client.post('/levelup/', payload(help_with='other', help_with_other='Pricing the thing'))
        reg = LevelUpRegistration.objects.get()
        self.assertEqual(reg.help_with, 'other')
        self.assertEqual(reg.help_with_labels(), ['Pricing the thing'])

    def test_help_with_other_text_is_dropped_for_other_choices(self):
        self.client.post('/levelup/', payload(help_with='deploy', help_with_other='ignored'))
        self.assertEqual(LevelUpRegistration.objects.get().help_with_other, '')

    def test_required_fields_and_errors_marked(self):
        r = self.client.post('/levelup/', payload(name='', email='not-an-email'))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'lu-field has-error', count=2)
        self.assertEqual(LevelUpRegistration.objects.count(), 0)

    def test_honeypot_blocks_bots(self):
        r = self.client.post('/levelup/', payload(company_fax='http://spam'))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(LevelUpRegistration.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_invalid_help_key_rejected(self):
        form = LevelUpRegistrationForm(payload(help_with=['hacking']))
        self.assertFalse(form.is_valid())
        self.assertIn('help_with', form.errors)

    @override_settings(LEVELUP_VIDEO_URL='https://meet.example.org/private-room')
    def test_access_email_includes_link_and_updates_calendar(self):
        registration = LevelUpRegistration.objects.create(
            name='Ada Example', email='ada@example.org', organization='Ada Labs',
            help_with='deploy', goal='Ship it', tier='free_nonprofit', payment_status='free',
        )
        self.assertTrue(_levelup_send_access(registration, 'https://meet.example.org/private-room'))
        registration.refresh_from_db()
        self.assertTrue(registration.invited)
        self.assertIsNotNone(registration.access_sent_at)
        self.assertIn('https://meet.example.org/private-room', mail.outbox[0].body)
        calendar_body = mail.outbox[0].attachments[0][1]
        if isinstance(calendar_body, bytes):
            calendar_body = calendar_body.decode()
        self.assertIn('https://meet.example.org/private-room', calendar_body)

    def _stripe_event(self, registration, **overrides):
        session = {
            'id': 'cs_test_levelup',
            'client_reference_id': f'levelup-{registration.pk}',
            'payment_status': 'paid',
            'amount_total': 4900,
            'currency': 'usd',
        }
        session.update(overrides)
        return {
            'type': 'checkout.session.completed',
            'data': {'object': session},
        }

    def _signed_webhook(self, event, secret='whsec_test'):
        body = json.dumps(event, separators=(',', ':')).encode()
        timestamp = int(time.time())
        signature = hmac.new(
            secret.encode(), str(timestamp).encode() + b'.' + body, hashlib.sha256
        ).hexdigest()
        return self.client.post(
            '/levelup/stripe/webhook/', data=body, content_type='application/json',
            HTTP_STRIPE_SIGNATURE=f't={timestamp},v1={signature}',
        )

    def test_verified_stripe_webhook_marks_registration_paid(self):
        registration = LevelUpRegistration.objects.create(
            name='Ada Example', email='ada@example.org', organization='Ada Labs',
            help_with='deploy', goal='Ship it', tier='paid', payment_status='pending',
        )
        r = self._signed_webhook(self._stripe_event(registration))
        self.assertEqual(r.status_code, 200)
        self.assertJSONEqual(r.content, {'received': True, 'updated': True})
        registration.refresh_from_db()
        self.assertEqual(registration.payment_status, 'paid')
        self.assertEqual(registration.stripe_reference, 'cs_test_levelup')

    def test_stripe_webhook_rejects_bad_signature(self):
        registration = LevelUpRegistration.objects.create(
            name='Ada Example', email='ada@example.org', organization='Ada Labs',
            help_with='deploy', goal='Ship it', tier='paid', payment_status='pending',
        )
        event = self._stripe_event(registration)
        body = json.dumps(event, separators=(',', ':')).encode()
        r = self.client.post(
            '/levelup/stripe/webhook/', data=body, content_type='application/json',
            HTTP_STRIPE_SIGNATURE=f't={int(time.time())},v1=wrong',
        )
        self.assertEqual(r.status_code, 400)
        registration.refresh_from_db()
        self.assertEqual(registration.payment_status, 'pending')

    def test_stripe_webhook_ignores_wrong_amount(self):
        registration = LevelUpRegistration.objects.create(
            name='Ada Example', email='ada@example.org', organization='Ada Labs',
            help_with='deploy', goal='Ship it', tier='paid', payment_status='pending',
        )
        r = self._signed_webhook(self._stripe_event(registration, amount_total=5000))
        self.assertEqual(r.status_code, 200)
        registration.refresh_from_db()
        self.assertEqual(registration.payment_status, 'pending')

    def test_sitemap_lists_levelup(self):
        r = self.client.get('/sitemap-pages.xml')
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, '/levelup/')


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
                   LEVELUP_STRIPE_PAYMENT_LINK='', LEVELUP_NOTIFY_EMAIL='connect@linkedtrust.us')
class LevelUpSessionTests(TestCase):
    """Both sittings are offered, and the one picked drives the emails and the .ics."""

    def test_page_offers_upcoming_sittings_in_pacific_time(self):
        r = self.client.get('/levelup/')
        self.assertContains(r, 'Wednesday, October 21, 2026')
        self.assertContains(r, 'Wednesday, November 18, 2026')
        self.assertNotContains(r, 'September 16')
        self.assertNotContains(r, 'UTC')
        self.assertContains(r, '7:00 to 9:00 am PT')

    def test_free_for_nonprofits_only(self):
        r = self.client.get('/levelup/')
        self.assertContains(r, 'Cost: $49')
        self.assertContains(r, 'Free for nonprofits.')
        self.assertNotContains(r, 'olopreneur')
        self.assertNotContains(r, 'under 10')
        self.assertNotContains(r, 'employees')

    def test_page_leads_with_production(self):
        r = self.client.get('/levelup/')
        self.assertContains(r, 'Go from vibe coding')
        self.assertContains(r, 'to live in production.')
        self.assertContains(r, '$49')
        self.assertNotContains(r, '$100')

    def test_november_is_pacific_standard_time(self):
        self.client.post('/levelup/', payload(session='nov18'))
        attendee = mail.outbox[1]
        self.assertIn('Wednesday, November 18, 2026', attendee.body)
        ics = [c for c in attendee.attachments if str(c[0]).endswith('.ics')][0][1]
        body = ics.decode() if isinstance(ics, bytes) else ics
        self.assertIn('DTSTART:20261118T150000Z', body)
        self.assertIn('DTEND:20261118T170000Z', body)

    def test_past_sitting_is_not_accepted(self):
        self.client.post('/levelup/', payload(session='sep16'))
        self.assertFalse(LevelUpRegistration.objects.exists())

    def test_october_choice_drives_emails_and_calendar(self):
        self.client.post('/levelup/', payload(session='oct21'))
        reg = LevelUpRegistration.objects.get()
        self.assertEqual(reg.session, 'oct21')
        team, attendee = mail.outbox
        self.assertIn('Wednesday, October 21, 2026', team.body)
        self.assertIn('Wednesday, October 21, 2026', attendee.body)
        self.assertIn('Oct 21', attendee.subject)
        ics = [c for c in attendee.attachments if str(c[0]).endswith('.ics')][0][1]
        body = ics.decode() if isinstance(ics, bytes) else ics
        self.assertIn('DTSTART:20261021T140000Z', body)
        self.assertIn('DTEND:20261021T160000Z', body)

    def test_thanks_page_shows_the_chosen_sitting(self):
        self.client.post('/levelup/', payload(session='oct21'))
        r = self.client.get('/levelup/thanks/')
        self.assertContains(r, 'Wednesday, October 21, 2026')
        self.assertContains(r, '/levelup/calendar/oct21.ics')

    def test_ics_download_is_a_calendar_file(self):
        r = self.client.get('/levelup/calendar/oct21.ics')
        self.assertEqual(r.status_code, 200)
        self.assertIn('text/calendar', r['Content-Type'])
        self.assertIn('levelup-oct21.ics', r['Content-Disposition'])
        self.assertIn('DTSTART:20261021T140000Z', r.content.decode())

    def test_sitting_shows_pacific_time_on_the_page(self):
        r = self.client.get('/levelup/')
        self.assertContains(r, 'Wednesday, October 21, 2026, 7:00 to 9:00 am PT')
        self.assertNotContains(r, 'Pick one when you register')

    def test_unknown_session_rejected(self):
        r = self.client.post('/levelup/', payload(session='dec25'))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(LevelUpRegistration.objects.count(), 0)

    def test_team_notification_goes_to_connect_inbox(self):
        self.client.post('/levelup/', payload())
        self.assertEqual(mail.outbox[0].to, ['connect@linkedtrust.us'])
        self.assertIn('Wednesday, October 21, 2026', mail.outbox[0].body)


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
                   LEVELUP_STRIPE_PAYMENT_LINK='', LEVELUP_NOTIFY_EMAIL='connect@linkedtrust.us')
class LevelUpNotificationTests(TestCase):
    """A registration must never be lost to a mail outage, and the admin has to
    show whether the notification actually left the server."""

    def test_delivery_is_recorded_on_success(self):
        self.client.post('/levelup/', payload())
        reg = LevelUpRegistration.objects.get()
        self.assertTrue(reg.team_notified)
        self.assertTrue(reg.attendee_notified)

    def test_registration_survives_a_dead_mail_server(self):
        with patch('website.views.EmailMessage.send', side_effect=OSError('smtp down')):
            r = self.client.post('/levelup/', payload())
        self.assertRedirects(r, '/levelup/thanks/', fetch_redirect_response=False)
        reg = LevelUpRegistration.objects.get()
        self.assertFalse(reg.team_notified)
        self.assertFalse(reg.attendee_notified)

    def test_attendee_failure_still_records_the_team_notification(self):
        real = LevelUpRegistration.objects.count
        calls = {'n': 0}

        def flaky(self, *a, **kw):
            calls['n'] += 1
            if calls['n'] > 1:
                raise OSError('smtp down')
            return 1

        with patch('website.views.EmailMessage.send', flaky):
            self.client.post('/levelup/', payload())
        reg = LevelUpRegistration.objects.get()
        self.assertTrue(reg.team_notified)
        self.assertFalse(reg.attendee_notified)


class CsrfFailurePageTests(TestCase):
    """A stale form must not drop a registrant on Django's debug 403."""

    def test_expired_form_gets_a_way_back(self):
        client = Client(enforce_csrf_checks=True)
        r = client.post('/levelup/', payload())
        self.assertEqual(r.status_code, 403)
        self.assertContains(r, 'This page expired', status_code=403)
        self.assertContains(r, 'Back to LevelUp', status_code=403)


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class LevelUpCodeCheckTests(TestCase):
    """The form shows the price before submitting, so the code endpoint has to
    agree with what save() will do."""

    def setUp(self):
        self.code = LevelUpAccessCode.objects.create(code='PARTNER1', label='A partner')

    def test_valid_code_is_reported_valid(self):
        r = self.client.post('/levelup/code/', {'code': 'partner1'})
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json()['valid'])

    def test_unknown_code_is_reported_invalid(self):
        self.assertFalse(self.client.post('/levelup/code/', {'code': 'NOPE'}).json()['valid'])

    def test_exhausted_code_is_reported_invalid(self):
        self.code.max_uses = 1
        self.code.uses = 1
        self.code.save()
        self.assertFalse(self.client.post('/levelup/code/', {'code': 'PARTNER1'}).json()['valid'])

    def test_get_is_not_allowed(self):
        self.assertEqual(self.client.get('/levelup/code/').status_code, 405)

    def test_guessing_is_throttled(self):
        for _ in range(20):
            self.client.post('/levelup/code/', {'code': 'NOPE'})
        self.assertEqual(self.client.post('/levelup/code/', {'code': 'PARTNER1'}).status_code, 429)


class LevelUpAccessCodeCreatorTests(TestCase):
    def test_admin_records_who_created_a_code(self):
        from django.contrib.auth import get_user_model
        user = get_user_model().objects.create_superuser('codemaker', 'codemaker@example.org', 'pw')
        self.client.force_login(user)
        self.client.post(reverse('linkedtrust_admin:website_levelupaccesscode_add'),
                         {'code': 'partner1', 'label': 'A partner', 'active': 'on', 'max_uses': '0'})
        code = LevelUpAccessCode.objects.get(code='PARTNER1')
        self.assertEqual(code.created_by, user)
        other = get_user_model().objects.create_superuser('editor', 'editor@example.org', 'pw')
        self.client.force_login(other)
        self.client.post(reverse('linkedtrust_admin:website_levelupaccesscode_change', args=[code.pk]),
                         {'code': 'PARTNER1', 'label': 'Renamed', 'active': 'on', 'max_uses': '0'})
        code.refresh_from_db()
        self.assertEqual(code.label, 'Renamed')
        self.assertEqual(code.created_by, user)


class LevelUpBadgeTests(TestCase):
    def _badge(self, claim_id):
        from .models import Testimonial
        return Testimonial.objects.create(
            person_name=f'Person {claim_id}', person_title='Founder',
            quote_text='It went live.', linked_claim_id=claim_id,
            placement='levelup', badge_layout='card', badge_theme='light',
        )

    def test_levelup_badge_shows_on_levelup_page_and_homepage(self):
        # Seeded by migration 0020.
        from .models import Testimonial
        self.assertTrue(Testimonial.objects.filter(linked_claim_id='124842', placement='levelup').exists())
        for url in ('/levelup/', '/'):
            r = self.client.get(url)
            self.assertContains(r, '<linked-badge claim-id="124842" layout="card" theme="light">', html=False)

    def _rail(self, html):
        """Just the badge rail markup, so page CSS and JS do not skew counts."""
        start = html.index('<div class="lu-hero-badge"')
        return html[start:html.index('</section>', start)]

    def test_badge_sits_in_the_hero(self):
        html = self.client.get('/levelup/').content.decode()
        hero = html[html.index('<section class="lu-hero"'):html.index('<div class="lu-body">')]
        self.assertIn('lu-hero-badge', hero)
        self.assertIn('claim-id="124842"', hero)
        self.assertIn('has-badge', hero)

    def test_one_page_of_two_badges_does_not_rotate(self):
        self._badge('900001')
        rail = self._rail(self.client.get('/levelup/').content.decode())
        self.assertEqual(rail.count('<div class="lu-badge-page'), 1)
        self.assertEqual(rail.count('<linked-badge'), 2)
        self.assertNotIn('aria-hidden="true"', rail)

    def test_more_than_two_badges_paginate_two_at_a_time(self):
        for claim in ('900001', '900002', '900003'):
            self._badge(claim)
        rail = self._rail(self.client.get('/levelup/').content.decode())
        self.assertEqual(rail.count('<div class="lu-badge-page'), 2)  # 4 badges, 2 pages
        self.assertEqual(rail.count('<linked-badge'), 4)
        self.assertEqual(rail.count('is-on'), 1)
        self.assertEqual(rail.count('aria-hidden="true"'), 1)

    def test_hero_has_no_badge_markup_when_there_are_none(self):
        from .models import Testimonial
        Testimonial.objects.filter(placement='levelup').delete()
        html = self.client.get('/levelup/').content.decode()
        hero = html[html.index('<section class="lu-hero"'):html.index('<div class="lu-body">')]
        self.assertNotIn('lu-hero-badge', hero)
        self.assertNotIn('has-badge', hero)
