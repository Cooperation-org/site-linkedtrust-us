from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0023_contactinquiry_tracking'),
    ]

    operations = [
        migrations.AddField(
            model_name='contactinquiry',
            name='verdict',
            field=models.CharField(blank=True, db_index=True, default='', max_length=20),
        ),
    ]
