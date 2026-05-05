from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('player', '0004_dailyroutine_completion_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='dailyroutine',
            name='workout_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]
