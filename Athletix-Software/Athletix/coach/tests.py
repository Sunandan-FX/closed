from datetime import time

from django.contrib.auth import get_user_model
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import TestCase
from django.test import tag
from django.urls import reverse
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from unittest import SkipTest

from player.models import AthleteCoach, CoachRequest, DailyRoutine, Sport
from user.models import AthleteProfile, CoachProfile


User = get_user_model()


class CoachAppTests(TestCase):
    def setUp(self):
        self.coach = User.objects.create_user(
            email='coach@example.com',
            name='Coach User',
            password='pass12345',
            role='coach',
        )
        self.athlete = User.objects.create_user(
            email='athlete@example.com',
            name='Athlete User',
            password='pass12345',
            role='athlete',
        )
        self.athlete_profile = AthleteProfile.objects.create(user=self.athlete)
        self.sport_football, _ = Sport.objects.get_or_create(name='Football')
        self.sport_tennis, _ = Sport.objects.get_or_create(name='Tennis')
        self.coach_profile = CoachProfile.objects.create(user=self.coach, sport=self.sport_football)

    def test_accept_request_with_matching_sport_creates_relation(self):
        coach_request = CoachRequest.objects.create(
            athlete=self.athlete,
            coach=self.coach,
            sport=self.sport_football,
            status='pending',
        )
        self.client.force_login(self.coach)
        response = self.client.post(reverse('coach:handle_request', args=[coach_request.id, 'accept']))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('coach:athlete_requests'))
        coach_request.refresh_from_db()
        self.assertEqual(coach_request.status, 'accepted')
        self.assertTrue(
            AthleteCoach.objects.filter(
                athlete=self.athlete, coach=self.coach, sport=self.sport_football, is_active=True
            ).exists()
        )

    def test_accept_request_with_mismatched_sport_is_blocked(self):
        coach_request = CoachRequest.objects.create(
            athlete=self.athlete,
            coach=self.coach,
            sport=self.sport_tennis,
            status='pending',
        )
        self.client.force_login(self.coach)
        response = self.client.post(reverse('coach:handle_request', args=[coach_request.id, 'accept']))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('coach:athlete_requests'))
        coach_request.refresh_from_db()
        self.assertEqual(coach_request.status, 'pending')
        self.assertFalse(AthleteCoach.objects.filter(athlete=self.athlete, coach=self.coach).exists())

    def test_approve_routine_completion_sets_completion_fields(self):
        routine = DailyRoutine.objects.create(
            athlete=self.athlete,
            coach=self.coach,
            sport=self.sport_football,
            day='monday',
            title='Drill',
            start_time=time(7, 0),
            end_time=time(8, 0),
            completion_message='Not complete',
        )
        AthleteCoach.objects.create(
            athlete=self.athlete,
            coach=self.coach,
            sport=self.sport_football,
            is_active=True,
        )
        self.client.force_login(self.coach)
        response = self.client.post(reverse('coach:approve_routine_completion', args=[routine.id]))

        self.assertEqual(response.status_code, 302)
        routine.refresh_from_db()
        self.assertTrue(routine.athlete_marked_complete)
        self.assertTrue(routine.coach_approved_completion)
        self.assertEqual(routine.completion_message, 'Approved by coach.')

    def test_approve_routine_completion_get_redirects_without_update(self):
        routine = DailyRoutine.objects.create(
            athlete=self.athlete,
            coach=self.coach,
            sport=self.sport_football,
            day='tuesday',
            title='Speed Work',
            start_time=time(9, 0),
            end_time=time(10, 0),
            completion_message='Not complete',
        )
        self.client.force_login(self.coach)
        response = self.client.get(reverse('coach:approve_routine_completion', args=[routine.id]))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('coach:my_athletes'))
        routine.refresh_from_db()
        self.assertFalse(routine.coach_approved_completion)

    def test_accept_request_without_coach_sport_is_blocked(self):
        self.coach_profile.sport = None
        self.coach_profile.save(update_fields=['sport'])
        coach_request = CoachRequest.objects.create(
            athlete=self.athlete,
            coach=self.coach,
            sport=self.sport_football,
            status='pending',
        )

        self.client.force_login(self.coach)
        response = self.client.post(reverse('coach:handle_request', args=[coach_request.id, 'accept']))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('coach:athlete_requests'))
        coach_request.refresh_from_db()
        self.assertEqual(coach_request.status, 'pending')


@tag('selenium')
class CoachAppSeleniumTests(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        options = Options()
        if os.getenv('SELENIUM_HEADLESS', '0') == '1':
            options.add_argument('--headless=new')
        else:
            options.add_argument('--start-maximized')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1400,900')
        try:
            cls.browser = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=options,
            )
            cls.browser.implicitly_wait(10)
        except Exception as exc:
            raise SkipTest(f'Selenium WebDriver unavailable: {exc}')

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'browser'):
            cls.browser.quit()
        super().tearDownClass()

    def setUp(self):
        self.coach = User.objects.create_user(
            email='selenium_coach@example.com',
            name='Selenium Coach',
            password='pass12345',
            role='coach',
            is_approved=True,
        )
        self.sport, _ = Sport.objects.get_or_create(name='Selenium Sport Coach')
        CoachProfile.objects.create(user=self.coach, sport=self.sport)
        self.athlete = User.objects.create_user(
            email='selenium_athlete_for_coach@example.com',
            name='Coach Side Athlete',
            password='pass12345',
            role='athlete',
        )
        AthleteProfile.objects.create(user=self.athlete)
        self.request_obj = CoachRequest.objects.create(
            athlete=self.athlete,
            coach=self.coach,
            sport=self.sport,
            status='pending',
            message='Need training plan',
        )

    def _login(self, email, password):
        self.browser.get(self.live_server_url + reverse('login'))
        WebDriverWait(self.browser, 10).until(
            lambda d: d.find_element(By.ID, 'email').is_displayed()
        )
        self.browser.find_element(By.ID, 'email').clear()
        self.browser.find_element(By.ID, 'email').send_keys(email)
        self.browser.find_element(By.ID, 'password').clear()
        self.browser.find_element(By.ID, 'password').send_keys(password)
        self.browser.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

    def test_coach_dashboard_visible_after_login(self):
        self._login('selenium_coach@example.com', 'pass12345')
        self.browser.get(self.live_server_url + reverse('coach:dashboard'))
        WebDriverWait(self.browser, 10).until(lambda d: 'coach/dashboard' in d.current_url)
        self.assertIn('Coach Dashboard', self.browser.page_source)

    def test_coach_can_accept_request_from_athlete_requests_page(self):
        self._login('selenium_coach@example.com', 'pass12345')
        self.browser.get(self.live_server_url + reverse('coach:athlete_requests'))
        accept_button = WebDriverWait(self.browser, 10).until(
            lambda d: d.find_element(
                By.XPATH,
                f"//form[contains(@action, '/coach/requests/{self.request_obj.id}/accept/')]/button"
            )
        )
        accept_button.click()
        WebDriverWait(self.browser, 10).until(
            lambda _: CoachRequest.objects.get(id=self.request_obj.id).status == 'accepted'
        )
        self.request_obj.refresh_from_db()
        self.assertEqual(self.request_obj.status, 'accepted')
        self.assertTrue(
            AthleteCoach.objects.filter(
                athlete=self.athlete, coach=self.coach, sport=self.sport, is_active=True
            ).exists()
        )

    def test_coach_can_reject_request_from_athlete_requests_page(self):
        second_athlete = User.objects.create_user(
            email='selenium_athlete_for_reject@example.com',
            name='Reject Athlete',
            password='pass12345',
            role='athlete',
        )
        AthleteProfile.objects.create(user=second_athlete)
        reject_request = CoachRequest.objects.create(
            athlete=second_athlete,
            coach=self.coach,
            sport=self.sport,
            status='pending',
        )

        self._login('selenium_coach@example.com', 'pass12345')
        self.browser.get(self.live_server_url + reverse('coach:athlete_requests'))
        reject_button = WebDriverWait(self.browser, 10).until(
            lambda d: d.find_element(
                By.XPATH,
                f"//form[contains(@action, '/coach/requests/{reject_request.id}/reject/')]/button"
            )
        )
        reject_button.click()
        WebDriverWait(self.browser, 10).until(
            lambda _: CoachRequest.objects.get(id=reject_request.id).status == 'rejected'
        )
        reject_request.refresh_from_db()
        self.assertEqual(reject_request.status, 'rejected')
