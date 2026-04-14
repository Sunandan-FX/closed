from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from player.models import Sport
from user.models import MedicalProfile

from .models import AthleteHealthRecord, MedicalFeedback


User = get_user_model()


class MedicalStaffDashboardTests(TestCase):
    def setUp(self):
        self.medical_user = User.objects.create_user(
            email='medic@test.com',
            name='Medical User',
            password='pass12345',
            role='medical',
        )
        MedicalProfile.objects.create(user=self.medical_user, specialty='Sports Medicine')
        self.athlete = User.objects.create_user(
            email='athlete_medical@test.com',
            name='Athlete Medical',
            password='pass12345',
            role='athlete',
        )
        Sport.objects.get_or_create(name='Medical Test Sport')

    def test_medical_dashboard_accessible_for_medical_user(self):
        self.client.force_login(self.medical_user)
        response = self.client.get(reverse('medical_staff:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Medical Staff Dashboard')

    def test_add_health_record_creates_record(self):
        self.client.force_login(self.medical_user)
        response = self.client.post(
            reverse('medical_staff:add_health_record'),
            data={
                'athlete': self.athlete.id,
                'heart_rate': 68,
                'blood_pressure': '120/80',
                'weight_kg': '65.50',
                'sleep_hours': '7.5',
                'fatigue_level': 3,
                'injury_status': 'minor',
                'injury_notes': 'Mild knee pain',
                'recovery_status': 'watch',
                'performance_notes': 'Needs reduced load for 3 days',
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('medical_staff:dashboard'))
        self.assertTrue(
            AthleteHealthRecord.objects.filter(
                athlete=self.athlete, medical_staff=self.medical_user
            ).exists()
        )

    def test_add_feedback_creates_feedback(self):
        self.client.force_login(self.medical_user)
        response = self.client.post(
            reverse('medical_staff:add_feedback'),
            data={
                'athlete': self.athlete.id,
                'feedback_type': 'performance',
                'title': 'Training Load Suggestion',
                'feedback': 'Reduce high-intensity sessions this week.',
                'recommendations': 'Hydration, sleep >8 hours.',
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('medical_staff:dashboard'))
        self.assertTrue(
            MedicalFeedback.objects.filter(
                athlete=self.athlete, medical_staff=self.medical_user
            ).exists()
        )
