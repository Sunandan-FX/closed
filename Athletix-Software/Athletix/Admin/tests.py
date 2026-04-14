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

from user.models import AthleteProfile, MedicalProfile


User = get_user_model()


class AdminAppTests(TestCase):
    def setUp(self):
        self.staff_user = User.objects.create_user(
            email='staff@example.com',
            name='Staff User',
            password='pass12345',
            role='coach',
            is_staff=True,
        )
        self.normal_user = User.objects.create_user(
            email='athlete@example.com',
            name='Athlete User',
            password='pass12345',
            role='athlete',
        )
        self.pending_coach = User.objects.create_user(
            email='pendingcoach@example.com',
            name='Pending Coach',
            password='pass12345',
            role='coach',
            is_approved=False,
            is_active=False,
        )

    def test_dashboard_accessible_for_staff(self):
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse('admin_app:dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_dashboard_denied_for_non_staff(self):
        self.client.force_login(self.normal_user)
        response = self.client.get(reverse('admin_app:dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('home'))

    def test_approve_coach_view_approves_pending_coach(self):
        self.client.force_login(self.staff_user)
        response = self.client.post(
            reverse('admin_app:approve_coach', args=[self.pending_coach.id])
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('admin_app:users'))

        self.pending_coach.refresh_from_db()
        self.assertTrue(self.pending_coach.is_approved)
        self.assertTrue(self.pending_coach.is_active)

    def test_toggle_user_status_post_toggles_user_activity(self):
        self.client.force_login(self.staff_user)
        self.assertTrue(self.normal_user.is_active)

        response = self.client.post(
            reverse('admin_app:toggle_user_status', args=[self.normal_user.id])
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('admin_app:users'))

        self.normal_user.refresh_from_db()
        self.assertFalse(self.normal_user.is_active)

    def test_approve_coach_get_does_not_change_status(self):
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse('admin_app:approve_coach', args=[self.pending_coach.id]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('admin_app:users'))

        self.pending_coach.refresh_from_db()
        self.assertFalse(self.pending_coach.is_approved)

    def test_edit_medical_user_updates_medical_profile_fields(self):
        medical_user = User.objects.create_user(
            email='medic@example.com',
            name='Medic User',
            password='pass12345',
            role='medical',
            is_active=True,
        )
        self.client.force_login(self.staff_user)
        response = self.client.post(
            reverse('admin_app:edit_user', args=[medical_user.id]),
            data={
                'name': 'Updated Medic',
                'email': 'medic@example.com',
                'phone': '01700000000',
                'address': 'Dhaka',
                'blood_group': 'A+',
                'is_active': 'on',
                'license_no': 'MED-7788',
                'specialty': 'Sports Medicine',
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('admin_app:users'))

        medical_user.refresh_from_db()
        self.assertEqual(medical_user.name, 'Updated Medic')
        self.assertEqual(medical_user.phone, '01700000000')
        self.assertEqual(medical_user.address, 'Dhaka')
        self.assertEqual(medical_user.blood_group, 'A+')
        self.assertTrue(medical_user.is_active)
        self.assertTrue(hasattr(medical_user, 'medical_profile'))
        self.assertEqual(medical_user.medical_profile.license_no, 'MED-7788')
        self.assertEqual(medical_user.medical_profile.specialty, 'Sports Medicine')

    def test_edit_athlete_user_creates_athlete_profile_if_missing(self):
        athlete_user = User.objects.create_user(
            email='athlete-new@example.com',
            name='Athlete New',
            password='pass12345',
            role='athlete',
            is_active=True,
        )
        self.assertFalse(AthleteProfile.objects.filter(user=athlete_user).exists())
        self.client.force_login(self.staff_user)
        response = self.client.post(
            reverse('admin_app:edit_user', args=[athlete_user.id]),
            data={
                'name': 'Athlete Updated',
                'email': 'athlete-new@example.com',
                'phone': '',
                'address': '',
                'blood_group': '',
                'is_active': 'on',
                'age': '19',
                'height': "5'8\"",
                'weight': '64 kg',
                'fitness_level': 'high',
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('admin_app:users'))
        self.assertTrue(AthleteProfile.objects.filter(user=athlete_user).exists())
        athlete_profile = AthleteProfile.objects.get(user=athlete_user)
        self.assertEqual(athlete_profile.age, 19)
        self.assertEqual(athlete_profile.height, "5'8\"")
        self.assertEqual(athlete_profile.weight, '64 kg')
        self.assertEqual(athlete_profile.fitness_level, 'high')

    def test_edit_medical_user_creates_medical_profile_if_missing(self):
        medical_user = User.objects.create_user(
            email='medic-new@example.com',
            name='Medic New',
            password='pass12345',
            role='medical',
            is_active=True,
        )
        self.assertFalse(MedicalProfile.objects.filter(user=medical_user).exists())
        self.client.force_login(self.staff_user)
        response = self.client.post(
            reverse('admin_app:edit_user', args=[medical_user.id]),
            data={
                'name': 'Medic New',
                'email': 'medic-new@example.com',
                'phone': '',
                'address': '',
                'blood_group': '',
                'is_active': 'on',
                'license_no': 'MED-001',
                'specialty': 'Physiotherapy',
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('admin_app:users'))
        self.assertTrue(MedicalProfile.objects.filter(user=medical_user).exists())


@tag('selenium')
class AdminAppSeleniumTests(StaticLiveServerTestCase):
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
        self.staff_user = User.objects.create_user(
            email='selenium_admin_staff@example.com',
            name='Selenium Staff',
            password='pass12345',
            role='coach',
            is_staff=True,
        )
        self.pending_coach = User.objects.create_user(
            email='selenium_pending_coach@example.com',
            name='Pending Selenium Coach',
            password='pass12345',
            role='coach',
            is_approved=False,
            is_active=False,
        )
        self.normal_user = User.objects.create_user(
            email='selenium_normal_user@example.com',
            name='Selenium Normal User',
            password='pass12345',
            role='athlete',
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

    def test_staff_can_open_admin_app_dashboard(self):
        self._login('selenium_admin_staff@example.com', 'pass12345')
        self.browser.get(self.live_server_url + reverse('admin_app:dashboard'))
        WebDriverWait(self.browser, 10).until(lambda d: 'admin-app' in d.current_url)
        self.assertIn('Admin App', self.browser.page_source)

    def test_staff_can_approve_pending_coach_from_users_page(self):
        self._login('selenium_admin_staff@example.com', 'pass12345')
        self.browser.get(self.live_server_url + reverse('admin_app:users'))
        approve_button = WebDriverWait(self.browser, 10).until(
            lambda d: d.find_element(
                By.XPATH,
                f"//form[contains(@action, '/admin-app/approve-coach/{self.pending_coach.id}/')]//button"
            )
        )
        approve_button.click()
        WebDriverWait(self.browser, 10).until(
            lambda _: User.objects.get(id=self.pending_coach.id).is_approved
        )
        self.pending_coach.refresh_from_db()
        self.assertTrue(self.pending_coach.is_approved)
        self.assertTrue(self.pending_coach.is_active)

    def test_staff_can_toggle_user_status_from_users_page(self):
        self._login('selenium_admin_staff@example.com', 'pass12345')
        self.browser.get(self.live_server_url + reverse('admin_app:users'))
        toggle_button = WebDriverWait(self.browser, 10).until(
            lambda d: d.find_element(
                By.XPATH,
                f"//form[contains(@action, '/admin-app/users/{self.normal_user.id}/toggle-status/')]//button"
            )
        )
        toggle_button.click()
        WebDriverWait(self.browser, 10).until(
            lambda _: not User.objects.get(id=self.normal_user.id).is_active
        )
        self.normal_user.refresh_from_db()
        self.assertFalse(self.normal_user.is_active)
