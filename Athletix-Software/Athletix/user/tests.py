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

from user.models import User
from player.models import Sport

# ==============================================================================
# -------------------------------- UNIT TESTS ----------------------------------
# ==============================================================================

@tag('unit')
class UserAppUnitTests(TestCase):
    """
    Comprehensive Unit tests for the user app.
    Run these ONLY with: python manage.py test user --tag=unit
    """

    def setUp(self):
        self.client = Client()
        self.test_user = User.objects.create_user(
            email='unit_user@example.com',
            name='Unit User',
            password='testpassword123',
            role='athlete',
            is_approved=True
        )
        self.test_superuser = User.objects.create_superuser(
            email='admin_user@example.com',
            name='Admin',
            password='testpassword123',
        )

    def test_model_creation(self):
        """Basic model creation verification."""
        self.assertEqual(self.test_user.email, 'unit_user@example.com')
        self.assertTrue(self.test_user.check_password('testpassword123'))

    def test_user_authentication(self):
        """Test that user can log in and access system."""
        login = self.client.login(email='unit_user@example.com', password='testpassword123')
        self.assertTrue(login)

    def test_home_view_accessible(self):
        """Unit Test: Asserts that the home page loads correctly for anonymous users."""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home.html')

    def test_unapproved_user_login_fails(self):
        """Unit Test: Ensures users pending approval cannot log in."""
        unapproved_user = User.objects.create_user(
            email='unapproved@example.com',
            name='Unapproved User',
            password='password', 
            is_approved=False
        )
        login_attempt = self.client.login(email='unapproved@example.com', password='password')
        self.assertFalse(login_attempt, "Login should fail for unapproved users.")

    def test_dashboard_redirects_based_on_role(self):
        """Unit Test: Verifies that users are redirected to the correct dashboard."""
        # Athlete
        self.client.login(email='unit_user@example.com', password='testpassword123')
        response = self.client.get(reverse('dashboard'))
        self.assertRedirects(response, reverse('player-dashboard'))

        # Coach
        coach_user = User.objects.create_user(email='coach@example.com', name='Coach', password='password', role='coach', is_approved=True)
        self.client.login(email='coach@example.com', password='password')
        response = self.client.get(reverse('dashboard'))
        self.assertRedirects(response, reverse('coach-dashboard'))
        
        # Medical Staff
        medical_user = User.objects.create_user(email='medical@example.com', name='Medical', password='password', role='medical', is_approved=True)
        self.client.login(email='medical@example.com', password='password')
        response = self.client.get(reverse('dashboard'))
        self.assertRedirects(response, reverse('medical-dashboard'))


# ==============================================================================
# ------------------------------ SELENIUM TESTS --------------------------------
# ==============================================================================

@tag('selenium')
class UserAppSeleniumTests(StaticLiveServerTestCase):
    """
    Comprehensive Selenium end-to-end tests for the user app.
    Run these ONLY with: python manage.py test user --tag=selenium
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
            email='selenium_user@example.com',
            name='Selenium User',
            password='pass12345',
            role='athlete',
            is_approved=True,
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
        self._login('selenium_user@example.com', 'pass12345')
        import time
        time.sleep(2)
        self.assertNotIn('login', self.browser.current_url)

    def test_full_signup_and_profile_edit_flow(self):
        """Selenium Test: Simulates a full user signup, login, and profile update."""
        # Signup
        self.browser.get(self.live_server_url + reverse('signup'))
        self.browser.find_element(By.ID, 'name').send_keys('New Selenium User')
        self.browser.find_element(By.ID, 'email').send_keys('new_selenium@example.com')
        self.browser.find_element(By.ID, 'password').send_keys('new_password123')
        self.browser.find_element(By.ID, 'password2').send_keys('new_password123')
        self.browser.find_element(By.ID, 'role').send_keys('athlete')
        self.browser.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        # Manually approve the user for the test
        new_user = User.objects.get(email='new_selenium@example.com')
        new_user.is_approved = True
        new_user.save()

        # Login
        self._login('new_selenium@example.com', 'new_password123')
        self.assertTrue(self.browser.current_url.endswith(reverse('player_dashboard')), "Failed to redirect to dashboard after login.")

        # Edit Profile
        self.browser.get(self.live_server_url + reverse('profile_edit'))
        phone_field = self.browser.find_element(By.ID, 'phone')
        phone_field.clear()
        phone_field.send_keys('1234567890')
        self.browser.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        self.assertTrue(self.browser.current_url.endswith(reverse('profile')), "Failed to redirect to profile after edit.")
        
        # Verify the change
        self.user.refresh_from_db()
        self.assertEqual(User.objects.get(email='new_selenium@example.com').phone, '1234567890')


# ==============================================================================
# ------------------------------ SELENIUM TESTS --------------------------------
# ==============================================================================

@tag('selenium')
class UserAppSeleniumTests(StaticLiveServerTestCase):
    """
    Comprehensive Selenium end-to-end tests for the user app.
    Run these ONLY with: python manage.py test user --tag=selenium
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
            email='selenium_user@example.com',
            name='Selenium User',
            password='pass12345',
            role='athlete',
            is_approved=True,
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
        self._login('selenium_user@example.com', 'pass12345')
        import time
        time.sleep(2)
        self.assertNotIn('login', self.browser.current_url)

