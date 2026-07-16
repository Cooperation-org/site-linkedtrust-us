"""Tests for the earnedgov GovKit invite flow (magic links).

GovKit and LinkedTrust are mocked — these tests cover the doorway's side of
the contract in govkit/scratch.md (2026-07-13): resolve by opaque code, render
per invite status, publish the claim, report back, hand off to accept_url.
"""
from unittest.mock import patch

import requests
from django.test import TestCase, override_settings

from .earnedgov_govkit import GovKitUnavailable, resolve_invite, report_committed
from .models import EarnedgovCommitment

GOVKIT_SETTINGS = dict(
    GOVKIT_BASE_URL='https://govkit.test',
    GOVKIT_ORG_SLUG='earnedgov',
    GOVKIT_S2S_TOKEN='test-s2s-token',
)

INVITE = {
    'code': 'AB3xK9dQ',
    'name': 'Ada Example',
    'email': 'ada@example.org',
    'image_url': '',
    'link': 'https://linkedin.com/in/ada',
    'audience': 'mentor',
    'drafted_statement': 'I am committing to mentor teams in the alpha cohort.',
    'drafted_social_post': '',
    'status': 'created',
    'expires_at': '2026-08-12',
    'accept_url': 'https://govkit.test/invites/AB3xK9dQ/accept/',
    'committed_claim_id': None,
}


class FakeResponse:
    def __init__(self, status_code, data=None):
        self.status_code = status_code
        self._data = data or {}

    def json(self):
        return self._data


@override_settings(**GOVKIT_SETTINGS)
class GovKitClientTests(TestCase):
    @patch('website.earnedgov_govkit.requests.get')
    def test_resolve_ok(self, get):
        get.return_value = FakeResponse(200, dict(INVITE))
        invite = resolve_invite('AB3xK9dQ')
        self.assertEqual(invite['name'], 'Ada Example')
        get.assert_called_once()
        url = get.call_args[0][0]
        self.assertEqual(url, 'https://govkit.test/api/v1/orgs/earnedgov/invites/AB3xK9dQ/')
        self.assertEqual(
            get.call_args[1]['headers']['Authorization'], 'Bearer test-s2s-token')

    @patch('website.earnedgov_govkit.requests.get')
    def test_resolve_audience_falls_back_to_role(self, get):
        payload = dict(INVITE)
        del payload['audience']
        payload['role'] = 'advisor'
        get.return_value = FakeResponse(200, payload)
        self.assertEqual(resolve_invite('x')['audience'], 'advisor')

    @patch('website.earnedgov_govkit.requests.get')
    def test_resolve_unknown_code_is_none(self, get):
        get.return_value = FakeResponse(404)
        self.assertIsNone(resolve_invite('nope'))

    @patch('website.earnedgov_govkit.requests.get')
    def test_resolve_auth_misconfig_is_unavailable_not_invalid(self, get):
        get.return_value = FakeResponse(401)
        with self.assertRaises(GovKitUnavailable):
            resolve_invite('AB3xK9dQ')

    @patch('website.earnedgov_govkit.requests.get')
    def test_resolve_5xx_raises_unavailable(self, get):
        get.return_value = FakeResponse(500)
        with self.assertRaises(GovKitUnavailable):
            resolve_invite('AB3xK9dQ')

    @patch('website.earnedgov_govkit.requests.get')
    def test_resolve_network_error_raises_unavailable(self, get):
        get.side_effect = requests.ConnectionError()
        with self.assertRaises(GovKitUnavailable):
            resolve_invite('AB3xK9dQ')

    @override_settings(GOVKIT_S2S_TOKEN='')
    def test_resolve_unconfigured_is_none(self):
        self.assertIsNone(resolve_invite('AB3xK9dQ'))

    @patch('website.earnedgov_govkit.requests.post')
    def test_report_committed_posts_contract_payload(self, post):
        post.return_value = FakeResponse(200)
        ok = report_committed('AB3xK9dQ', claim_id=777, statement='words',
                              video_url='https://live.linkedtrust.us/v.webm')
        self.assertTrue(ok)
        url = post.call_args[0][0]
        self.assertEqual(
            url, 'https://govkit.test/api/v1/orgs/earnedgov/invites/AB3xK9dQ/committed/')
        self.assertEqual(post.call_args[1]['json'], {
            'claim_id': 777,
            'statement_as_published': 'words',
            'video_url': 'https://live.linkedtrust.us/v.webm',
        })

    @patch('website.earnedgov_govkit.requests.post')
    def test_report_committed_failure_returns_false(self, post):
        post.side_effect = requests.ConnectionError()
        self.assertFalse(report_committed('AB3xK9dQ', claim_id=777, statement='w'))


@override_settings(**GOVKIT_SETTINGS)
class InvitePageTests(TestCase):
    URL = '/earnedgov/i/AB3xK9dQ/'

    @patch('website.earnedgov_govkit.resolve_invite')
    def test_form_greets_and_prefills(self, resolve):
        resolve.return_value = dict(INVITE)
        r = self.client.get(self.URL)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Ada Example, you\'re invited')
        # Per-audience language (2026-07-15 pin): mentors join, nobody "commits".
        self.assertContains(r, 'Join the Earned Governance Accelerator as a mentor.')
        self.assertContains(r, 'Join as a mentor')
        self.assertContains(r, 'I am committing to mentor teams in the alpha cohort.')
        self.assertContains(r, 'https://linkedin.com/in/ada')

    @patch('website.earnedgov_govkit.resolve_invite')
    def test_founder_invite_says_share_my_launch(self, resolve):
        resolve.return_value = {**INVITE, 'audience': 'founder'}
        r = self.client.get(self.URL)
        self.assertContains(r, 'Share my launch')
        self.assertContains(r, 'Share your launch in the Earned Governance Accelerator.')

    @patch('website.earnedgov_govkit.resolve_invite')
    def test_empty_draft_gets_factual_placeholder(self, resolve):
        resolve.return_value = {**INVITE, 'drafted_statement': ''}
        r = self.client.get(self.URL)
        self.assertContains(
            r, "I&#x27;m joining the Earned Governance Accelerator as a mentor.")

    @patch('website.earnedgov_govkit.resolve_invite')
    def test_invalid_code_404s_kindly(self, resolve):
        resolve.return_value = None
        r = self.client.get(self.URL)
        self.assertEqual(r.status_code, 404)
        self.assertContains(r, "isn't valid", status_code=404)

    @patch('website.earnedgov_govkit.resolve_invite')
    def test_revoked_treated_as_invalid(self, resolve):
        resolve.return_value = {**INVITE, 'status': 'revoked'}
        self.assertEqual(self.client.get(self.URL).status_code, 404)

    @patch('website.earnedgov_govkit.resolve_invite')
    def test_govkit_down_says_try_again(self, resolve):
        resolve.side_effect = GovKitUnavailable()
        r = self.client.get(self.URL)
        self.assertEqual(r.status_code, 503)
        self.assertContains(r, 'try again in a minute', status_code=503)

    @patch('website.earnedgov_govkit.resolve_invite')
    def test_accepted_shows_dashboard_link(self, resolve):
        resolve.return_value = {**INVITE, 'status': 'accepted'}
        r = self.client.get(self.URL)
        self.assertContains(r, "You're already in")
        self.assertContains(r, 'https://govkit.test')

    @patch('website.earnedgov_govkit.resolve_invite')
    def test_committed_shows_accept_url_and_wall_links(self, resolve):
        resolve.return_value = {**INVITE, 'status': 'committed', 'committed_claim_id': 777}
        r = self.client.get(self.URL)
        self.assertContains(r, INVITE['accept_url'])
        self.assertContains(r, 'Continue to your dashboard')
        self.assertContains(r, '/earnedgov/?committed=777#committed')

    @patch('website.earnedgov_govkit.report_committed')
    @patch('website.earnedgov_claims.create_commitment')
    @patch('website.earnedgov_govkit.resolve_invite')
    def test_commit_publishes_approves_reports_and_redirects(self, resolve, create, report):
        resolve.return_value = dict(INVITE)
        create.return_value = {'id': 777}
        r = self.client.post(self.URL, {
            'name': 'Ada Example',
            'link': 'https://linkedin.com/in/ada',
            'statement': 'My own words.',
            'video_url': '',
        })
        self.assertRedirects(r, f'{self.URL}?committed=777',
                             fetch_redirect_response=False)
        create.assert_called_once()
        kwargs = create.call_args[1]
        self.assertEqual(kwargs['role'], 'mentor')
        self.assertTrue(kwargs['self_attested'])
        ledger = EarnedgovCommitment.objects.get(claim_id=777)
        self.assertEqual(ledger.status, 'approved')
        self.assertTrue(ledger.invited)
        report.assert_called_once_with(
            'AB3xK9dQ', claim_id=777, statement='My own words.', video_url=None)

    @patch('website.earnedgov_govkit.report_committed')
    @patch('website.earnedgov_claims.create_commitment')
    @patch('website.earnedgov_govkit.resolve_invite')
    def test_commit_requires_statement(self, resolve, create, report):
        resolve.return_value = dict(INVITE)
        r = self.client.post(self.URL, {
            'name': 'Ada Example', 'link': '', 'statement': '', 'video_url': '',
        })
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'needs words')
        create.assert_not_called()
        report.assert_not_called()


@override_settings(**GOVKIT_SETTINGS)
class HostRoutingTests(TestCase):
    """workers.vc serves the accelerator at its root (board: domain rev 3)."""

    @patch('website.earnedgov_claims.fetch_commitments')
    def test_workersvc_root_is_the_accelerator_landing(self, wall):
        wall.return_value = {'groups': [], 'count': 0}
        r = self.client.get('/', HTTP_HOST='workers.vc')
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Earned Governance')

    @patch('website.earnedgov_govkit.resolve_invite')
    def test_workersvc_invite_path_is_at_root(self, resolve):
        resolve.return_value = dict(INVITE)
        r = self.client.get('/i/AB3xK9dQ/', HTTP_HOST='workers.vc')
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Ada Example, you're invited")

    def test_workersvc_does_not_serve_the_main_site(self):
        r = self.client.get('/about/', HTTP_HOST='workers.vc')
        self.assertEqual(r.status_code, 404)

    @override_settings(WORKERSVC_LIVE=True)
    def test_earnedgov_paths_redirect_once_live(self):
        r = self.client.get('/earnedgov/?committed=5', HTTP_HOST='linkedtrust.us')
        self.assertEqual(r.status_code, 301)
        # workers.vc root is the VC; the old landing is the accelerator page.
        self.assertEqual(r['Location'], 'https://workers.vc/accelerator/?committed=5')
        r = self.client.get('/earnedgov/commit/', HTTP_HOST='linkedtrust.us')
        self.assertEqual(r['Location'], 'https://workers.vc/commit/')
        r = self.client.get('/earnedgov/i/AB3xK9dQ/', HTTP_HOST='linkedtrust.us')
        self.assertEqual(r['Location'], 'https://workers.vc/i/AB3xK9dQ/')

    def test_earnedgov_paths_serve_normally_before_live(self):
        r = self.client.get('/earnedgov/commit/', HTTP_HOST='linkedtrust.us')
        self.assertEqual(r.status_code, 200)


class WalkUpModerationTests(TestCase):
    @patch('website.earnedgov_claims.create_commitment')
    def test_walkup_commit_is_held_pending(self, create):
        create.return_value = {'id': 888}
        r = self.client.post('/earnedgov/commit/', {
            'mode': 'self',
            'name': 'Walk Up',
            'link': '',
            'role': 'supporter',
            'statement': 'I support this.',
            'voucher_name': '', 'voucher_link': '', 'video_url': '',
        })
        self.assertEqual(r.status_code, 302)
        self.assertIn('pending=1', r['Location'])
        ledger = EarnedgovCommitment.objects.get(claim_id=888)
        self.assertEqual(ledger.status, 'pending')
        self.assertFalse(ledger.invited)
