"""LinkedTrust SSO: the start redirect, callback login of an existing staff user,
and the security guarantees (unknown email is turned away and never provisioned,
bad state is rejected without any token exchange). sqlite, IdP calls mocked."""
from unittest.mock import patch
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model

User = get_user_model()


@override_settings(LINKEDTRUST_CLIENT_ID="lt_test", LINKEDTRUST_CLIENT_SECRET="secret",
                   LINKEDTRUST_URL="https://live.linkedtrust.us")
class LtAuthTests(TestCase):
    def test_start_redirects_to_idp_with_state(self):
        r = self.client.get("/auth/linkedtrust/start/?next=/console/")
        self.assertEqual(r.status_code, 302)
        self.assertIn("live.linkedtrust.us/oauth/authorize", r["Location"])
        self.assertIn("state=", r["Location"])
        self.assertIn("lt_oauth_state", self.client.session)

    def test_callback_logs_in_existing_staff(self):
        User.objects.create_user("amos", email="amos@linkedtrust.us", password="x", is_staff=True)
        s = self.client.session
        s["lt_oauth_state"] = "st"; s["lt_post_login_next"] = "/console/"; s.save()
        with patch("website.ltauth._post_form", return_value={"access_token": "at"}), \
             patch("website.ltauth._get_json", return_value={"email": "amos@linkedtrust.us"}):
            r = self.client.get("/auth/linkedtrust/callback/?state=st&code=c")
        self.assertEqual(r.status_code, 302)
        self.assertEqual(r["Location"], "/console/")
        self.assertIn("_auth_user_id", self.client.session)

    def test_callback_unknown_email_denied_and_not_created(self):
        s = self.client.session; s["lt_oauth_state"] = "st"; s.save()
        with patch("website.ltauth._post_form", return_value={"access_token": "at"}), \
             patch("website.ltauth._get_json", return_value={"email": "stranger@nowhere.com"}):
            r = self.client.get("/auth/linkedtrust/callback/?state=st&code=c")
        self.assertEqual(r.status_code, 302)
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertFalse(User.objects.filter(email="stranger@nowhere.com").exists())

    def test_callback_bad_state_does_no_token_exchange(self):
        s = self.client.session; s["lt_oauth_state"] = "st"; s.save()
        with patch("website.ltauth._post_form") as pf:
            r = self.client.get("/auth/linkedtrust/callback/?state=WRONG&code=c")
        self.assertEqual(r.status_code, 302)
        pf.assert_not_called()

    def test_non_staff_email_match_cannot_reach_console(self):
        # a real person who is matched but not staff must not get console access
        User.objects.create_user("intern", email="intern@x.com", password="x", is_staff=False)
        s = self.client.session; s["lt_oauth_state"] = "st"; s.save()
        with patch("website.ltauth._post_form", return_value={"access_token": "at"}), \
             patch("website.ltauth._get_json", return_value={"email": "intern@x.com"}):
            self.client.get("/auth/linkedtrust/callback/?state=st&code=c")
        r = self.client.get("/console/")
        self.assertContains(r, "does not have console access")  # no_access page

    def test_console_anonymous_shows_sso_button(self):
        r = self.client.get("/console/")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Sign in with LinkedTrust")
