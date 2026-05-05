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
class AdminAppUnitTests(TestCase):
    """
    Comprehensive Unit tests for the Admin app.
    Run these ONLY with: python manage.py test Admin --tag=unit
    """

    def setUp(self):
        self.client = Client()
        self.test_user = User.objects.create_user(
            email='unit_Admin@example.com',
            name='Unit Admin',
            password='testpassword123',
            role='athlete',
            is_approved=True
        )
        self.test_superuser = User.objects.create_superuser(
            email='admin_Admin@example.com',
            name='Admin',
            password='testpassword123',
        )

    def test_model_creation(self):
        """Basic model creation verification."""
        self.assertEqual(self.test_user.email, 'unit_Admin@example.com')
        self.assertTrue(self.test_user.check_password('testpassword123'))

    def test_user_authentication(self):
        """Test that user can log in and access system."""
        login = self.client.login(email='unit_Admin@example.com', password='testpassword123')
        self.assertTrue(login)

    def test_admin_dashboard_access_for_superuser(self):
        """Unit Test: Ensures only superusers can access the admin dashboard."""
        self.client.login(email='admin_Admin@example.com', password='testpassword123')
        response = self.client.get(reverse('admin_app:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'Admin/dashboard.html')

    def test_non_superuser_redirected_from_admin_dashboard(self):
        """Unit Test: Verifies non-superusers are redirected from the admin dashboard."""
        self.client.login(email='unit_Admin@example.com', password='testpassword123')
        response = self.client.get(reverse('admin_app:dashboard'))
        self.assertRedirects(response, reverse('home'))

    def test_user_approval_and_rejection_flow(self):
        """Unit Test: Admin can approve coach accounts and toggle active status."""
        pending_coach = User.objects.create_user(
            email='pending_coach@example.com',
            name='Pending Coach',
            password='password',
            role='coach',
            is_approved=False,
            is_active=True,
        )
        toggle_user = User.objects.create_user(
            email='toggle@example.com',
            name='Toggle User',
            password='password',
            role='athlete',
            is_approved=True,
            is_active=True,
        )

        self.client.login(email='admin_Admin@example.com', password='testpassword123')

        self.client.post(reverse('admin_app:approve_coach', args=[pending_coach.id]))
        pending_coach.refresh_from_db()
        self.assertTrue(pending_coach.is_approved)

        self.client.post(reverse('admin_app:toggle_user_status', args=[toggle_user.id]))
        toggle_user.refresh_from_db()
        self.assertFalse(toggle_user.is_active)



# ==============================================================================
# ------------------------------ SELENIUM TESTS --------------------------------
# ==============================================================================

@tag('selenium')
class AdminAppSeleniumTests(StaticLiveServerTestCase):
    """
    Comprehensive Selenium end-to-end tests for the Admin app.
    Run these ONLY with: python manage.py test Admin --tag=selenium
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
            email='selenium_Admin@example.com',
            name='Selenium Admin',
            password='pass12345',
            role='athlete',
            is_approved=True,
        )
        self.admin = User.objects.create_superuser(
            email='selenium_admin_staff@example.com',
            name='Selenium Staff',
            password='pass12345',
        )
        self.pending_coach = User.objects.create_user(
            email='selenium_pending_coach@example.com',
            name='Selenium Pending Coach',
            password='pass12345',
            role='coach',
            is_approved=False,
            is_active=True,
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
        self._login('selenium_Admin@example.com', 'pass12345')
        WebDriverWait(self.browser, 10).until(lambda d: 'login' not in d.current_url)

    def test_admin_can_approve_coach_from_users_page(self):
        """Selenium Test: Admin approves a coach from the users screen."""
        self._login('selenium_admin_staff@example.com', 'pass12345')
        WebDriverWait(self.browser, 10).until(
            lambda d: d.current_url.endswith(reverse('admin_app:dashboard'))
        )

        self.browser.get(self.live_server_url + reverse('admin_app:users'))
        WebDriverWait(self.browser, 10).until(
            lambda d: 'Pending Coach Approvals' in d.page_source
        )

        approve_button = self.browser.find_element(By.XPATH, "//button[contains(., 'Approve Coach')]")
        approve_button.click()
        WebDriverWait(self.browser, 10).until(
            lambda d: 'approved successfully' in d.page_source.lower()
        )
        self.pending_coach.refresh_from_db()
        self.assertTrue(self.pending_coach.is_approved)

