"""Submit URLs to IndexNow (Bing / Yandex / Copilot / ChatGPT Search index).

By default submits every canonical URL on the site (derived from the sitemaps).
Pass one or more --url flags to submit specific URLs instead.

Examples:
    python manage.py indexnow_ping
    python manage.py indexnow_ping --include-blog
    python manage.py indexnow_ping --url https://linkedtrust.us/work/streetwell/
    python manage.py indexnow_ping --url https://linkedtrust.us/ --url https://linkedtrust.us/services/
"""
from django.core.management.base import BaseCommand

from website import indexnow


class Command(BaseCommand):
    help = "Submit site URLs to IndexNow for instant indexing (Bing/Yandex)."

    def add_arguments(self, parser):
        parser.add_argument(
            '--url',
            action='append',
            dest='urls',
            metavar='URL',
            help='Submit a specific URL (repeatable). If omitted, the whole site is submitted.',
        )
        parser.add_argument(
            '--host',
            default=indexnow.DEFAULT_HOST,
            help=f'Host to submit under (default: {indexnow.DEFAULT_HOST}).',
        )
        parser.add_argument(
            '--include-blog',
            action='store_true',
            dest='include_blog',
            help='Also submit blog URLs pulled from /blog/sitemap.xml (Ghost).',
        )

    def handle(self, *args, **options):
        host = options['host']
        urls = options.get('urls')
        include_blog = options.get('include_blog')

        if urls:
            self.stdout.write(f'Submitting {len(urls)} explicit URL(s) to IndexNow...')
        else:
            urls = indexnow.all_site_urls(host=host)
            if include_blog:
                seen = set(urls)
                blog = [u for u in indexnow.blog_urls(host=host) if u not in seen]
                urls = urls + blog
                self.stdout.write(f'Including {len(blog)} blog URL(s) from /blog/sitemap.xml')
            self.stdout.write(f'Submitting all {len(urls)} site URL(s) to IndexNow...')

        for u in urls:
            self.stdout.write(f'  - {u}')

        if not urls:
            self.stdout.write(self.style.WARNING('No URLs to submit. Nothing sent.'))
            return

        status = indexnow.submit_urls(urls, host=host)

        if status in (200, 202):
            self.stdout.write(self.style.SUCCESS(
                f'IndexNow accepted {len(urls)} URL(s) (HTTP {status}).'))
        elif status is None:
            self.stdout.write(self.style.ERROR(
                'IndexNow submission failed (network/error). Check logs.'))
        else:
            self.stdout.write(self.style.WARNING(
                f'IndexNow returned HTTP {status} — submission may have been rejected. '
                'Check the key file is reachable and the host matches.'))
