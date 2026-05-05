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
from player.models import Sport, CoachRequest, AthleteCoach, DailyRoutine, AthleteSport
from user.models import CoachProfile, AthleteProfile

from datetime import date

# ==============================================================================
# -------------------------------- UNIT TESTS ----------------------------------
# ==============================================================================

@tag('unit')
class CoachAppUnitTests(TestCase):
    """
    Comprehensive Unit tests for the coach app.
    Run these ONLY with: python manage.py test coach --tag=unit
    """

    def setUp(self):
        self.client = Client()
        self.test_user = User.objects.create_user(
            email='unit_coach@example.com',
            name='Unit Coach',
            password='testpassword123',
            role='athlete',
            is_approved=True
        )
        self.test_superuser = User.objects.create_superuser(
            email='admin_coach@example.com',
            name='Admin',
            password='testpassword123',
        )

    def test_model_creation(self):
        """Basic model creation verification."""
        self.assertEqual(self.test_user.email, 'unit_coach@example.com')
        self.assertTrue(self.test_user.check_password('testpassword123'))

    def test_user_authentication(self):
        """Test that user can log in and access system."""
        login = self.client.login(email='unit_coach@example.com', password='testpassword123')
        self.assertTrue(login)

    def test_coach_dashboard_access(self):
        """Unit Test: Ensures only authenticated coaches can access the coach dashboard."""
        coach_user = User.objects.create_user(
            email='coach_user@example.com',
            name='Coach User',
            password='password',
            role='coach',
            is_approved=True
        )
        self.client.login(email='coach_user@example.com', password='password')
        response = self.client.get(reverse('coach:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'coach/dashboard.html')

    def test_non_coach_redirected_from_dashboard(self):
        """Unit Test: Verifies non-coach users are redirected from the coach dashboard."""
        self.client.login(email='unit_coach@example.com', password='testpassword123') # Logs in as an athlete
        response = self.client.get(reverse('coach:dashboard'))
        self.assertRedirects(response, reverse('home'))


# ==============================================================================
# ------------------------------ SELENIUM TESTS --------------------------------
# ==============================================================================

@tag('selenium')
class CoachAppSeleniumTests(StaticLiveServerTestCase):
    """
    Comprehensive Selenium end-to-end tests for the coach app.
    Run these ONLY with: python manage.py test coach --tag=selenium
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
        self.coach = User.objects.create_user(
            email='selenium_coach@example.com',
            name='Selenium Coach',
            password='pass12345',
            role='coach',
            is_approved=True,
        )
        CoachProfile.objects.get_or_create(user=self.coach, defaults={'sport': self.sport})
        # Ensure sport is assigned so coach can accept requests
        self.coach.coach_profile.sport = self.sport
        self.coach.coach_profile.save()

        self.athlete = User.objects.create_user(
            email='athlete@example.com',
            name='Test Athlete',
            password='password',
            role='athlete',
            is_approved=True
        )
        AthleteProfile.objects.get_or_create(user=self.athlete)
        AthleteSport.objects.get_or_create(athlete=self.athlete, sport=self.sport)

        self.pending_request = CoachRequest.objects.create(
            athlete=self.athlete,
            coach=self.coach,
            sport=self.sport,
            status='pending',
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

    def test_basic_login_flow(self):
        """Selenium Test: Verify basic login works across apps."""
        self._login('selenium_coach@example.com', 'pass12345')
        WebDriverWait(self.browser, 10).until(
            lambda d: d.current_url.endswith(reverse('coach:dashboard'))
        )

    def test_coach_can_accept_request_and_create_routine(self):
        """Selenium Test: Coach accepts an athlete request and creates a routine."""
        self._login('selenium_coach@example.com', 'pass12345')
        WebDriverWait(self.browser, 10).until(lambda d: d.current_url.endswith(reverse('coach:dashboard')))

        # Accept the pending request
        self.browser.get(self.live_server_url + reverse('coach:athlete_requests'))
        WebDriverWait(self.browser, 10).until(lambda d: 'Pending Requests' in d.page_source or 'Pending' in d.page_source)

        accept_button = self.browser.find_element(By.XPATH, "//button[contains(., 'Accept')]")
        accept_button.click()

        WebDriverWait(self.browser, 10).until(lambda d: 'Accepted' in d.page_source or 'accepted' in d.page_source)
        self.assertTrue(
            AthleteCoach.objects.filter(athlete=self.athlete, coach=self.coach, sport=self.sport, is_active=True).exists()
        )

        # Create a routine
        self.browser.get(self.live_server_url + reverse('coach:create_routine_select'))
        WebDriverWait(self.browser, 10).until(lambda d: 'Create Routine' in d.page_source)
        self.browser.find_element(By.LINK_TEXT, 'Create Routine').click()

        WebDriverWait(self.browser, 10).until(lambda d: d.find_element(By.ID, 'title').is_displayed())
        self.browser.find_element(By.ID, 'title').send_keys('Selenium Routine')
        Select(self.browser.find_element(By.ID, 'sport')).select_by_visible_text(self.sport.name)
        Select(self.browser.find_element(By.ID, 'day_of_week')).select_by_value('monday')
        self.browser.find_element(By.ID, 'workout_date').send_keys(date.today().isoformat())
        self.browser.find_element(By.ID, 'start_time').send_keys('09:00')
        self.browser.find_element(By.ID, 'end_time').send_keys('10:00')
        self.browser.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

        WebDriverWait(self.browser, 10).until(lambda d: 'Routine created' in d.page_source)
        self.assertTrue(DailyRoutine.objects.filter(athlete=self.athlete, coach=self.coach, title='Selenium Routine').exists())

