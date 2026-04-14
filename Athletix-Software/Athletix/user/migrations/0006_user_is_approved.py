from django.db import migrations, models


def set_unapproved_for_existing_coaches(apps, schema_editor):
    User = apps.get_model('user', 'User')
    User.objects.filter(role='coach').update(is_approved=False)


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0005_alter_coachprofile_sport'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='is_approved',
            field=models.BooleanField(default=True),
        ),
        migrations.RunPython(set_unapproved_for_existing_coaches, migrations.RunPython.noop),
    ]

