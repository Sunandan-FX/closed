from django.test import TestCase, tag, Client
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import reverse
import os
from unittest import SkipTest

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select

from user.models import User
from player.models import Sport, AthleteSport, CoachRequest, DailyRoutine
from user.models import CoachProfile, AthleteProfile

from datetime import date

# ==============================================================================
# -------------------------------- UNIT TESTS ----------------------------------
# ==============================================================================

@tag('unit')
class PlayerAppUnitTests(TestCase):
    """
    Comprehensive Unit tests for the player app.
    Run these ONLY with: python manage.py test player --tag=unit
    """

    def setUp(self):
        self.client = Client()
        self.test_user = User.objects.create_user(
            email='unit_player@example.com',
            name='Unit Player',
            password='testpassword123',
            role='athlete',
            is_approved=True
        )
        self.test_superuser = User.objects.create_superuser(
            email='admin_player@example.com',
            name='Admin',
            password='testpassword123',
        )

    def test_model_creation(self):
        """Basic model creation verification."""
        self.assertEqual(self.test_user.email, 'unit_player@example.com')
        self.assertTrue(self.test_user.check_password('testpassword123'))

    def test_user_authentication(self):
        """Test that user can log in and access system."""
        login = self.client.login(email='unit_player@example.com', password='testpassword123')
        self.assertTrue(login)

    def test_player_dashboard_access(self):
        """Unit Test: Ensures an authenticated athlete can access their dashboard."""
        self.client.login(email='unit_player@example.com', password='testpassword123')
        response = self.client.get(reverse('player:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'player/dashboard.html')

    def test_non_athlete_redirected_from_player_dashboard(self):
        """Unit Test: Verifies non-athlete users are redirected from the player dashboard."""
        coach_user = User.objects.create_user(
            email='coach@example.com',
            name='Coach',
            password='password',
            role='coach',
            is_approved=True
        )
        self.client.login(email='coach@example.com', password='password')
        response = self.client.get(reverse('player:dashboard'))
        self.assertRedirects(response, reverse('home'))


# ==============================================================================
# ------------------------------ SELENIUM TESTS --------------------------------
# ==============================================================================

@tag('selenium')
class PlayerAppSeleniumTests(StaticLiveServerTestCase):
    """
    Comprehensive Selenium end-to-end tests for the player app.
    Run these ONLY with: python manage.py test player --tag=selenium
    """
    
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
        self.sport = Sport.objects.create(name='Selenium Sport')
        self.athlete = User.objects.create_user(
            email='selenium_player@example.com',
            name='Selenium Player',
            password='pass12345',
            role='athlete',
            is_approved=True,
        )
        AthleteProfile.objects.get_or_create(user=self.athlete)

        self.coach = User.objects.create_user(
            email='selenium_player_coach@example.com',
            name='Selenium Coach',
            password='pass12345',
            role='coach',
            is_approved=True,
        )
        CoachProfile.objects.get_or_create(user=self.coach, defaults={'sport': self.sport})
        self.coach.coach_profile.sport = self.sport
        self.coach.coach_profile.save()

        AthleteSport.objects.get_or_create(athlete=self.athlete, sport=self.sport)
        DailyRoutine.objects.create(
            athlete=self.athlete,
            coach=self.coach,
            sport=self.sport,
            day='monday',
            workout_date=date.today(),
            title='Existing Routine',
            description='',
            start_time='09:00',
            end_time='10:00',
            exercises='Run',
            notes='',
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

    def test_athlete_login_and_view_dashboard(self):
        """Selenium Test: An athlete logs in and views their dashboard."""
        self._login('selenium_player@example.com', 'pass12345')
        WebDriverWait(self.browser, 10).until(lambda d: d.current_url.endswith(reverse('player:dashboard')))
        WebDriverWait(self.browser, 10).until(lambda d: 'Athlete Dashboard' in d.page_source)

    def test_player_can_select_sport_and_request_coach(self):
        """Selenium Test: Athlete selects a sport and requests a coach."""
        self._login('selenium_player@example.com', 'pass12345')

        # Select sports
        self.browser.get(self.live_server_url + reverse('player:select_sports'))
        WebDriverWait(self.browser, 10).until(lambda d: 'Available Sports' in d.page_source)
        checkbox = self.browser.find_element(By.CSS_SELECTOR, f"input[type='checkbox'][name='sports'][value='{self.sport.id}']")
        if not checkbox.is_selected():
            checkbox.click()
        self.browser.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        WebDriverWait(self.browser, 10).until(lambda d: 'Sports selection updated' in d.page_source)

        # Request coach
        self.browser.get(self.live_server_url + reverse('player:find_coaches'))
        WebDriverWait(self.browser, 10).until(lambda d: 'Find a Coach' in d.page_source)
        self.browser.find_element(By.XPATH, "//button[contains(., 'Request Coach')]").click()
        WebDriverWait(self.browser, 10).until(lambda d: 'Request sent' in d.page_source or 'pending' in d.page_source.lower())
        self.assertTrue(CoachRequest.objects.filter(athlete=self.athlete, coach=self.coach, sport=self.sport).exists())

    def test_player_can_submit_self_health_metrics(self):
        """Selenium Test: Athlete submits health metrics from the dashboard."""
        self._login('selenium_player@example.com', 'pass12345')
        WebDriverWait(self.browser, 10).until(lambda d: d.current_url.endswith(reverse('player:dashboard')))

        toggle = self.browser.find_element(By.ID, 'health-toggle-btn')
        toggle.click()
        WebDriverWait(self.browser, 10).until(lambda d: d.find_element(By.ID, 'health-metrics').is_displayed())

        self.browser.find_element(By.ID, 'id_heart_rate').clear()
        self.browser.find_element(By.ID, 'id_heart_rate').send_keys('60')
        self.browser.find_element(By.ID, 'id_blood_pressure').clear()
        self.browser.find_element(By.ID, 'id_blood_pressure').send_keys('120/80')
        self.browser.find_element(By.ID, 'id_fatigue_level').clear()
        self.browser.find_element(By.ID, 'id_fatigue_level').send_keys('2')

        Select(self.browser.find_element(By.ID, 'id_injury_status')).select_by_value('none')
        Select(self.browser.find_element(By.ID, 'id_recovery_status')).select_by_value('good')

        # Submit form inside health metrics panel
        self.browser.find_element(By.CSS_SELECTOR, "#health-metrics button[type='submit']").click()
        WebDriverWait(self.browser, 10).until(lambda d: 'health metrics were saved' in d.page_source.lower())

