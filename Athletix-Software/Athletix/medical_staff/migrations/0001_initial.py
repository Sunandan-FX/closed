from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AthleteHealthRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('recorded_on', models.DateField(auto_now_add=True)),
                ('heart_rate', models.PositiveIntegerField(help_text='Resting heart rate (bpm)')),
                ('blood_pressure', models.CharField(blank=True, help_text='e.g. 120/80', max_length=20)),
                ('weight_kg', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('sleep_hours', models.DecimalField(blank=True, decimal_places=1, max_digits=4, null=True)),
                ('fatigue_level', models.PositiveSmallIntegerField(default=1, help_text='1(low)-10(high)')),
                ('injury_status', models.CharField(choices=[('none', 'No Injury'), ('minor', 'Minor Injury'), ('moderate', 'Moderate Injury'), ('severe', 'Severe Injury'), ('recovering', 'Recovering')], default='none', max_length=20)),
                ('injury_notes', models.TextField(blank=True)),
                ('recovery_status', models.CharField(choices=[('good', 'Good'), ('watch', 'Needs Monitoring'), ('critical', 'Critical')], default='good', max_length=20)),
                ('performance_notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('athlete', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='health_records', to=settings.AUTH_USER_MODEL)),
                ('medical_staff', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='recorded_health_metrics', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'athlete_health_record',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='MedicalFeedback',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('feedback_type', models.CharField(choices=[('health', 'Health Feedback'), ('performance', 'Performance Feedback')], max_length=20)),
                ('title', models.CharField(max_length=150)),
                ('feedback', models.TextField()),
                ('recommendations', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('athlete', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='medical_feedbacks', to=settings.AUTH_USER_MODEL)),
                ('medical_staff', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='given_medical_feedbacks', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'medical_feedback',
                'ordering': ['-created_at'],
            },
        ),
    ]

