from django.contrib import admin
from .models import AthleteHealthRecord, MedicalFeedback


@admin.register(AthleteHealthRecord)
class AthleteHealthRecordAdmin(admin.ModelAdmin):
    list_display = (
        'athlete',
        'medical_staff',
        'heart_rate',
        'fatigue_level',
        'injury_status',
        'recovery_status',
        'created_at',
    )
    list_filter = ('injury_status', 'recovery_status', 'created_at')
    search_fields = ('athlete__name', 'medical_staff__name')


@admin.register(MedicalFeedback)
class MedicalFeedbackAdmin(admin.ModelAdmin):
    list_display = ('athlete', 'medical_staff', 'feedback_type', 'title', 'created_at')
    list_filter = ('feedback_type', 'created_at')
    search_fields = ('athlete__name', 'medical_staff__name', 'title')
