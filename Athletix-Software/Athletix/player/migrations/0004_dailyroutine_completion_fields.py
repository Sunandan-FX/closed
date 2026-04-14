from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('player', '0003_alter_dailyroutine_exercises'),
    ]

    operations = [
        migrations.AddField(
            model_name='dailyroutine',
            name='athlete_marked_complete',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='dailyroutine',
            name='coach_approved_completion',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='dailyroutine',
            name='completion_message',
            field=models.CharField(blank=True, max_length=200),
        ),
    ]

