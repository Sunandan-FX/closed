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
from medical_staff.models import AthleteHealthRecord, MedicalFeedback

# ==============================================================================
# -------------------------------- UNIT TESTS ----------------------------------
# ==============================================================================

@tag('unit')
class MedicalstaffAppUnitTests(TestCase):
    """
    Comprehensive Unit tests for the medical_staff app.
    Run these ONLY with: python manage.py test medical_staff --tag=unit
    """

    def setUp(self):
        self.client = Client()
        self.test_user = User.objects.create_user(
            email='unit_medical_staff@example.com',
            name='Unit Medicalstaff',
            password='testpassword123',
            role='athlete',
            is_approved=True
        )
        self.test_superuser = User.objects.create_superuser(
            email='admin_medical_staff@example.com',
            name='Admin',
            password='testpassword123',
        )

    def test_model_creation(self):
        """Basic model creation verification."""
        self.assertEqual(self.test_user.email, 'unit_medical_staff@example.com')
        self.assertTrue(self.test_user.check_password('testpassword123'))

    def test_user_authentication(self):
        """Test that user can log in and access system."""
        login = self.client.login(email='unit_medical_staff@example.com', password='testpassword123')
        self.assertTrue(login)

    def test_medical_dashboard_access(self):
        """Unit Test: Ensures only authenticated medical staff can access the medical dashboard."""
        medical_user = User.objects.create_user(
            email='medical_user@example.com',
            name='Medical User',
            password='password',
            role='medical',
            is_approved=True
        )
        self.client.login(email=medical_user.email, password='password')
        response = self.client.get(reverse('medical_staff:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'medical_staff/dashboard.html')

    def test_non_medical_redirected_from_dashboard(self):
        """Unit Test: Verifies non-medical users are redirected from the medical dashboard."""
        self.client.login(email='unit_medical_staff@example.com', password='testpassword123') # Logs in as an athlete
        response = self.client.get(reverse('medical_staff:dashboard'))
        self.assertRedirects(response, reverse('home'))

    def test_add_health_record_post_creates_record(self):
        """Unit Test: Medical staff can create an AthleteHealthRecord via POST."""
        medical_user = User.objects.create_user(
            email='medical_add@example.com',
            name='Medical Add',
            password='password',
            role='medical',
            is_approved=True,
        )
        athlete = User.objects.create_user(
            email='athlete_health@example.com',
            name='Athlete Health',
            password='password',
            role='athlete',
            is_approved=True,
        )
        self.client.login(email=medical_user.email, password='password')
        response = self.client.post(
            reverse('medical_staff:add_health_record'),
            data={
                'athlete': athlete.id,
                'heart_rate': 60,
                'blood_pressure': '120/80',
                'weight_kg': '70',
                'sleep_hours': '7.5',
                'fatigue_level': 3,
                'injury_status': 'none',
                'injury_notes': '',
                'recovery_status': 'good',
                'performance_notes': 'OK',
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(AthleteHealthRecord.objects.filter(athlete=athlete, medical_staff=medical_user).exists())



# ==============================================================================
# ------------------------------ SELENIUM TESTS --------------------------------
# ==============================================================================

@tag('selenium')
class MedicalstaffAppSeleniumTests(StaticLiveServerTestCase):
    """
    Comprehensive Selenium end-to-end tests for the medical_staff app.
    Run these ONLY with: python manage.py test medical_staff --tag=selenium
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
        self.user = User.objects.create_user(
            email='selenium_medical_staff@example.com',
            name='Selenium Medicalstaff',
            password='pass12345',
            role='medical',
            is_approved=True,
        )
        self.athlete = User.objects.create_user(
            email='selenium_medical_athlete@example.com',
            name='Selenium Athlete',
            password='pass12345',
            role='athlete',
            is_approved=True,
        )
        self.health_record = AthleteHealthRecord.objects.create(
            athlete=self.athlete,
            medical_staff=self.user,
            heart_rate=62,
            blood_pressure='120/80',
            weight_kg=70,
            sleep_hours=7,
            fatigue_level=3,
            injury_status='none',
            injury_notes='',
            recovery_status='good',
            performance_notes='OK',
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
        self._login('selenium_medical_staff@example.com', 'pass12345')
        WebDriverWait(self.browser, 10).until(lambda d: 'login' not in d.current_url)

    def test_medical_staff_can_submit_feedback_on_dashboard(self):
        """Selenium Test: Medical staff submits feedback via the dashboard form."""
        self._login('selenium_medical_staff@example.com', 'pass12345')
        WebDriverWait(self.browser, 10).until(lambda d: d.current_url.endswith(reverse('medical_staff:dashboard')))

        Select(self.browser.find_element(By.ID, 'id_athlete')).select_by_value(str(self.athlete.id))
        Select(self.browser.find_element(By.ID, 'id_feedback_type')).select_by_value('training')
        self.browser.find_element(By.ID, 'id_title').send_keys('Selenium Feedback')
        self.browser.find_element(By.ID, 'id_feedback').send_keys('Hydrate and rest.')
        self.browser.find_element(By.ID, 'id_recommendations').send_keys('Mobility for 20 minutes.')
        self.browser.find_element(By.CSS_SELECTOR, "form[action$='/feedback/add/'] button[type='submit']").click()

        WebDriverWait(self.browser, 10).until(
            lambda d: 'Medical feedback submitted successfully.' in d.page_source
        )
        self.assertTrue(MedicalFeedback.objects.filter(title='Selenium Feedback', medical_staff=self.user).exists())

    def test_medical_staff_can_view_athlete_health_detail(self):
        """Selenium Test: Medical staff opens athlete health detail from dashboard table."""
        self._login('selenium_medical_staff@example.com', 'pass12345')
        WebDriverWait(self.browser, 10).until(lambda d: d.current_url.endswith(reverse('medical_staff:dashboard')))

        self.browser.find_element(By.LINK_TEXT, 'View Full Profile').click()
        WebDriverWait(self.browser, 10).until(
            lambda d: d.current_url.endswith(reverse('medical_staff:athlete_health_detail', args=[self.athlete.id]))
        )
        WebDriverWait(self.browser, 10).until(lambda d: 'Health Records History' in d.page_source)

