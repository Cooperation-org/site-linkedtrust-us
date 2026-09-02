"""LevelUp workshop registration: /levelup/ form, pricing tiers, access codes,
Stripe handoff, emails, and the thanks page."""
from django.core import mail
from django.test import TestCase, override_settings

from .forms import LevelUpRegistrationForm
from .models import LevelUpAccessCode, LevelUpRegistration


def payload(**over):
    base = {
        'name': 'Ada Example',
        'email': 'ada@example.org',
        'organization': 'Ada Labs',
        'link': 'https://adalabs.example',
        'help_with': ['deploy', 'scale'],
        'goal': 'Get the app live on a real domain.',
        'wants_checkin': 'on',
        'tier': 'free_small',
        'code': '',
        'company_fax': '',
    }
    base.update(over)
    return base


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
                   LEVELUP_STRIPE_PAYMENT_LINK='', LEVELUP_NOTIFY_EMAIL='team@example.org')
class LevelUpPageTests(TestCase):
    def test_page_renders_with_form(self):
        r = self.client.get('/levelup/')
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Save your seat')
        self.assertContains(r, 'name="help_with"')
        self.assertContains(r, 'September 9')

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
        self.assertIn('$100', mail.outbox[1].body)
        r = self.client.get('/levelup/thanks/')
        self.assertContains(r, 'payment link')

    @override_settings(LEVELUP_STRIPE_PAYMENT_LINK='https://buy.stripe.com/test_abc')
    def test_paid_with_stripe_redirects_to_payment_link(self):
        r = self.client.post('/levelup/', payload(tier='paid'))
        reg = LevelUpRegistration.objects.get()
        self.assertEqual(r.status_code, 302)
        self.assertTrue(r['Location'].startswith('https://buy.stripe.com/test_abc?'))
        self.assertIn('prefilled_email=ada%40example.org', r['Location'])
        self.assertIn(f'client_reference_id=levelup-{reg.pk}', r['Location'])
        self.assertEqual(reg.payment_status, 'pending')

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

    def test_requires_at_least_one_help_choice(self):
        r = self.client.post('/levelup/', payload(help_with=[]))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Pick at least one')
        self.assertEqual(LevelUpRegistration.objects.count(), 0)

    def test_required_fields_and_errors_marked(self):
        r = self.client.post('/levelup/', payload(name='', email='not-an-email', goal=''))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'lu-field has-error', count=3)
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

    def test_sitemap_lists_levelup(self):
        r = self.client.get('/sitemap-pages.xml')
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, '/levelup/')
