"""
Seed the database with initial portfolio projects, services, and sample testimonials.
Run with: python manage.py seed_portfolio
Run with --clear to wipe existing data first: python manage.py seed_portfolio --clear
"""
from django.core.management.base import BaseCommand
from website.models import PortfolioProject, CaseStudy, Testimonial, ServicePackage


PROJECTS = [
    # --- Client Work ---
    {
        'title': 'StreetWell',
        'client_name': 'Rising LLC / Construction Cooperatives',
        'short_description': 'Double-entry bookkeeping platform for construction cooperatives.',
        'full_description': (
            'StreetWell is a financial management platform built for construction worker cooperatives. '
            'It provides double-entry bookkeeping, job costing, payroll tracking, and cooperative-specific '
            'features like profit-sharing calculations and member equity tracking.\n\n'
            'The platform replaces spreadsheet-based accounting with a purpose-built system that understands '
            'how cooperatives work — shared ownership, democratic governance, and equitable distribution.'
        ),
        'tech_tags': 'React, PostgreSQL, Node.js, Plaid API',
        'category': 'client_work',
        'featured': True,
        'sort_order': 1,
        'demo_url': '',
        'repo_url': '',
    },
    {
        'title': 'AZ-Sunshine',
        'client_name': 'Ben Armentrout / AZ Political Transparency',
        'short_description': 'Political transparency tool tracking Arizona election spending.',
        'full_description': (
            'AZ-Sunshine makes Arizona political spending transparent and searchable. It aggregates '
            'campaign finance data from the Arizona Secretary of State and presents it in a clean, '
            'searchable interface so voters can see who funds their representatives.\n\n'
            'Features include candidate profiles, donor search, spending breakdowns by category, '
            'and timeline views of campaign finance activity. The goal is simple: sunlight as disinfectant.'
        ),
        'tech_tags': 'Django, React, PostgreSQL, Python, Scrapy',
        'category': 'client_work',
        'featured': True,
        'sort_order': 2,
        'demo_url': '',
        'repo_url': 'https://github.com/Cooperation-org/az-sunshine',
    },
    {
        'title': 'Accentrics',
        'client_name': 'AZ Tender Hands Home Health',
        'short_description': 'AI-powered business automation for home health care.',
        'full_description': (
            'Accentrics automates the most time-consuming parts of running a home health agency: '
            'scheduling, compliance documentation, caregiver matching, and billing preparation.\n\n'
            'Built with FastAPI and Claude AI, the system ingests patient intake forms, matches '
            'them with qualified caregivers based on skills and availability, and generates compliant '
            'documentation. What used to take 3-4 hours of admin work per patient now takes minutes.'
        ),
        'tech_tags': 'FastAPI, Claude AI, Python, React, PostgreSQL',
        'category': 'client_work',
        'featured': True,
        'sort_order': 3,
        'demo_url': '',
        'repo_url': '',
    },
    {
        'title': 'CivicSky',
        'client_name': 'George Polisner',
        'short_description': 'Ghost CMS to Bluesky bridge with civic action cards.',
        'full_description': (
            'CivicSky bridges Ghost CMS publications to Bluesky, automatically cross-posting '
            'articles with rich civic action cards. When a journalist publishes on Ghost, CivicSky '
            'creates a Bluesky post with embedded action items — call your rep, sign a petition, '
            'attend a meeting.\n\n'
            'Built on the AT Protocol (Bluesky\'s underlying protocol), CivicSky demonstrates how '
            'decentralized social media can be used for civic engagement, not just conversation.'
        ),
        'tech_tags': 'Next.js, ATProto, Ghost API, TypeScript',
        'category': 'client_work',
        'featured': True,
        'sort_order': 4,
        'demo_url': '',
        'repo_url': 'https://github.com/Cooperation-org/civicsky',
    },
    {
        'title': 'Skills-Aware',
        'client_name': 'Skills-Aware / Workforce Development',
        'short_description': 'Endorsement workflow platform for verified professional skills.',
        'full_description': (
            'Skills-Aware is a platform for issuing and verifying professional skill endorsements. '
            'Employers, trainers, and peers can endorse specific skills with verifiable credentials '
            'that follow the Open Badges v3 standard.\n\n'
            'The workflow supports multi-party endorsement chains: a trainer certifies a skill, '
            'an employer confirms it in practice, and the credential is anchored to the LinkedTrust '
            'trust graph for independent verification.'
        ),
        'tech_tags': 'React, Node.js, Open Badges v3, LinkedTrust API',
        'category': 'client_work',
        'featured': False,
        'sort_order': 5,
        'demo_url': '',
        'repo_url': '',
    },
    {
        'title': 'GoodDollar Apps',
        'client_name': 'GoodDollar Protocol',
        'short_description': 'Community apps built on the GoodDollar UBI protocol.',
        'full_description': (
            'Built two community applications on the GoodDollar universal basic income protocol: '
            'Pesia\'s Kitchen (community meal coordination) and Global Classrooms (educational '
            'resource sharing).\n\n'
            'Both apps use GoodDollar\'s G$ token for micro-transactions, enabling communities '
            'to coordinate services and resources using blockchain-based UBI.'
        ),
        'tech_tags': 'React, GoodDollar SDK, Ethereum, Fuse Network',
        'category': 'client_work',
        'featured': False,
        'sort_order': 6,
        'demo_url': '',
        'repo_url': '',
    },

    # --- Internal Products ---
    {
        'title': 'LinkedTrust Platform',
        'client_name': 'LinkedTrust (Internal)',
        'short_description': 'Decentralized web of trust — verified claims, credentials, and endorsements.',
        'full_description': (
            'The LinkedTrust platform is our core product: a decentralized trust graph where '
            'claims, credentials, and endorsements are independently verifiable. Any claim made '
            'by one party can be attested, disputed, or endorsed by others — building a web of '
            'trust that doesn\'t depend on a single authority.\n\n'
            'The platform supports video testimonials, credential issuance (Open Badges v3), '
            'and a public API for embedding trust badges anywhere on the web. This site uses it: '
            'every testimonial badge links back to a verified claim on the trust graph.'
        ),
        'tech_tags': 'React, Node.js, PostgreSQL, DID/VC, Open Badges v3',
        'category': 'internal_product',
        'featured': False,
        'sort_order': 10,
        'demo_url': 'https://live.linkedtrust.us',
        'repo_url': 'https://github.com/Cooperation-org/LinkedTrust',
    },
    {
        'title': 'Certify',
        'client_name': 'LinkedTrust (Internal)',
        'short_description': 'Volunteer recognition and badge issuance for nonprofits.',
        'full_description': (
            'Certify helps nonprofits recognize volunteers with verifiable digital badges. '
            'Organizations can create badge templates, issue them to volunteers, and the badges '
            'are backed by the LinkedTrust trust graph.\n\n'
            'Volunteers get portable, verifiable credentials they can share with employers or '
            'other organizations — turning volunteer work into recognized professional development.'
        ),
        'tech_tags': 'React, Open Badges v3, LinkedTrust API',
        'category': 'internal_product',
        'featured': False,
        'sort_order': 11,
        'demo_url': '',
        'repo_url': '',
    },
    {
        'title': 'Talent / TalentStamp',
        'client_name': 'LinkedTrust (Internal)',
        'short_description': 'Professional credential verification for hiring and recruiting.',
        'full_description': (
            'TalentStamp is a professional credential verification tool. Job seekers can '
            'collect verified endorsements from colleagues, managers, and clients — then share '
            'a single link with recruiters showing their verified skill profile.\n\n'
            'Recruiters can filter candidates by verified skills rather than self-reported ones, '
            'dramatically reducing the noise in the hiring pipeline.'
        ),
        'tech_tags': 'React, Node.js, LinkedTrust API, PostgreSQL',
        'category': 'internal_product',
        'featured': False,
        'sort_order': 12,
        'demo_url': '',
        'repo_url': '',
    },
    {
        'title': 'Alonovo',
        'client_name': 'LinkedTrust (Internal)',
        'short_description': 'Ethical capital allocation platform for cooperative investment.',
        'full_description': (
            'Alonovo is an experimental platform for ethical capital allocation — matching '
            'investors with cooperative and social enterprises based on verified impact data '
            'rather than traditional financial metrics alone.\n\n'
            'The platform uses LinkedTrust trust graph data to provide verified impact scores '
            'alongside financial projections.'
        ),
        'tech_tags': 'React, Django, PostgreSQL',
        'category': 'internal_product',
        'featured': False,
        'sort_order': 13,
        'demo_url': '',
        'repo_url': '',
    },
    {
        'title': 'Amebo',
        'client_name': 'LinkedTrust (Internal)',
        'short_description': 'AI-powered workspace intelligence and knowledge extraction.',
        'full_description': (
            'Amebo is an AI-powered workspace tool that extracts knowledge from team conversations, '
            'documents, and project artifacts. It builds a searchable knowledge graph of decisions, '
            'action items, and institutional knowledge.\n\n'
            'Instead of losing context when team members leave or conversations scroll away, '
            'Amebo captures and organizes the collective intelligence of the team.'
        ),
        'tech_tags': 'Python, FastAPI, Claude AI, RAG, PostgreSQL',
        'category': 'internal_product',
        'featured': False,
        'sort_order': 14,
        'demo_url': '',
        'repo_url': '',
    },
    {
        'title': 'AZ Local First RAG',
        'client_name': 'Local First Arizona Foundation',
        'short_description': 'Vector search engine for Arizona local business directory.',
        'full_description': (
            'A RAG (Retrieval-Augmented Generation) search engine for Local First Arizona\'s '
            'business directory. Instead of keyword matching, users can search in natural language: '
            '"restaurants near downtown Tucson that source local ingredients" and get semantically '
            'relevant results.\n\n'
            'The system ingests business profiles, generates embeddings, and serves search results '
            'with AI-generated summaries explaining why each result matches the query.'
        ),
        'tech_tags': 'Python, FastAPI, pgvector, Claude AI, Streamlit',
        'category': 'internal_product',
        'featured': False,
        'sort_order': 15,
        'demo_url': 'https://demos.linkedtrust.us/azlocal/',
        'repo_url': 'https://github.com/Cooperation-org/az-local-first-rag',
    },

    # --- Open Source / Tools ---
    {
        'title': 'LinkedClaims SDK',
        'client_name': 'Open Source',
        'short_description': 'TypeScript SDK for creating and verifying linked claims.',
        'full_description': (
            'The LinkedClaims SDK is a TypeScript library for programmatically creating, signing, '
            'and verifying claims on the LinkedTrust trust graph. It supports claim creation, '
            'attestation workflows, and badge embedding.\n\n'
            'Published as an npm package, it\'s the building block for any application that wants '
            'to integrate with the LinkedTrust platform.'
        ),
        'tech_tags': 'TypeScript, npm, DID/VC, Open Badges v3',
        'category': 'open_source',
        'featured': False,
        'sort_order': 20,
        'demo_url': '',
        'repo_url': 'https://github.com/Cooperation-org/linked-claims-extractor',
    },
    {
        'title': 'Claim Extractor',
        'client_name': 'Open Source',
        'short_description': 'AI-powered PDF extraction for verifiable claims and credentials.',
        'full_description': (
            'Claim Extractor uses AI to parse PDF documents — resumes, certificates, recommendation '
            'letters — and extract structured claims that can be verified on the LinkedTrust platform.\n\n'
            'Upload a PDF, and the system identifies claims (skills, experiences, endorsements), '
            'creates draft LinkedTrust claims for each one, and lets the user review and publish them.'
        ),
        'tech_tags': 'Python, Claude AI, PDF parsing, FastAPI',
        'category': 'open_source',
        'featured': False,
        'sort_order': 21,
        'demo_url': '',
        'repo_url': 'https://github.com/Cooperation-org/claim-extractor',
    },
    {
        'title': 'odoo-cli',
        'client_name': 'Open Source',
        'short_description': 'Command-line tool for Odoo CRM operations.',
        'full_description': (
            'A command-line interface for common Odoo CRM operations. Manage contacts, deals, '
            'and pipelines from the terminal — useful for automation scripts and developers who '
            'prefer CLI workflows over the web UI.'
        ),
        'tech_tags': 'Python, Odoo API, Click',
        'category': 'open_source',
        'featured': False,
        'sort_order': 22,
        'demo_url': '',
        'repo_url': 'https://github.com/Cooperation-org/odoo-cli',
    },
]

SERVICES = [
    {
        'title': 'Baremetal Migration',
        'icon': '\u2699',  # ⚙
        'short_description': 'Move off Amazon. Save money. 128GB bare metal infrastructure.',
        'full_description': (
            'We help organizations migrate from AWS, GCP, or Azure to dedicated bare metal servers. '
            'Our 128GB bare metal infrastructure runs at a fraction of the cost of cloud compute.\n\n'
            'We handle the full migration: audit your current infrastructure, plan the transition, '
            'set up the new servers, migrate your data and services, and provide ongoing support.\n\n'
            'Typical savings: 40-70% reduction in monthly infrastructure costs.'
        ),
        'price_range': '$3K-8K',
        'sort_order': 1,
    },
    {
        'title': 'AI Integration',
        'icon': '\U0001F916',  # 🤖
        'short_description': 'RAG search, document extraction, agentic AI for your systems.',
        'full_description': (
            'We integrate AI capabilities into your existing systems — not chatbots, but real '
            'AI-powered features that solve specific problems.\n\n'
            'RAG search: Let users search your data in natural language.\n'
            'Document extraction: Pull structured data from PDFs, emails, and forms.\n'
            'Agentic AI: Automated workflows that handle repetitive tasks.\n\n'
            'We use Claude, OpenAI, and open-source models depending on your needs and budget.'
        ),
        'price_range': '$2K-6K',
        'sort_order': 2,
    },
    {
        'title': 'Credentials & Badges',
        'icon': '\U0001F393',  # 🎓
        'short_description': 'Verifiable credentials for employees and partners. Open Badges v3.',
        'full_description': (
            'Issue verifiable digital credentials to your employees, volunteers, and partners. '
            'We use the Open Badges v3 standard backed by the LinkedTrust trust graph.\n\n'
            'Credentials are portable, independently verifiable, and can include video testimonials. '
            'Your people get recognized for real skills — backed by cryptographic proof, not just a PDF.'
        ),
        'price_range': '$1.5K-4K',
        'sort_order': 3,
    },
    {
        'title': 'MVP Development',
        'icon': '\U0001F680',  # 🚀
        'short_description': 'Full-stack prototypes in weeks. React, Django, Next.js, FastAPI.',
        'full_description': (
            'We build functional prototypes fast. Tell us the problem, and in 2-4 weeks you\'ll '
            'have a working application you can show to users, investors, or stakeholders.\n\n'
            'Our stack: React or Next.js frontend, Django or FastAPI backend, PostgreSQL database. '
            'Deployed and running. Not a mockup — a real application.'
        ),
        'price_range': '$3K-10K',
        'sort_order': 4,
    },
    {
        'title': 'Team Augmentation',
        'icon': '\U0001F465',  # 👥
        'short_description': 'Full-stack developers at affordable rates. Node, Python, React, Next.js.',
        'full_description': (
            'Need extra hands? Our developers integrate into your team and work on your codebase. '
            'Full-stack capabilities: Node.js, Python, React, Next.js, Django, FastAPI.\n\n'
            'Global team, affordable rates, same high standards. We work in your tools (GitHub, '
            'Jira, Slack) and follow your processes.'
        ),
        'price_range': '$25-55/hr',
        'sort_order': 5,
    },
    {
        'title': 'Recruiter Tools',
        'icon': '\U0001F50D',  # 🔍
        'short_description': 'Sort resumes with verified skills. AI-powered credential matching.',
        'full_description': (
            'Stop reading 200 resumes to find 5 good candidates. Our recruiter tools use AI to '
            'match candidates against your requirements — weighted by verified skills, not just keywords.\n\n'
            'Integrates with the LinkedTrust platform to surface candidates with independently '
            'verified endorsements and credentials.'
        ),
        'price_range': '$2K-5K',
        'sort_order': 6,
    },
]


class Command(BaseCommand):
    help = 'Seed the database with initial portfolio projects and service packages.'

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true', help='Delete existing data before seeding')

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing data...')
            CaseStudy.objects.all().delete()
            Testimonial.objects.all().delete()
            ServicePackage.objects.all().delete()
            PortfolioProject.objects.all().delete()
            self.stdout.write(self.style.WARNING('All portfolio data cleared.'))

        # Seed projects
        created_count = 0
        for data in PROJECTS:
            obj, created = PortfolioProject.objects.get_or_create(
                title=data['title'],
                defaults=data,
            )
            if created:
                created_count += 1
                self.stdout.write(f'  + {obj.title}')
            else:
                self.stdout.write(f'  = {obj.title} (already exists)')
        self.stdout.write(self.style.SUCCESS(f'{created_count} projects created.'))

        # Seed services
        created_count = 0
        for data in SERVICES:
            obj, created = ServicePackage.objects.get_or_create(
                title=data['title'],
                defaults=data,
            )
            if created:
                created_count += 1
                self.stdout.write(f'  + {obj.title}')
            else:
                self.stdout.write(f'  = {obj.title} (already exists)')
        self.stdout.write(self.style.SUCCESS(f'{created_count} services created.'))

        # Link services to related projects
        self._link_services_to_projects()

        self.stdout.write(self.style.SUCCESS('\nDone! Visit /admin/ to add images, case studies, and testimonials.'))

    def _link_services_to_projects(self):
        """Link service packages to relevant example projects."""
        links = {
            'Baremetal Migration': ['AZ Local First RAG', 'LinkedTrust Platform'],
            'AI Integration': ['Accentrics', 'AZ Local First RAG', 'Amebo', 'Claim Extractor'],
            'Credentials & Badges': ['LinkedTrust Platform', 'Skills-Aware', 'Certify', 'Talent / TalentStamp'],
            'MVP Development': ['StreetWell', 'AZ-Sunshine', 'CivicSky'],
            'Team Augmentation': ['StreetWell', 'GoodDollar Apps', 'AZ-Sunshine'],
            'Recruiter Tools': ['Talent / TalentStamp', 'Claim Extractor'],
        }
        for service_title, project_titles in links.items():
            try:
                service = ServicePackage.objects.get(title=service_title)
                projects = PortfolioProject.objects.filter(title__in=project_titles)
                service.example_projects.set(projects)
                self.stdout.write(f'  Linked {service_title} -> {projects.count()} projects')
            except ServicePackage.DoesNotExist:
                pass
