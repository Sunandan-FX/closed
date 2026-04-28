from django.conf import settings
from django.db import models


class AthleteHealthRecord(models.Model):
    INJURY_STATUS_CHOICES = (
        ('none', 'No Injury'),
        ('minor', 'Minor Injury'),
        ('moderate', 'Moderate Injury'),
        ('severe', 'Severe Injury'),
        ('recovering', 'Recovering'),
    )
    RECOVERY_STATUS_CHOICES = (
        ('good', 'Good'),
        ('watch', 'Needs Monitoring'),
        ('critical', 'Critical'),
    )

    athlete = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='health_records',
    )
    medical_staff = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='recorded_health_metrics',
        null=True,
        blank=True,
    )
    recorded_on = models.DateField(auto_now_add=True)
    heart_rate = models.PositiveIntegerField(help_text='Resting heart rate (bpm)')
    blood_pressure = models.CharField(max_length=20, blank=True, help_text='e.g. 120/80')
    weight_kg = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    sleep_hours = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    fatigue_level = models.PositiveSmallIntegerField(default=1, help_text='1(low)-10(high)')
    injury_status = models.CharField(max_length=20, choices=INJURY_STATUS_CHOICES, default='none')
    injury_notes = models.TextField(blank=True)
    recovery_status = models.CharField(max_length=20, choices=RECOVERY_STATUS_CHOICES, default='good')
    performance_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    review_requested = models.BooleanField(default=False, help_text='Player requested medical review')

    class Meta:
        db_table = 'athlete_health_record'
        ordering = ['-created_at']


class MedicalFeedback(models.Model):
    FEEDBACK_TYPE_CHOICES = (
        ('health', 'Health Feedback'),
        ('performance', 'Performance Feedback'),
    )

    athlete = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='medical_feedbacks',
    )
    medical_staff = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='given_medical_feedbacks',
    )
    feedback_type = models.CharField(max_length=20, choices=FEEDBACK_TYPE_CHOICES)
    title = models.CharField(max_length=150)
    feedback = models.TextField()
    recommendations = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'medical_feedback'
        ordering = ['-created_at']
