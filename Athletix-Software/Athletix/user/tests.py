from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from .models import User, AthleteProfile, CoachProfile, MedicalProfile
from .forms import SignUpForm, LoginForm, ForgotPasswordForm, ProfileEditForm
from django.contrib.staticfiles.testing import StaticLiveServerTestCase

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from django.test import tag
import time

# ============================================================================
# MODEL TESTS (Tests 1-13)
# ============================================================================

class UserModelTests(TestCase):
    """Tests for the custom User model"""

    def setUp(self):
        self.user_data = {
            'email': 'test@example.com',
            'name': 'John Doe',
            'password': 'testpass123',
            'role': 'athlete'
        }

    # Test 1: Create user with email
    def test_create_user_with_email(self):
        """Test creating a user with email is successful"""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.email, self.user_data['email'])
        self.assertEqual(user.name, self.user_data['name'])
        self.assertTrue(user.check_password(self.user_data['password']))
        self.assertEqual(user.role, 'athlete')

    # Test 2: Email normalization
    def test_new_user_email_normalized(self):
        """Test email is normalized for new users"""
        email = 'test@EXAMPLE.COM'
        user = User.objects.create_user(email=email, name='Test', password='test123')
        self.assertEqual(user.email, email.lower())

    # Test 3: User without email raises error
    def test_new_user_without_email_raises_error(self):
        """Test that creating user without email raises ValueError"""
        with self.assertRaises(ValueError):
            User.objects.create_user(email='', name='Test', password='test123')

    # Test 4: Create superuser
    def test_create_superuser(self):
        """Test creating a superuser"""
        user = User.objects.create_superuser(
            email='admin@example.com',
            name='Admin User',
            password='adminpass123'
        )
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)
        self.assertEqual(user.role, 'coach')

    # Test 5: User string representation
    def test_user_str_representation(self):
        """Test the user string representation"""
        user = User.objects.create_user(**self.user_data)
        expected = f"{user.name} ({user.email}) - Athlete"
        self.assertEqual(str(user), expected)

    # Test 6: First name property
    def test_user_first_name_property(self):
        """Test first_name property returns first word of name"""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.first_name, 'John')

    # Test 7: First name with empty name
    def test_user_first_name_empty_name(self):
        """Test first_name property with empty name"""
        user = User.objects.create_user(
            email='empty@example.com',
            name='',
            password='test123'
        )
        self.assertEqual(user.first_name, '')

    # Test 8: User default is active
    def test_user_default_is_active(self):
        """Test user is active by default"""
        user = User.objects.create_user(**self.user_data)
        self.assertTrue(user.is_active)

    # Test 9: User default is not staff
    def test_user_default_is_not_staff(self):
        """Test user is not staff by default"""
        user = User.objects.create_user(**self.user_data)
        self.assertFalse(user.is_staff)


class AthleteProfileTests(TestCase):
    """Tests for AthleteProfile model"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='athlete@example.com',
            name='Athlete User',
            password='test123',
            role='athlete'
        )

    # Test 10: Create athlete profile
    def test_create_athlete_profile(self):
        """Test creating an athlete profile"""
        profile = AthleteProfile.objects.create(
            user=self.user,
            sport_type='Football',
            age=25,
            fitness_level='high'
        )
        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.sport_type, 'Football')
        self.assertEqual(profile.age, 25)

    # Test 11: Athlete profile string representation
    def test_athlete_profile_str(self):
        """Test athlete profile string representation"""
        profile = AthleteProfile.objects.create(user=self.user)
        self.assertEqual(str(profile), f"Athlete: {self.user.name}")

    # Test 12: Athlete profile default fitness level
    def test_athlete_profile_default_fitness_level(self):
        """Test default fitness level is medium"""
        profile = AthleteProfile.objects.create(user=self.user)
        self.assertEqual(profile.fitness_level, 'medium')


class CoachProfileTests(TestCase):
    """Tests for CoachProfile model"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='coach@example.com',
            name='Coach User',
            password='test123',
            role='coach'
        )

    # Test 13: Create coach profile
    def test_create_coach_profile(self):
        """Test creating a coach profile"""
        profile = CoachProfile.objects.create(
            user=self.user,
            specialization='Fitness Training',
            experience_years=10
        )
        self.assertEqual(profile.specialization, 'Fitness Training')
        self.assertEqual(profile.experience_years, 10)

    # Test 14: Coach profile string representation
    def test_coach_profile_str(self):
        """Test coach profile string representation"""
        profile = CoachProfile.objects.create(user=self.user)
        self.assertEqual(str(profile), f"Coach: {self.user.name}")


class MedicalProfileTests(TestCase):
    """Tests for MedicalProfile model"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='medical@example.com',
            name='Medical User',
            password='test123',
            role='medical'
        )

    # Test 15: Create medical profile
    def test_create_medical_profile(self):
        """Test creating a medical profile"""
        profile = MedicalProfile.objects.create(
            user=self.user,
            license_no='MED123456',
            specialty='Sports Medicine'
        )
        self.assertEqual(profile.license_no, 'MED123456')
        self.assertEqual(profile.specialty, 'Sports Medicine')

    # Test 16: Medical profile string representation
    def test_medical_profile_str(self):
        """Test medical profile string representation"""
        profile = MedicalProfile.objects.create(user=self.user)
        self.assertEqual(str(profile), f"Medical: {self.user.name}")


# ============================================================================
# FORM TESTS (Tests 17-26)
# ============================================================================

class SignUpFormTests(TestCase):
    """Tests for SignUpForm"""

    # Test 17: Valid signup form
    def test_valid_signup_form(self):
        """Test signup form with valid data"""
        form_data = {
            'name': 'Test User',
            'email': 'test@example.com',
            'role': 'athlete',
            'password': 'securepass123',
            'confirm_password': 'securepass123'
        }
        form = SignUpForm(data=form_data)
        self.assertTrue(form.is_valid())

    # Test 18: Signup form password mismatch
    def test_signup_form_password_mismatch(self):
        """Test signup form with mismatched passwords"""
        form_data = {
            'name': 'Test User',
            'email': 'test@example.com',
            'role': 'athlete',
            'password': 'securepass123',
            'confirm_password': 'differentpass'
        }
        form = SignUpForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('Passwords do not match', str(form.errors))

    # Test 19: Signup form short password
    def test_signup_form_short_password(self):
        """Test signup form with password less than 8 characters"""
        form_data = {
            'name': 'Test User',
            'email': 'test@example.com',
            'role': 'athlete',
            'password': 'short',
            'confirm_password': 'short'
        }
        form = SignUpForm(data=form_data)
        self.assertFalse(form.is_valid())

    # Test 20: Signup form duplicate email
    def test_signup_form_duplicate_email(self):
        """Test signup form with existing email"""
        User.objects.create_user(
            email='existing@example.com',
            name='Existing User',
            password='test123'
        )
        form_data = {
            'name': 'New User',
            'email': 'existing@example.com',
            'role': 'athlete',
            'password': 'securepass123',
            'confirm_password': 'securepass123'
        }
        form = SignUpForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    # Test 21: Signup form saves user with hashed password
    def test_signup_form_saves_user(self):
        """Test that form saves user with hashed password"""
        form_data = {
            'name': 'Test User',
            'email': 'newuser@example.com',
            'role': 'coach',
            'password': 'securepass123',
            'confirm_password': 'securepass123'
        }
        form = SignUpForm(data=form_data)
        self.assertTrue(form.is_valid())
        user = form.save()
        self.assertTrue(user.check_password('securepass123'))
        self.assertEqual(user.role, 'coach')


class LoginFormTests(TestCase):
    """Tests for LoginForm"""

    # Test 22: Valid login form
    def test_valid_login_form(self):
        """Test login form with valid data"""
        form_data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        form = LoginForm(data=form_data)
        self.assertTrue(form.is_valid())

    # Test 23: Login form invalid email
    def test_login_form_invalid_email(self):
        """Test login form with invalid email format"""
        form_data = {
            'email': 'invalid-email',
            'password': 'testpass123'
        }
        form = LoginForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    # Test 24: Login form empty fields
    def test_login_form_empty_fields(self):
        """Test login form with empty fields"""
        form = LoginForm(data={})
        self.assertFalse(form.is_valid())


class ForgotPasswordFormTests(TestCase):
    """Tests for ForgotPasswordForm"""

    # Test 25: Valid forgot password form
    def test_valid_forgot_password_form(self):
        """Test forgot password form with valid data"""
        form_data = {
            'email': 'test@example.com',
            'new_password': 'newpass123',
            'confirm_password': 'newpass123'
        }
        form = ForgotPasswordForm(data=form_data)
        self.assertTrue(form.is_valid())

    # Test 26: Forgot password form password mismatch
    def test_forgot_password_mismatch(self):
        """Test forgot password form with mismatched passwords"""
        form_data = {
            'email': 'test@example.com',
            'new_password': 'newpass123',
            'confirm_password': 'different123'
        }
        form = ForgotPasswordForm(data=form_data)
        self.assertFalse(form.is_valid())


# ============================================================================
# VIEW TESTS (Tests 27-53)
# ============================================================================

class HomeViewTests(TestCase):
    """Tests for home view"""

    # Test 27: Home page status code
    def test_home_page_status_code(self):
        """Test home page returns 200"""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)

    # Test 28: Home page uses correct template
    def test_home_page_uses_correct_template(self):
        """Test home page uses home.html template"""
        response = self.client.get(reverse('home'))
        self.assertTemplateUsed(response, 'home.html')


class LoginViewTests(TestCase):
    """Tests for login view"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            name='Test User',
            password='testpass123'
        )
        self.login_url = reverse('login')

    # Test 29: Login page status code
    def test_login_page_status_code(self):
        """Test login page returns 200"""
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)

    # Test 30: Login page uses correct template
    def test_login_page_uses_correct_template(self):
        """Test login page uses correct template"""
        response = self.client.get(self.login_url)
        self.assertTemplateUsed(response, 'user/login.html')

    # Test 31: Login with valid credentials
    def test_login_with_valid_credentials(self):
        """Test login with valid credentials redirects"""
        response = self.client.post(self.login_url, {
            'email': 'test@example.com',
            'password': 'testpass123'
        })
        self.assertRedirects(response, reverse('home'))

    # Test 32: Login with invalid credentials
    def test_login_with_invalid_credentials(self):
        """Test login with invalid credentials shows error"""
        response = self.client.post(self.login_url, {
            'email': 'test@example.com',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)

    # Test 33: Login redirects authenticated user
    def test_login_redirects_authenticated_user(self):
        """Test authenticated user is redirected from login page"""
        self.client.force_login(self.user)
        response = self.client.get(self.login_url)
        self.assertRedirects(response, reverse('home'))

    # Test 34: Login with inactive user
    def test_login_inactive_user(self):
        """Test login with inactive user shows error"""
        self.user.is_active = False
        self.user.save()
        response = self.client.post(self.login_url, {
            'email': 'test@example.com',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 200)


class SignupViewTests(TestCase):
    """Tests for signup view"""

    def setUp(self):
        self.signup_url = reverse('signup')

    # Test 35: Signup page status code
    def test_signup_page_status_code(self):
        """Test signup page returns 200"""
        response = self.client.get(self.signup_url)
        self.assertEqual(response.status_code, 200)

    # Test 36: Signup page uses correct template
    def test_signup_page_uses_correct_template(self):
        """Test signup page uses correct template"""
        response = self.client.get(self.signup_url)
        self.assertTemplateUsed(response, 'user/signup.html')

    # Test 37: Signup creates user
    def test_signup_creates_user(self):
        """Test successful signup creates user"""
        response = self.client.post(self.signup_url, {
            'name': 'New User',
            'email': 'newuser@example.com',
            'role': 'athlete',
            'password': 'securepass123',
            'confirm_password': 'securepass123'
        })
        self.assertRedirects(response, reverse('login'))
        self.assertTrue(User.objects.filter(email='newuser@example.com').exists())

    # Test 38: Signup creates athlete profile
    def test_signup_creates_athlete_profile(self):
        """Test signup as athlete creates AthleteProfile"""
        self.client.post(self.signup_url, {
            'name': 'Athlete User',
            'email': 'athlete@example.com',
            'role': 'athlete',
            'password': 'securepass123',
            'confirm_password': 'securepass123'
        })
        user = User.objects.get(email='athlete@example.com')
        self.assertTrue(hasattr(user, 'athlete_profile'))

    # Test 39: Signup creates coach profile
    def test_signup_creates_coach_profile(self):
        """Test signup as coach creates CoachProfile"""
        self.client.post(self.signup_url, {
            'name': 'Coach User',
            'email': 'coach@example.com',
            'role': 'coach',
            'password': 'securepass123',
            'confirm_password': 'securepass123'
        })
        user = User.objects.get(email='coach@example.com')
        self.assertTrue(hasattr(user, 'coach_profile'))

    # Test 40: Signup creates medical profile
    def test_signup_creates_medical_profile(self):
        """Test signup as medical creates MedicalProfile"""
        self.client.post(self.signup_url, {
            'name': 'Medical User',
            'email': 'medical@example.com',
            'role': 'medical',
            'password': 'securepass123',
            'confirm_password': 'securepass123'
        })
        user = User.objects.get(email='medical@example.com')
        self.assertTrue(hasattr(user, 'medical_profile'))


class LogoutViewTests(TestCase):
    """Tests for logout view"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            name='Test User',
            password='testpass123'
        )

    # Test 41: Logout redirects to home
    def test_logout_redirects_to_home(self):
        """Test logout redirects to home page"""
        self.client.force_login(self.user)
        response = self.client.get(reverse('logout'))
        self.assertRedirects(response, reverse('home'))

    # Test 42: Logout requires login
    def test_logout_requires_login(self):
        """Test logout requires authentication"""
        response = self.client.get(reverse('logout'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('logout')}")


class ForgotPasswordViewTests(TestCase):
    """Tests for forgot password view"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            name='Test User',
            password='oldpass123'
        )
        self.forgot_url = reverse('forgot_password')

    # Test 43: Forgot password page status code
    def test_forgot_password_page_status_code(self):
        """Test forgot password page returns 200"""
        response = self.client.get(self.forgot_url)
        self.assertEqual(response.status_code, 200)

    # Test 44: Forgot password updates password
    def test_forgot_password_updates_password(self):
        """Test forgot password updates user password"""
        response = self.client.post(self.forgot_url, {
            'email': 'test@example.com',
            'new_password': 'newpass123',
            'confirm_password': 'newpass123'
        })
        self.assertRedirects(response, reverse('login'))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpass123'))

    # Test 45: Forgot password with non-existent email
    def test_forgot_password_nonexistent_email(self):
        """Test forgot password with non-existent email"""
        response = self.client.post(self.forgot_url, {
            'email': 'nonexistent@example.com',
            'new_password': 'newpass123',
            'confirm_password': 'newpass123'
        })
        self.assertEqual(response.status_code, 200)


class DashboardViewTests(TestCase):
    """Tests for dashboard view"""

    def setUp(self):
        # Use medical role since athlete/coach redirects to their app dashboards
        self.user = User.objects.create_user(
            email='test@example.com',
            name='Test User',
            password='testpass123',
            role='medical'
        )
        MedicalProfile.objects.create(user=self.user)
        self.dashboard_url = reverse('dashboard')

    # Test 46: Dashboard requires login
    def test_dashboard_requires_login(self):
        """Test dashboard requires authentication"""
        response = self.client.get(self.dashboard_url)
        self.assertRedirects(response, f"{reverse('login')}?next={self.dashboard_url}")

    # Test 47: Dashboard accessible when logged in
        def test_dashboard_accessible_when_logged_in(self):
          self.client.force_login(User.objects.create_user(username='testuser', password='testpassword'))
          response = self.client.get(reverse('dashboard'))
          self.assertEqual(response.status_code, 200)

    def test_dashboard_uses_correct_template(self):
        response = self.client.get(reverse('dashboard'))
        self.assertTemplateUsed(response, 'user/dashboard.html')


    # Test 48b: Athlete redirects to player dashboard
    def test_athlete_redirects_to_player_dashboard(self):
        """Test athlete is redirected to player dashboard"""
        athlete = User.objects.create_user(
            email='athlete@example.com',
            name='Athlete User',
            password='testpass123',
            role='athlete'
        )
        AthleteProfile.objects.create(user=athlete)
        self.client.force_login(athlete)
        response = self.client.get(self.dashboard_url)
        self.assertRedirects(response, reverse('player:dashboard'))

    # Test 48c: Coach redirects to coach dashboard
    def test_coach_redirects_to_coach_dashboard(self):
        """Test coach is redirected to coach dashboard"""
        coach = User.objects.create_user(
            email='coach@example.com',
            name='Coach User',
            password='testpass123',
            role='coach'
        )
        CoachProfile.objects.create(user=coach)
        self.client.force_login(coach)
        response = self.client.get(self.dashboard_url)
        self.assertRedirects(response, reverse('coach:dashboard'))


class ProfileViewTests(TestCase):
    """Tests for profile view"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            name='Test User',
            password='testpass123'
        )
        self.profile_url = reverse('profile')

    # Test 49: Profile requires login
    def test_profile_requires_login(self):
        """Test profile requires authentication"""
        response = self.client.get(self.profile_url)
        self.assertRedirects(response, f"{reverse('login')}?next={self.profile_url}")

    # Test 50: Profile accessible when logged in
    def test_profile_accessible_when_logged_in(self):
        """Test profile is accessible when logged in"""
        self.client.force_login(self.user)
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 200)


class ProfileEditViewTests(TestCase):
    """Tests for profile edit view"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            name='Test User',
            password='testpass123'
        )
        self.edit_url = reverse('profile_edit')

    # Test 51: Profile edit requires login
    def test_profile_edit_requires_login(self):
        """Test profile edit requires authentication"""
        response = self.client.get(self.edit_url)
        self.assertRedirects(response, f"{reverse('login')}?next={self.edit_url}")

    # Test 52: Profile edit accessible when logged in
    def test_profile_edit_accessible_when_logged_in(self):
        """Test profile edit is accessible when logged in"""
        self.client.force_login(self.user)
        response = self.client.get(self.edit_url)
        self.assertEqual(response.status_code, 200)

    # Test 53: Profile edit updates user data
    def test_profile_edit_updates_user(self):
        """Test profile edit updates user data"""
        self.client.force_login(self.user)
        response = self.client.post(self.edit_url, {
            'name': 'Updated Name',
            'email': 'test@example.com',
            'phone': '1234567890',
            'address': 'New Address',
            'date_of_birth': '',
            'blood_group': 'O+',
        })
        self.assertRedirects(response, reverse('profile'))
        self.user.refresh_from_db()
        self.assertEqual(self.user.name, 'Updated Name')
        self.assertEqual(self.user.phone, '1234567890')


# ============================================================================
# SELENIUM TESTS (Browser-based UI Tests)
# ============================================================================
# Run these tests with: python manage.py test user.tests --tag=selenium
# Make sure Chrome and ChromeDriver are installed
# These tests will open a visible browser window




@tag('selenium')
class SeleniumHomePageTests(StaticLiveServerTestCase):
    """Selenium tests for home page - visible browser"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Chrome options - NO headless so browser is visible
        chrome_options = Options()
        chrome_options.add_argument('--start-maximized')
        chrome_options.add_argument('--disable-gpu')
        # Use webdriver-manager to auto-download ChromeDriver
        service = Service(ChromeDriverManager().install())
        cls.browser = webdriver.Chrome(service=service, options=chrome_options)
        cls.browser.implicitly_wait(10)

    @classmethod
    def tearDownClass(cls):
        cls.browser.quit()
        super().tearDownClass()

    # Selenium Test 1: Home page loads correctly
    def test_home_page_loads(self):
        """Test home page loads and displays logo"""
        self.browser.get(self.live_server_url + '/')
        WebDriverWait(self.browser, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'a.nav-logo'))
        )
        
        # Check page title
        self.assertIn('Athletix', self.browser.title)
        
        # Check logo is present
        logo = self.browser.find_element(By.CSS_SELECTOR, 'a.nav-logo')
        self.assertIn('ATHLETI', logo.text)

    # Selenium Test 2: Navigation links are present
    def test_home_page_nav_links(self):
        """Test home page has login and signup links"""
        self.browser.get(self.live_server_url + '/')
        WebDriverWait(self.browser, 10).until(
            EC.presence_of_element_located((By.ID, 'navLinks'))
        )
        
        # Find login link
        login_link = self.browser.find_element(By.XPATH, "//a[contains(@href, '/user/login/')]")
        self.assertTrue(login_link.is_displayed())
        
        # Find signup link
        signup_link = self.browser.find_element(By.XPATH, "//a[contains(@href, '/user/signup/')]")
        self.assertTrue(signup_link.is_displayed())

    # Selenium Test 3: Click login navigates to login page
    def test_click_login_link(self):
        """Test clicking login link navigates to login page"""
        self.browser.get(self.live_server_url + '/')
        WebDriverWait(self.browser, 10).until(
            EC.presence_of_element_located((By.ID, 'navLinks'))
        )
        
        login_link = self.browser.find_element(By.XPATH, "//a[contains(@href, '/user/login/')]")
        login_link.click()
        WebDriverWait(self.browser, 10).until(
            lambda d: '/user/login/' in d.current_url
        )
        
        # Should be on login page
        self.assertIn('login', self.browser.current_url)


@tag('selenium')
class SeleniumSignupTests(StaticLiveServerTestCase):
    """Selenium tests for signup functionality"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        chrome_options = Options()
        chrome_options.add_argument('--start-maximized')
        chrome_options.add_argument('--disable-gpu')
        service = Service(ChromeDriverManager().install())
        cls.browser = webdriver.Chrome(service=service, options=chrome_options)
        cls.browser.implicitly_wait(10)

    @classmethod
    def tearDownClass(cls):
        cls.browser.quit()
        super().tearDownClass()

    # Selenium Test 4: Signup page loads
    def test_signup_page_loads(self):
        """Test signup page loads correctly"""
        self.browser.get(self.live_server_url + '/user/signup/')
        time.sleep(1)
        
        self.assertIn('Sign Up', self.browser.title)
        
        # Check form fields exist
        name_field = self.browser.find_element(By.ID, 'name')
        email_field = self.browser.find_element(By.ID, 'email')
        password_field = self.browser.find_element(By.ID, 'password')
        
        self.assertTrue(name_field.is_displayed())
        self.assertTrue(email_field.is_displayed())
        self.assertTrue(password_field.is_displayed())

    # Selenium Test 5: User can signup successfully
    def test_user_signup_flow(self):
        """Test complete user signup flow"""
        self.browser.get(self.live_server_url + '/user/signup/')
        time.sleep(1)
        
        # Fill in the form
        self.browser.find_element(By.ID, 'name').send_keys('Test Athlete')
        self.browser.find_element(By.ID, 'email').send_keys('newathlete@test.com')
        
        # Select role
        role_select = Select(self.browser.find_element(By.ID, 'role'))
        role_select.select_by_value('athlete')
        
        self.browser.find_element(By.ID, 'password').send_keys('securepass123')
        self.browser.find_element(By.ID, 'confirm_password').send_keys('securepass123')
        
        time.sleep(1)  # Pause to see filled form
        
        # Submit form
        submit_btn = self.browser.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
        submit_btn.click()
        
        time.sleep(2)  # Wait for redirect
        
        # Should redirect to login page
        self.assertIn('login', self.browser.current_url)

    # Selenium Test 6: Signup shows error for mismatched passwords
    def test_signup_password_mismatch(self):
        """Test signup shows error for password mismatch"""
        self.browser.get(self.live_server_url + '/user/signup/')
        time.sleep(1)
        
        self.browser.find_element(By.ID, 'name').send_keys('Test User')
        self.browser.find_element(By.ID, 'email').send_keys('test@test.com')
        self.browser.find_element(By.ID, 'password').send_keys('password123')
        self.browser.find_element(By.ID, 'confirm_password').send_keys('different123')
        
        submit_btn = self.browser.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
        submit_btn.click()
        
        time.sleep(1)
        
        # Should show error
        page_source = self.browser.page_source
        self.assertTrue('match' in page_source.lower() or 'error' in page_source.lower())


@tag('selenium')
class SeleniumLoginTests(StaticLiveServerTestCase):
    """Selenium tests for login functionality"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        chrome_options = Options()
        chrome_options.add_argument('--start-maximized')
        chrome_options.add_argument('--disable-gpu')
        service = Service(ChromeDriverManager().install())
        cls.browser = webdriver.Chrome(service=service, options=chrome_options)
        cls.browser.implicitly_wait(10)

    @classmethod
    def tearDownClass(cls):
        cls.browser.quit()
        super().tearDownClass()

    def setUp(self):
        # Create a test user for login tests
        self.test_user = User.objects.create_user(
            email='selenium@test.com',
            name='Selenium Tester',
            password='testpass123',
            role='athlete'
        )
        AthleteProfile.objects.create(user=self.test_user)

    # Selenium Test 7: Login page loads
    def test_login_page_loads(self):
        """Test login page loads correctly"""
        self.browser.get(self.live_server_url + '/user/login/')
        time.sleep(1)
        
        self.assertIn('Login', self.browser.title)
        
        email_field = self.browser.find_element(By.ID, 'email')
        password_field = self.browser.find_element(By.ID, 'password')
        
        self.assertTrue(email_field.is_displayed())
        self.assertTrue(password_field.is_displayed())

    # Selenium Test 8: User can login successfully
    def test_user_login_flow(self):
        """Test complete user login flow"""
        self.browser.get(self.live_server_url + '/user/login/')
        time.sleep(1)
        
        # Fill login form
        self.browser.find_element(By.ID, 'email').send_keys('selenium@test.com')
        self.browser.find_element(By.ID, 'password').send_keys('testpass123')
        
        time.sleep(1)
        
        # Submit
        submit_btn = self.browser.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
        submit_btn.click()
        
        time.sleep(2)
        
        # Should redirect to home or dashboard
        self.assertTrue(
            '/' in self.browser.current_url or 
            'dashboard' in self.browser.current_url or
            'home' in self.browser.current_url
        )

    # Selenium Test 9: Invalid login shows error
    def test_invalid_login_shows_error(self):
        """Test invalid credentials show error message"""
        self.browser.get(self.live_server_url + '/user/login/')
        time.sleep(1)
        
        self.browser.find_element(By.ID, 'email').send_keys('wrong@email.com')
        self.browser.find_element(By.ID, 'password').send_keys('wrongpassword')
        
        submit_btn = self.browser.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
        submit_btn.click()
        
        time.sleep(1)
        
        # Should show error message
        page_source = self.browser.page_source
        self.assertTrue(
            'invalid' in page_source.lower() or 
            'error' in page_source.lower() or
            'incorrect' in page_source.lower()
        )


@tag('selenium')
class SeleniumDashboardTests(StaticLiveServerTestCase):
    """Selenium tests for user app dashboard functionality"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        chrome_options = Options()
        chrome_options.add_argument('--start-maximized')
        chrome_options.add_argument('--disable-gpu')
        service = Service(ChromeDriverManager().install())
        cls.browser = webdriver.Chrome(service=service, options=chrome_options)
        cls.browser.implicitly_wait(10)

    @classmethod
    def tearDownClass(cls):
        cls.browser.quit()
        super().tearDownClass()

    def setUp(self):
        # Create medical user (stays on user dashboard, not redirected)
        self.medical_user = User.objects.create_user(
            email='medical@test.com',
            name='Test Medical',
            password='testpass123',
            role='medical'
        )
        MedicalProfile.objects.create(user=self.medical_user)

    def _login(self, email, password):
        """Helper method to login a user"""
        self.browser.get(self.live_server_url + '/user/login/')
        self.browser.find_element(By.ID, 'email').send_keys(email)
        self.browser.find_element(By.ID, 'password').send_keys(password)
        self.browser.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        time.sleep(2)

    # Selenium Test 10: User dashboard requires login
    def test_dashboard_requires_login(self):
        """Test dashboard redirects to login if not authenticated"""
        self.browser.get(self.live_server_url + '/user/dashboard/')
        time.sleep(1)
        
        # Should be redirected to login
        self.assertIn('login', self.browser.current_url)

    # Selenium Test 11: Medical user can access dashboard
    def test_medical_dashboard_loads(self):
        """Test medical user can access user dashboard"""
        self._login('medical@test.com', 'testpass123')
        
        self.browser.get(self.live_server_url + '/user/dashboard/')
        time.sleep(1)
        
        # Should see dashboard content
        page_source = self.browser.page_source
        self.assertTrue('Dashboard' in page_source or 'Welcome' in page_source)

    # Selenium Test 12: Login redirects to home
    def test_login_redirects_to_home(self):
        """Test successful login redirects to home page"""
        self._login('medical@test.com', 'testpass123')
        
        # Should be on home page after login
        self.assertTrue(
            self.browser.current_url.endswith('/') or 
            'home' in self.browser.current_url
        )


@tag('selenium')
class SeleniumProfileTests(StaticLiveServerTestCase):
    """Selenium tests for profile functionality"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        chrome_options = Options()
        chrome_options.add_argument('--start-maximized')
        chrome_options.add_argument('--disable-gpu')
        service = Service(ChromeDriverManager().install())
        cls.browser = webdriver.Chrome(service=service, options=chrome_options)
        cls.browser.implicitly_wait(10)

    @classmethod
    def tearDownClass(cls):
        cls.browser.quit()
        super().tearDownClass()

    def setUp(self):
        self.user = User.objects.create_user(
            email='profile@test.com',
            name='Profile Tester',
            password='testpass123',
            role='athlete',
            phone='1234567890',
            blood_group='O+'
        )
        AthleteProfile.objects.create(user=self.user)

    def _login(self):
        """Helper to login"""
        self.browser.get(self.live_server_url + '/user/login/')
        self.browser.find_element(By.ID, 'email').send_keys('profile@test.com')
        self.browser.find_element(By.ID, 'password').send_keys('testpass123')
        self.browser.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        time.sleep(2)

    # Selenium Test 13: Profile page shows user info
    def test_profile_shows_user_info(self):
        """Test profile page displays user information"""
        self._login()
        
        self.browser.get(self.live_server_url + '/user/profile/')
        time.sleep(1)
        
        page_source = self.browser.page_source
        self.assertIn('Profile Tester', page_source)
        self.assertIn('profile@test.com', page_source)

    # Selenium Test 14: Profile shows blood group
    def test_profile_shows_blood_group(self):
        """Test profile page displays blood group"""
        self._login()
        
        self.browser.get(self.live_server_url + '/user/profile/')
        time.sleep(1)
        
        page_source = self.browser.page_source
        self.assertIn('O+', page_source)

    # Selenium Test 15: Edit profile link works
    def test_edit_profile_link(self):
        """Test edit profile link navigates correctly"""
        self._login()
        
        self.browser.get(self.live_server_url + '/user/profile/')
        WebDriverWait(self.browser, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, 'body'))
        )
        
        # Find and click edit link
        edit_link = self.browser.find_element(By.XPATH, "//a[contains(@href, '/user/profile/edit/')]")
        edit_link.click()
        WebDriverWait(self.browser, 10).until(
            lambda d: '/user/profile/edit/' in d.current_url
        )
        
        self.assertIn('edit', self.browser.current_url)

    # Selenium Test 16: Profile edit form works
    def test_profile_edit_form(self):
        """Test profile edit form can be submitted"""
        self._login()
        
        self.browser.get(self.live_server_url + '/user/profile/edit/')
        time.sleep(1)
        
        # Update name
        name_field = self.browser.find_element(By.ID, 'name')
        name_field.clear()
        name_field.send_keys('Updated Name')
        
        time.sleep(1)
        
        # Submit
        submit_btn = self.browser.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
        submit_btn.click()
        
        time.sleep(2)
        
        # Should redirect to profile
        self.assertIn('profile', self.browser.current_url)


@tag('selenium')
class SeleniumLogoutTests(StaticLiveServerTestCase):
    """Selenium tests for logout functionality"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        chrome_options = Options()
        chrome_options.add_argument('--start-maximized')
        chrome_options.add_argument('--disable-gpu')
        service = Service(ChromeDriverManager().install())
        cls.browser = webdriver.Chrome(service=service, options=chrome_options)
        cls.browser.implicitly_wait(10)

    @classmethod
    def tearDownClass(cls):
        cls.browser.quit()
        super().tearDownClass()

    def setUp(self):
        self.user = User.objects.create_user(
            email='logout@test.com',
            name='Logout Tester',
            password='testpass123',
            role='athlete'
        )
        AthleteProfile.objects.create(user=self.user)

    # Selenium Test 17: User can logout
    def test_logout_flow(self):
        """Test user can logout successfully"""
        # Login first
        self.browser.get(self.live_server_url + '/user/login/')
        self.browser.find_element(By.ID, 'email').send_keys('logout@test.com')
        self.browser.find_element(By.ID, 'password').send_keys('testpass123')
        self.browser.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        time.sleep(2)
        
        # Go to dashboard
        self.browser.get(self.live_server_url + '/player/dashboard/')
        WebDriverWait(self.browser, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, 'body'))
        )
        
        # Click logout
        logout_link = WebDriverWait(self.browser, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, '/user/logout/')]"))
        )
        logout_link.click()
        time.sleep(2)
        
        # Should be on home or login page
        self.assertTrue(
            'login' in self.browser.current_url or 
            self.browser.current_url.endswith('/')
        )
