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

from player.models import AthleteSport, CoachRequest, DailyRoutine, Sport
from user.models import CoachProfile


User = get_user_model()


class PlayerAppTests(TestCase):
    def setUp(self):
        self.athlete = User.objects.create_user(
            email='athlete1@example.com',
            name='Athlete One',
            password='pass12345',
            role='athlete',
        )
        self.coach = User.objects.create_user(
            email='coach1@example.com',
            name='Coach One',
            password='pass12345',
            role='coach',
        )
        self.sport_a, _ = Sport.objects.get_or_create(name='Football')
        self.sport_b, _ = Sport.objects.get_or_create(name='Basketball')
        self.coach_profile = CoachProfile.objects.create(user=self.coach, sport=self.sport_a)

    def test_find_coaches_shows_all_sports(self):
        self.client.force_login(self.athlete)
        response = self.client.get(reverse('player:find_coaches'))
        self.assertEqual(response.status_code, 200)
        all_sports = response.context['all_sports']
        all_sport_names = set(all_sports.values_list('name', flat=True))
        self.assertIn('Football', all_sport_names)
        self.assertIn('Basketball', all_sport_names)

    def test_request_coach_rejects_non_matching_sport(self):
        AthleteSport.objects.create(athlete=self.athlete, sport=self.sport_b, skill_level='beginner')

        self.client.force_login(self.athlete)
        response = self.client.post(reverse('player:request_coach', args=[self.coach_profile.id]))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('player:select_sports'))
        self.assertFalse(CoachRequest.objects.filter(athlete=self.athlete, coach=self.coach).exists())

    def test_routine_detail_access_limited_to_owner_athlete(self):
        other_athlete = User.objects.create_user(
            email='athlete2@example.com',
            name='Athlete Two',
            password='pass12345',
            role='athlete',
        )
        routine = DailyRoutine.objects.create(
            athlete=other_athlete,
            coach=self.coach,
            sport=self.sport_a,
            day='monday',
            title='Sprint Session',
            start_time=time(6, 0),
            end_time=time(7, 0),
        )

        self.client.force_login(self.athlete)
        response = self.client.get(reverse('player:routine_detail', args=[routine.id]))
        self.assertEqual(response.status_code, 404)

    def test_request_coach_with_matching_sport_creates_pending_request(self):
        AthleteSport.objects.create(athlete=self.athlete, sport=self.sport_a, skill_level='beginner')

        self.client.force_login(self.athlete)
        response = self.client.post(reverse('player:request_coach', args=[self.coach_profile.id]))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('player:find_coaches'))
        self.assertTrue(
            CoachRequest.objects.filter(
                athlete=self.athlete, coach=self.coach, sport=self.sport_a, status='pending'
            ).exists()
        )

    def test_request_coach_get_does_not_create_request(self):
        AthleteSport.objects.create(athlete=self.athlete, sport=self.sport_a, skill_level='beginner')

        self.client.force_login(self.athlete)
        response = self.client.get(reverse('player:request_coach', args=[self.coach_profile.id]))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('player:find_coaches'))
        self.assertFalse(CoachRequest.objects.filter(athlete=self.athlete, coach=self.coach).exists())


@tag('selenium')
class PlayerAppSeleniumTests(StaticLiveServerTestCase):
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
        self.athlete = User.objects.create_user(
            email='selenium_athlete@example.com',
            name='Selenium Athlete',
            password='pass12345',
            role='athlete',
        )
        self.sport_match, _ = Sport.objects.get_or_create(name='Selenium Match Sport')
        self.sport_other, _ = Sport.objects.get_or_create(name='Selenium Other Sport')
        AthleteSport.objects.create(athlete=self.athlete, sport=self.sport_match, skill_level='beginner')
        self.matching_coach_user = User.objects.create_user(
            email='selenium_matching_coach@example.com',
            name='Matching Coach',
            password='pass12345',
            role='coach',
            is_approved=True,
        )
        self.non_matching_coach_user = User.objects.create_user(
            email='selenium_nonmatching_coach@example.com',
            name='NonMatching Coach',
            password='pass12345',
            role='coach',
            is_approved=True,
        )
        CoachProfile.objects.create(
            user=self.matching_coach_user,
            sport=self.sport_match,
            specialization='Sprint'
        )
        CoachProfile.objects.create(
            user=self.non_matching_coach_user,
            sport=self.sport_other,
            specialization='Strength'
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

    def test_player_dashboard_visible_after_login(self):
        self._login('selenium_athlete@example.com', 'pass12345')
        self.browser.get(self.live_server_url + reverse('player:dashboard'))
        WebDriverWait(self.browser, 10).until(
            lambda d: 'Athlete Dashboard' in d.page_source
        )
        self.assertIn('Athlete Dashboard', self.browser.page_source)

    def test_player_can_request_matching_coach_from_find_coaches(self):
        self._login('selenium_athlete@example.com', 'pass12345')
        self.browser.get(self.live_server_url + reverse('player:find_coaches'))
        request_button = WebDriverWait(self.browser, 10).until(
            lambda d: d.find_element(
                By.XPATH,
                f"//form[contains(@action, '/player/coaches/request/{self.matching_coach_user.coach_profile.id}/')]/button"
            )
        )
        request_button.click()
        WebDriverWait(self.browser, 10).until(
            lambda _: CoachRequest.objects.filter(
                athlete=self.athlete,
                coach=self.matching_coach_user,
                sport=self.sport_match,
                status='pending',
            ).exists()
        )
        self.assertTrue(
            CoachRequest.objects.filter(
                athlete=self.athlete,
                coach=self.matching_coach_user,
                sport=self.sport_match,
                status='pending',
            ).exists()
        )

    def test_non_matching_coach_shows_disabled_request_button(self):
        self._login('selenium_athlete@example.com', 'pass12345')
        self.browser.get(self.live_server_url + reverse('player:find_coaches'))
        disabled_buttons = WebDriverWait(self.browser, 10).until(
            lambda d: d.find_elements(By.XPATH, "//button[@disabled and contains(., 'Sport Not Selected')]")
        )
        self.assertGreaterEqual(len(disabled_buttons), 1)
