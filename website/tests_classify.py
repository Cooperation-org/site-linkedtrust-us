"""Proof for spam detection: the rules catch junk and never flag the real leads,
the post_save signal auto-archives junk on arrival, and the console classify
endpoint clears the unreviewed backlog. sqlite, no prod data."""
import os
from django.test import TestCase
from django.contrib.auth.models import User
from website.classify import spam_by_rules
from website.models import ContactInquiry

SPAM_SAMPLES = [
    ("HarryKab", "Your 2026 Rolls-Royce Phantom for $15,000 https://telegra.ph/x"),
    ("NARYTHY1235521NEHTYHYHTR", "MEKYUJTYJ1235521MAMYJRTH"),
    ("Ziva", "Would you take a guest post on vehicle shipping for your readers?"),
    ("Cleopatra", "5,000+ new & upcoming slot games available Try Free"),
    ("Katie", "are you currently spending heavily on paid ads, lead lists, or outreach software?"),
    ("Robertvom", "Hi, I wanted to know your price."),
    ("Robertvom", "Salut, ech wollt Äre Präis wëssen."),
    ("Robertvom", "Γεια σου, ήθελα να μάθω την τιμή σας."),
    ("Elizabeth", "I would like more information. Please contact me by email — contact linkedtrust."),
    ("Chelsey", "Restore any site from Web Archives (Wayback Machine)."),
]
REAL_SAMPLES = [
    ("amr", "AI Knowledge Assistant demo request. Company: venture scalor. Use case: Customer Support"),
    ("David Randall Soley", "What is your value prop and who is responsible for sales?"),
    ("Madhup Verma", "We are looking for talented software engineers and manufacturing talent for our clients."),
    ("Magnus Muller", "A few people building civic tech and credential platforms led me to LinkedTrust. Most teams lose time to manual work."),
    ("Omar Ahmed", "I am reaching out to express my interest in the Backend Intern position. I am an ITI graduate."),
    ("Hannah Melotto", "Hey! Do you have any use for a freelance writer? I have nearly a decade of experience."),
    # real applicant who links a portfolio/GitHub/LinkedIn: must NOT be flagged
    ("Tiancheng Gao", "I'm applying for the internship cohort with a focus on QA or Python/backend. "
     "PageNote: https://apps.apple.com/au/app/pagenote/id6803788070 "
     "GitHub: https://github.com/TerryG907 LinkedIn: https://www.linkedin.com/in/tiancheng-gao/"),
]


class RuleTests(TestCase):
    def test_spam_samples_flagged(self):
        for name, msg in SPAM_SAMPLES:
            self.assertTrue(spam_by_rules(name, msg), f"missed spam: {name} / {msg[:40]}")

    def test_real_people_not_flagged(self):
        for name, msg in REAL_SAMPLES:
            self.assertFalse(spam_by_rules(name, msg), f"false positive: {name} / {msg[:40]}")


class SignalTests(TestCase):
    def test_spam_auto_archived_on_create(self):
        i = ContactInquiry.objects.create(email="x@y.ru", name="HarryKab",
                                          message="Rolls-Royce Phantom https://telegra.ph/x")
        i.refresh_from_db()
        self.assertTrue(i.archived)
        self.assertEqual(i.verdict, "spam")

    def test_real_left_alone_on_create(self):
        i = ContactInquiry.objects.create(email="amr@example.com", name="amr",
                                          message="AI Knowledge Assistant demo request for customer support")
        i.refresh_from_db()
        self.assertFalse(i.archived)
        self.assertEqual(i.verdict, "")


class ClassifyEndpointTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user("golda", password="x", is_staff=True)
        os.environ.pop("MINIMAX_API_KEY", None)
        # created via objects.create so the signal already archives obvious spam;
        # force these back to unreviewed to test the button path explicitly.
        self.spam = ContactInquiry.objects.create(email="s@x.com", name="SEO Pro", message="cheap backlinks and guest post")
        self.real = ContactInquiry.objects.create(email="lead@co.com", name="Jane", message="We want to hire your team for a project build.")
        ContactInquiry.objects.filter(pk__in=[self.spam.pk, self.real.pk]).update(verdict="", archived=False)

    def test_button_archives_spam_keeps_real(self):
        self.client.force_login(self.staff)
        r = self.client.post("/console/classify/")
        self.assertEqual(r.status_code, 200)
        self.spam.refresh_from_db(); self.real.refresh_from_db()
        self.assertTrue(self.spam.archived)
        self.assertFalse(self.real.archived)   # no key -> uncertain stays unreviewed
