from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0025_apply_inquiry_triage'),
    ]

    operations = [
        migrations.AddField(
            model_name='contactinquiry',
            name='contacted_claim_id',
            field=models.CharField(blank=True, default='', max_length=64),
        ),
    ]
