from django.test import TransactionTestCase

from app_user.models import User
from app_user.services.auth_service import AuthService


class TestAuthService(TransactionTestCase):
    databases = {"default", "user_rw"}

    def setUp(self):
        User.objects.using("user_rw").all().delete()

    def tearDown(self):
        User.objects.using("user_rw").all().delete()

    def test_register_and_login(self):
        registered = AuthService.register(username="user1", password="pass1234", email="user1@example.com")
        self.assertIn("access_token", registered)
        self.assertEqual(registered["user"]["username"], "user1")

        logged_in = AuthService.login(login_key="user1", password="pass1234")
        self.assertIn("access_token", logged_in)
        self.assertEqual(logged_in["user"]["username"], "user1")
