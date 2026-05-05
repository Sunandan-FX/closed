from django.db import models
from django.conf import settings


class Sport(models.Model):
    """Available sports for training"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)  # For emoji or icon class

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'sport'
        ordering = ['name']


class CoachRequest(models.Model):
    """Athlete's request to a coach for training"""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    )

    athlete = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='coach_requests_sent'
    )
    coach = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='coach_requests_received'
    )
    sport = models.ForeignKey(Sport, on_delete=models.CASCADE)
    message = models.TextField(blank=True, help_text="Message to the coach")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.athlete.first_name} -> {self.coach.first_name} ({self.sport.name}) - {self.status}"

    class Meta:
        db_table = 'coach_request'
        unique_together = ['athlete', 'coach', 'sport']
        ordering = ['-created_at']


class AthleteCoach(models.Model):
    """Relationship between athlete and coach after request is accepted"""
    athlete = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='my_coaches'
    )
    coach = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='my_athletes'
    )
    sport = models.ForeignKey(Sport, on_delete=models.CASCADE)
    start_date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.athlete.first_name} trained by {self.coach.first_name} in {self.sport.name}"

    class Meta:
        db_table = 'athlete_coach'
        unique_together = ['athlete', 'coach', 'sport']


class DailyRoutine(models.Model):
    """Daily routine/schedule set by coach for athlete"""
    DAY_CHOICES = (
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
        ('sunday', 'Sunday'),
    )

    athlete = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='daily_routines'
    )
    coach = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='routines_created'
    )
    sport = models.ForeignKey(Sport, on_delete=models.CASCADE)
    day = models.CharField(max_length=20, choices=DAY_CHOICES)
    workout_date = models.DateField(null=True, blank=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    start_time = models.TimeField()
    end_time = models.TimeField()
    exercises = models.TextField(blank=True, help_text="List of exercises for this session")
    notes = models.TextField(blank=True, help_text="Additional notes from coach")
    athlete_marked_complete = models.BooleanField(default=False)
    coach_approved_completion = models.BooleanField(default=False)
    completion_message = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.workout_date:
            return f"{self.athlete.first_name} - {self.workout_date} - {self.title}"
        return f"{self.athlete.first_name} - {self.day} - {self.title}"

    class Meta:
        db_table = 'daily_routine'
        ordering = ['day', 'start_time']


class AthleteSport(models.Model):
    """Sports selected by athlete for training"""
    athlete = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='selected_sports'
    )
    sport = models.ForeignKey(Sport, on_delete=models.CASCADE)
    skill_level = models.CharField(
        max_length=20,
        choices=[('beginner', 'Beginner'), ('intermediate', 'Intermediate'), ('advanced', 'Advanced')],
        default='beginner'
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.athlete.first_name} - {self.sport.name}"

    class Meta:
        db_table = 'athlete_sport'
        unique_together = ['athlete', 'sport']

