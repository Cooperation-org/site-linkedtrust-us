"""Offline proof for the inquiry cleanup: migration 0013 applies, the admin
actions change state, and draft generation works with the template fallback.
Runs on sqlite (manage.py test), so no prod DB is touched."""
import os
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware

from website.models import ContactInquiry
from website import admin as site_admin
from website import outreach


def _request():
    req = RequestFactory().post('/admin/website/contactinquiry/')
    SessionMiddleware(lambda r: None).process_request(req)
    req.session.save()
    setattr(req, '_messages', FallbackStorage(req))
    req.user, _ = User.objects.get_or_create(username='golda')
    return req


class InquiryTrackingTests(TestCase):
    def setUp(self):
        self.spam = ContactInquiry.objects.create(email='bot@x.ru', name='Bot', subject='consulting', message='SEO backlinks cheap')
        self.lead = ContactInquiry.objects.create(email='amr@example.com', name='Amr', subject='consulting', message='AI Knowledge Assistant demo request for customer support')

    def test_new_fields_exist_and_default(self):
        self.assertFalse(self.lead.archived)
        self.assertFalse(self.lead.contacted)
        self.assertIsNone(self.lead.contacted_at)
        self.assertEqual(self.lead.contacted_by, '')

    def test_archive_action(self):
        ma = site_admin.ContactInquiryAdmin(ContactInquiry, site_admin.admin_site)
        site_admin.archive_inquiries(ma, _request(), ContactInquiry.objects.filter(pk=self.spam.pk))
        self.spam.refresh_from_db()
        self.assertTrue(self.spam.archived)

    def test_mark_contacted_stamps_user_and_time(self):
        ma = site_admin.ContactInquiryAdmin(ContactInquiry, site_admin.admin_site)
        site_admin.mark_contacted(ma, _request(), ContactInquiry.objects.filter(pk=self.lead.pk))
        self.lead.refresh_from_db()
        self.assertTrue(self.lead.contacted)
        self.assertEqual(self.lead.contacted_by, 'golda')
        self.assertIsNotNone(self.lead.contacted_at)

    def test_archived_filter_defaults_to_active(self):
        self.spam.archived = True
        self.spam.save()
        f = site_admin.ArchivedFilter(_request(), {}, ContactInquiry, site_admin.ContactInquiryAdmin)
        qs = f.queryset(_request(), ContactInquiry.objects.all())
        self.assertIn(self.lead, qs)
        self.assertNotIn(self.spam, qs)

    def test_draft_template_fallback_clean(self):
        # no API key -> template engine, must still produce a clean draft
        os.environ.pop('MINIMAX_API_KEY', None)
        subject, body, resid, engine = outreach.draft_for(self.lead)
        self.assertEqual(engine, 'template')
        self.assertNotIn('—', body)          # no em dash
        self.assertIn(outreach.CAL_TOKEN, body)   # calendar placeholder present
        self.assertIn('Amr', body)

    def test_build_drafts_html_renders_recipient(self):
        os.environ.pop('MINIMAX_API_KEY', None)
        html = outreach.build_drafts_html([self.lead])
        self.assertIn('amr@example.com', html)
        self.assertIn('Bcc', html)
        self.assertNotIn('—', html)
