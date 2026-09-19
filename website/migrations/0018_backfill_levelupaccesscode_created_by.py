from django.db import migrations


def backfill(apps, schema_editor):
    """Codes made before created_by existed: take the creator from the admin
    history, which logs who added each object."""
    LogEntry = apps.get_model('admin', 'LogEntry')
    ContentType = apps.get_model('contenttypes', 'ContentType')
    Code = apps.get_model('website', 'LevelUpAccessCode')
    ct = ContentType.objects.filter(app_label='website', model='levelupaccesscode').first()
    if not ct:
        return
    for entry in LogEntry.objects.filter(content_type=ct, action_flag=1).order_by('action_time'):
        if entry.object_id and entry.object_id.isdigit():
            Code.objects.filter(pk=int(entry.object_id), created_by__isnull=True).update(created_by=entry.user_id)


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0017_levelupaccesscode_created_by'),
        ('admin', '0003_logentry_add_action_flag_choices'),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.RunPython(backfill, migrations.RunPython.noop),
    ]
