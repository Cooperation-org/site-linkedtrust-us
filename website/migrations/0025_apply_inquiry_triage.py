"""One-time data migration: apply the shipped contact-inquiry triage. Sets each
inquiry's verdict and archives the spam / duplicate / test rows so the console
inbox shows the real people. Idempotent, and it only auto-archives (never
auto-unarchives), so a manual restore in the admin or console is respected.
Reverse is a no-op: unarchiving by hand is the way back, not a migration."""
import json
from pathlib import Path
from django.db import migrations

ARCHIVE = {"spam", "dupe", "test"}


def apply_triage(apps, schema_editor):
    ContactInquiry = apps.get_model("website", "ContactInquiry")
    data_path = Path(__file__).resolve().parents[1] / "data" / "inquiry_triage.json"
    try:
        mapping = json.loads(data_path.read_text())
    except FileNotFoundError:
        return
    for sid, verdict in mapping.items():
        try:
            inq = ContactInquiry.objects.get(pk=int(sid))
        except ContactInquiry.DoesNotExist:
            continue
        fields = []
        if inq.verdict != verdict:
            inq.verdict = verdict
            fields.append("verdict")
        if verdict in ARCHIVE and not inq.archived:
            inq.archived = True
            fields.append("archived")
        if fields:
            inq.save(update_fields=fields)


class Migration(migrations.Migration):

    dependencies = [
        ("website", "0024_contactinquiry_verdict"),
    ]

    operations = [
        migrations.RunPython(apply_triage, migrations.RunPython.noop),
    ]
