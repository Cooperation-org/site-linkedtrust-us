"""Odoo CRM compose: not-connected by default, parses leads when configured,
degrades to empty on any Odoo failure, and the endpoint is staff-gated. sqlite,
Odoo mocked (no live XML-RPC)."""
from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from website import crm


class CrmModuleTests(TestCase):
    @override_settings(ODOO_URL="", ODOO_USER="", ODOO_API_KEY="")
    def test_not_configured_returns_nothing(self):
        self.assertFalse(crm.configured())
        self.assertEqual(crm.recent_leads(), [])

    @override_settings(ODOO_URL="http://odoo", ODOO_DB="linkedtrust_crm", ODOO_USER="u", ODOO_API_KEY="k")
    def test_leads_parsed(self):
        common = MagicMock(); common.authenticate.return_value = 7
        models = MagicMock()
        models.execute_kw.return_value = [{
            "id": 1, "name": "Demo request", "contact_name": "Jane", "email_from": "J@x.com",
            "user_id": [2, "Amos"], "stage_id": [3, "New"], "write_date": "2026-10-01 12:00:00"}]
        with patch("website.crm.xmlrpc.client.ServerProxy",
                   side_effect=lambda url: common if url.endswith("/common") else models):
            leads = crm.recent_leads()
        self.assertEqual(len(leads), 1)
        self.assertEqual(leads[0]["name"], "Jane")
        self.assertEqual(leads[0]["owner"], "Amos")
        self.assertEqual(leads[0]["stage"], "New")
        self.assertEqual(leads[0]["updated"], "2026-10-01")

    @override_settings(ODOO_URL="http://odoo", ODOO_USER="u", ODOO_API_KEY="k")
    def test_degrades_on_error(self):
        with patch("website.crm.xmlrpc.client.ServerProxy", side_effect=Exception("boom")):
            self.assertEqual(crm.recent_leads(), [])


class CrmEndpointTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user("g", password="x", is_staff=True)

    def test_requires_staff(self):
        self.assertEqual(self.client.get("/console/crm/").status_code, 302)

    @override_settings(ODOO_URL="", ODOO_USER="", ODOO_API_KEY="")
    def test_not_configured_payload(self):
        self.client.force_login(self.staff)
        d = self.client.get("/console/crm/").json()
        self.assertFalse(d["configured"])
        self.assertEqual(d["leads"], [])

    def test_returns_leads(self):
        self.client.force_login(self.staff)
        with patch("website.crm.configured", return_value=True), \
             patch("website.crm.recent_leads", return_value=[{"id": 1, "name": "Jane",
                   "email": "j@x.com", "owner": "Amos", "stage": "New", "updated": "2026-10-01", "title": "x"}]):
            d = self.client.get("/console/crm/").json()
        self.assertTrue(d["configured"])
        self.assertEqual(d["leads"][0]["name"], "Jane")
