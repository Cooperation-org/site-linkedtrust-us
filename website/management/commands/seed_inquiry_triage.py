"""Apply the one-time contact-inquiry triage: set each inquiry's verdict and
archive the spam / duplicate / test rows. Idempotent. Reversible (unarchive in
the admin or console). The classification lives in website/data/inquiry_triage.json
(id -> verdict), produced from the offline triage pass."""
import json
from pathlib import Path
from django.core.management.base import BaseCommand
from website.models import ContactInquiry

ARCHIVE = {"spam", "dupe", "test"}


class Command(BaseCommand):
    help = "Set ContactInquiry.verdict and archive spam/dupe/test from the shipped triage map."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Report only, write nothing.")

    def handle(self, *args, **opts):
        data_path = Path(__file__).resolve().parents[2] / "data" / "inquiry_triage.json"
        mapping = json.loads(data_path.read_text())
        dry = opts["dry_run"]
        set_verdict = archived = skipped = 0
        for sid, verdict in mapping.items():
            try:
                inq = ContactInquiry.objects.get(pk=int(sid))
            except ContactInquiry.DoesNotExist:
                skipped += 1
                continue
            want_archived = verdict in ARCHIVE
            changed = False
            if inq.verdict != verdict:
                inq.verdict = verdict; changed = True; set_verdict += 1
            # Only auto-archive; never auto-unarchive (respect manual restores).
            if want_archived and not inq.archived:
                inq.archived = True; changed = True; archived += 1
            if changed and not dry:
                inq.save(update_fields=["verdict", "archived"])
        self.stdout.write(self.style.SUCCESS(
            f"{'[dry-run] ' if dry else ''}verdict set: {set_verdict}, archived: {archived}, "
            f"missing ids skipped: {skipped}, total in map: {len(mapping)}"))
