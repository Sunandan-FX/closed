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
class ChatAppUnitTests(TestCase):
    """
    Comprehensive Unit tests for the chat app.
    Run these ONLY with: python manage.py test chat --tag=unit
    """

    def setUp(self):
        self.client = Client()
        self.test_user = User.objects.create_user(
            email='unit_chat@example.com',
            name='Unit Chat',
            password='testpassword123',
            role='athlete',
            is_approved=True
        )
        self.test_superuser = User.objects.create_superuser(
            email='admin_chat@example.com',
            name='Admin',
            password='testpassword123',
        )

    def test_model_creation(self):
        """Basic model creation verification."""
        self.assertEqual(self.test_user.email, 'unit_chat@example.com')
        self.assertTrue(self.test_user.check_password('testpassword123'))

    def test_user_authentication(self):
        """Test that user can log in and access system."""
        login = self.client.login(email='unit_chat@example.com', password='testpassword123')
        self.assertTrue(login)

    def test_conversations_list_view_requires_login(self):
        """Unit Test: Ensures the conversations list page requires authentication."""
        response = self.client.get(reverse('chat:conversations_list'))
        self.assertRedirects(response, reverse('login') + '?next=' + reverse('chat:conversations_list'))

    def test_start_conversation_creates_conversation(self):
        """Unit Test: Verifies that starting a conversation creates a new Conversation object."""
        user1 = self.test_user
        user2 = User.objects.create_user(
            email='user2@example.com',
            name='User Two',
            password='password',
            role='coach',
            is_approved=True,
        )
        self.client.login(email=user1.email, password='testpassword123')
        
        from chat.models import Conversation
        self.assertEqual(Conversation.objects.count(), 0)
        self.client.post(reverse('chat:start_conversation'), data={'recipient_id': user2.id})
        self.assertEqual(Conversation.objects.count(), 1)
        self.assertTrue(
            Conversation.objects.filter(participant1=user1, participant2=user2).exists()
            or Conversation.objects.filter(participant1=user2, participant2=user1).exists()
        )



# ==============================================================================
# ------------------------------ SELENIUM TESTS --------------------------------
# ==============================================================================

@tag('selenium')
class ChatAppSeleniumTests(StaticLiveServerTestCase):
    """
    Comprehensive Selenium end-to-end tests for the chat app.
    Run these ONLY with: python manage.py test chat --tag=selenium
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
            email='selenium_chat@example.com',
            name='Selenium Chat',
            password='pass12345',
            role='athlete',
            is_approved=True,
        )
        self.recipient = User.objects.create_user(
            email='selenium_chat_recipient@example.com',
            name='Selenium Recipient',
            password='pass12345',
            role='coach',
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
        self._login('selenium_chat@example.com', 'pass12345')
        WebDriverWait(self.browser, 10).until(lambda d: 'login' not in d.current_url)

    def test_start_conversation_and_send_message(self):
        """Selenium Test: Start a chat and send a message."""
        self._login('selenium_chat@example.com', 'pass12345')

        self.browser.get(self.live_server_url + reverse('chat:start_conversation'))
        WebDriverWait(self.browser, 10).until(
            lambda d: d.find_element(By.CSS_SELECTOR, "form#start-chat-form")
        )

        first_radio = self.browser.find_element(By.CSS_SELECTOR, "input[name='recipient_id']")
        first_radio.click()
        self.browser.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

        WebDriverWait(self.browser, 10).until(
            lambda d: reverse('chat:conversation_detail', args=[1])[:6] in d.current_url
            or 'conversation/' in d.current_url
        )

        message_box = self.browser.find_element(By.CSS_SELECTOR, "textarea[name='content']")
        message_box.send_keys('Hello from Selenium!')
        self.browser.find_element(By.CSS_SELECTOR, "button.btn-send").click()

        WebDriverWait(self.browser, 10).until(
            lambda d: 'Hello from Selenium!' in d.page_source
        )

