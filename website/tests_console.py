"""Offline proof for the new admin console: staff gate, page render, inbox
filtering, on-demand draft generation (template fallback), and the write
actions. Runs on sqlite, touches no prod data."""
import os, json
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.management import call_command
from website.models import ContactInquiry


class ConsoleTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user("golda", password="x", is_staff=True)
        self.lead = ContactInquiry.objects.create(
            email="amr@example.com", name="Amr", subject="consulting",
            message="AI Knowledge Assistant demo request for customer support", verdict="lead")
        self.spam = ContactInquiry.objects.create(
            email="bot@x.ru", subject="consulting", message="cheap SEO backlinks",
            verdict="spam", archived=True)
        os.environ.pop("MINIMAX_API_KEY", None)  # force template fallback

    def test_requires_staff(self):
        self.assertEqual(self.client.get("/console/").status_code, 302)  # anon -> login

    def test_page_renders_inbox_without_spam(self):
        self.client.force_login(self.staff)
        r = self.client.get("/console/")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "paneldata")
        self.assertContains(r, "amr@example.com")       # real lead in inbox
        self.assertNotContains(r, "bot@x.ru")           # archived spam excluded

    def test_draft_endpoint_template_fallback(self):
        self.client.force_login(self.staff)
        r = self.client.post(f"/console/draft/{self.lead.pk}/")
        self.assertEqual(r.status_code, 200)
        d = r.json()
        self.assertEqual(d["engine"], "template")
        self.assertIn("SCHEDULE_LINK", d["body"])
        self.assertNotIn("—", d["body"])           # no em dash

    def test_action_archive_and_contacted(self):
        self.client.force_login(self.staff)
        r = self.client.post("/console/action/", data=json.dumps({"action": "archive", "ids": [self.lead.pk]}),
                             content_type="application/json")
        self.assertEqual(r.status_code, 200)
        self.lead.refresh_from_db()
        self.assertTrue(self.lead.archived)

        self.client.post("/console/action/", data=json.dumps({"action": "contacted", "ids": [self.lead.pk]}),
                        content_type="application/json")
        self.lead.refresh_from_db()
        self.assertTrue(self.lead.contacted)
        self.assertEqual(self.lead.contacted_by, "golda")

    def test_bad_action_rejected(self):
        self.client.force_login(self.staff)
        r = self.client.post("/console/action/", data=json.dumps({"action": "delete", "ids": [1]}),
                             content_type="application/json")
        self.assertEqual(r.status_code, 400)

    def test_seed_command_runs(self):
        # The shipped map is keyed by prod ids; on this fresh db they are missing,
        # so the command should skip them cleanly and not error.
        call_command("seed_inquiry_triage", "--dry-run")
