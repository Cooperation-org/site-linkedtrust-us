from unittest import mock

from django.test import TestCase

from .models import ContactInquiry

PAGE = '/storykit/'


class StoryKitPageTests(TestCase):
    def test_page_links_to_app_and_samples(self):
        r = self.client.get(PAGE)
        self.assertContains(r, 'Start a free trial')
        self.assertContains(r, 'https://demos.linkedtrust.us/storykit/')
        self.assertContains(r, 'https://demos.linkedtrust.us/storykit/demo/')

    def test_email_saved_then_thanks_even_if_mail_fails(self):
        with mock.patch('website.views.EmailMessage.send', side_effect=OSError('smtp down')):
            r = self.client.post(PAGE, {'email': 'a@example.org'})
        self.assertEqual(r.status_code, 302)
        self.assertTrue(r['Location'].endswith('/storykit/?subscribed=1#updates'))
        i = ContactInquiry.objects.get()
        self.assertEqual((i.email, i.subject), ('a@example.org', 'storykit'))
        self.assertContains(self.client.get(PAGE + '?subscribed=1'), "You're on the list.")

    def test_honeypot_saves_nothing(self):
        self.client.post(PAGE, {'email': 'bot@example.org', 'website': 'x'})
        self.assertFalse(ContactInquiry.objects.exists())

    def test_bad_email_kept_in_box_with_a_line(self):
        r = self.client.post(PAGE, {'email': 'nope'})
        self.assertContains(r, "doesn't look right")
        self.assertFalse(ContactInquiry.objects.exists())
