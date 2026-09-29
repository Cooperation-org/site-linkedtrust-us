from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0022_levelupregistration_help_with_other_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='contactinquiry',
            name='archived',
            field=models.BooleanField(default=False, db_index=True),
        ),
        migrations.AddField(
            model_name='contactinquiry',
            name='contacted',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='contactinquiry',
            name='contacted_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='contactinquiry',
            name='contacted_by',
            field=models.CharField(blank=True, default='', max_length=100),
            preserve_default=False,
        ),
    ]
