"""Attestations as LinkedClaims: off by default (no outward call), publishes a
'contacted' claim when enabled, degrades on failure, and the console action caches
the returned claim id. sqlite, HTTP mocked, nothing hits the live trust graph."""
from unittest.mock import patch, MagicMock
import json
from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from website import linkedclaims
from website.models import ContactInquiry


def _resp(claim_id=123):
    m = MagicMock()
    m.raise_for_status.return_value = None
    m.json.return_value = {"claim": {"id": claim_id}}
    return m


class PublishTests(TestCase):
    def setUp(self):
        self.inq = ContactInquiry.objects.create(email="lead@co.com", name="Jane", verdict="lead")

    def test_disabled_by_default_no_call(self):
        with patch("website.linkedclaims.requests.post") as post:
            self.assertIsNone(linkedclaims.publish_contacted(self.inq, "amos"))
            post.assert_not_called()

    @override_settings(CONSOLE_PUBLISH_CLAIMS=True)
    def test_enabled_publishes(self):
        with patch("website.linkedclaims.requests.post", return_value=_resp(777)) as post:
            cid = linkedclaims.publish_contacted(self.inq, "amos")
        self.assertEqual(cid, "777")
        url = post.call_args[0][0]
        self.assertTrue(url.endswith("/api/claims"))
        body = post.call_args.kwargs["json"]
        self.assertEqual(body["subject"], "mailto:lead@co.com")
        self.assertEqual(body["claim"], "contacted")

    @override_settings(CONSOLE_PUBLISH_CLAIMS=True)
    def test_degrades_on_error(self):
        with patch("website.linkedclaims.requests.post", side_effect=Exception("boom")):
            self.assertIsNone(linkedclaims.publish_contacted(self.inq, "amos"))

    @override_settings(CONSOLE_PUBLISH_CLAIMS=True)
    def test_no_email_no_publish(self):
        inq = ContactInquiry.objects.create(email="", name="X", verdict="lead")
        with patch("website.linkedclaims.requests.post") as post:
            self.assertIsNone(linkedclaims.publish_contacted(inq, "amos"))
            post.assert_not_called()


class ContactedActionTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user("golda", password="x", is_staff=True)
        self.inq = ContactInquiry.objects.create(email="lead@co.com", name="Jane", verdict="lead")
        self.client.force_login(self.staff)

    def test_contacted_without_publishing(self):
        r = self.client.post("/console/action/", data=json.dumps({"action": "contacted", "ids": [self.inq.pk]}),
                             content_type="application/json")
        self.assertEqual(r.status_code, 200)
        self.inq.refresh_from_db()
        self.assertTrue(self.inq.contacted)
        self.assertEqual(self.inq.contacted_by, "golda")
        self.assertEqual(self.inq.contacted_claim_id, "")

    @override_settings(CONSOLE_PUBLISH_CLAIMS=True)
    def test_contacted_caches_claim_id(self):
        with patch("website.linkedclaims.requests.post", return_value=_resp(999)):
            self.client.post("/console/action/", data=json.dumps({"action": "contacted", "ids": [self.inq.pk]}),
                            content_type="application/json")
        self.inq.refresh_from_db()
        self.assertTrue(self.inq.contacted)
        self.assertEqual(self.inq.contacted_claim_id, "999")
