# Keep CoachProfile.sport nullable to support existing records

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('player', '0003_alter_dailyroutine_exercises'),
        ('user', '0004_coachprofile_sport'),
    ]

    operations = [
        migrations.AlterField(
            model_name='coachprofile',
            name='sport',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='coaches', to='player.sport'),
        ),
    ]
