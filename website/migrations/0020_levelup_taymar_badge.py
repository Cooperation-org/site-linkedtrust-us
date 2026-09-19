from django.db import migrations

CLAIM_ID = '124842'
QUOTE = "Wow! I am so glad I took the time to attend the LEVELUP workshop today, it was so helpful. The opportunity to get some live, in the moment, problem-solving help with what was going wrong with my app, and being walked through the solutions together with a group of technical wizards was invaluable. These issues have been plaguing us for months, and now I see not only the solutions to the immediate problems in the code, but also the underlying systems issues. Fixing those systems will help prevent future problems moving forward.  I'm finally unstuck!! I can't wait to take these insights back to my team. Thank you!"


def add(apps, schema_editor):
    Testimonial = apps.get_model('website', 'Testimonial')
    if Testimonial.objects.filter(linked_claim_id=CLAIM_ID).exists():
        return
    Testimonial.objects.create(
        person_name='Taymar Pixley',
        quote_text=QUOTE,
        linked_claim_id=CLAIM_ID,
        placement='levelup',
        badge_layout='card',
        badge_theme='light',
    )


def remove(apps, schema_editor):
    apps.get_model('website', 'Testimonial').objects.filter(linked_claim_id=CLAIM_ID, placement='levelup').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0019_testimonial_levelup_placement'),
    ]

    operations = [
        migrations.RunPython(add, remove),
    ]
