"""Taiga compose: not-connected by default, parses user stories when configured,
degrades to empty on failure, staff-gated endpoint. sqlite, HTTP mocked."""
import json
from unittest.mock import patch
from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from website import taiga


class _FakeResp:
    def __init__(self, payload): self._p = payload
    def read(self): return json.dumps(self._p).encode()
    def __enter__(self): return self
    def __exit__(self, *a): return False


def _fake_resp(payload):
    return _FakeResp(payload)


class TaigaModuleTests(TestCase):
    @override_settings(TAIGA_URL="https://taiga.linkedtrust.us", TAIGA_TOKEN="")
    def test_not_configured(self):
        self.assertFalse(taiga.configured())
        self.assertEqual(taiga.recent_items(), [])

    @override_settings(TAIGA_URL="https://taiga.x", TAIGA_TOKEN="tok")
    def test_items_parsed(self):
        story = [{"id": 5, "ref": 42, "subject": "Build the thing",
                  "status_extra_info": {"name": "In progress"},
                  "assigned_to_extra_info": {"full_name_display": "Amos"},
                  "project_extra_info": {"name": "Console"},
                  "modified_date": "2026-10-06T09:00:00+0000"}]
        with patch("website.taiga.urlopen", side_effect=lambda *a, **k: _fake_resp(story)):
            items = taiga.recent_items()
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["subject"], "Build the thing")
        self.assertEqual(items[0]["status"], "In progress")
        self.assertEqual(items[0]["assignee"], "Amos")
        self.assertEqual(items[0]["project"], "Console")
        self.assertEqual(items[0]["updated"], "2026-10-06")

    @override_settings(TAIGA_URL="https://taiga.x", TAIGA_TOKEN="tok")
    def test_degrades_on_error(self):
        with patch("website.taiga.urlopen", side_effect=Exception("boom")):
            self.assertEqual(taiga.recent_items(), [])


class TaigaEndpointTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user("g", password="x", is_staff=True)

    def test_requires_staff(self):
        self.assertEqual(self.client.get("/console/taiga/").status_code, 302)

    @override_settings(TAIGA_TOKEN="")
    def test_not_configured_payload(self):
        self.client.force_login(self.staff)
        d = self.client.get("/console/taiga/").json()
        self.assertFalse(d["configured"])
        self.assertEqual(d["items"], [])

    def test_returns_items(self):
        self.client.force_login(self.staff)
        with patch("website.taiga.configured", return_value=True), \
             patch("website.taiga.recent_items", return_value=[{"id": 5, "ref": 42,
                   "subject": "x", "status": "New", "assignee": "Amos", "project": "P", "updated": "2026-10-06"}]):
            d = self.client.get("/console/taiga/").json()
        self.assertTrue(d["configured"])
        self.assertEqual(d["items"][0]["subject"], "x")
