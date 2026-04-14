from django import forms

from user.models import User
from .models import AthleteHealthRecord, MedicalFeedback


class AthleteHealthRecordForm(forms.ModelForm):
    athlete = forms.ModelChoiceField(
        queryset=User.objects.filter(role='athlete', is_active=True).order_by('name'),
        widget=forms.Select(attrs={'class': 'form-input'})
    )

    class Meta:
        model = AthleteHealthRecord
        fields = [
            'athlete',
            'heart_rate',
            'blood_pressure',
            'weight_kg',
            'sleep_hours',
            'fatigue_level',
            'injury_status',
            'injury_notes',
            'recovery_status',
            'performance_notes',
        ]
        widgets = {
            'heart_rate': forms.NumberInput(attrs={'class': 'form-input', 'min': 30, 'max': 220}),
            'blood_pressure': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '120/80'}),
            'weight_kg': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'sleep_hours': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.1', 'min': 0, 'max': 24}),
            'fatigue_level': forms.NumberInput(attrs={'class': 'form-input', 'min': 1, 'max': 10}),
            'injury_status': forms.Select(attrs={'class': 'form-input'}),
            'injury_notes': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            'recovery_status': forms.Select(attrs={'class': 'form-input'}),
            'performance_notes': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
        }


class MedicalFeedbackForm(forms.ModelForm):
    athlete = forms.ModelChoiceField(
        queryset=User.objects.filter(role='athlete', is_active=True).order_by('name'),
        widget=forms.Select(attrs={'class': 'form-input'})
    )

    class Meta:
        model = MedicalFeedback
        fields = ['athlete', 'feedback_type', 'title', 'feedback', 'recommendations']
        widgets = {
            'feedback_type': forms.Select(attrs={'class': 'form-input'}),
            'title': forms.TextInput(attrs={'class': 'form-input'}),
            'feedback': forms.Textarea(attrs={'class': 'form-input', 'rows': 4}),
            'recommendations': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
        }
