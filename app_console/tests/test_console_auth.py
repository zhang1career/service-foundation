"""Session auth and staff gate for /console/."""

from django.contrib.auth.models import User
from django.test import TestCase, override_settings


@override_settings(CONSOLE_MONITORING_JSON_TOKEN="secret-token")
class ConsoleStaffGateTest(TestCase):
    def setUp(self):
        User.objects.create_user("staff1", "staff1@example.com", "pw", is_staff=True)
        User.objects.create_user("plain1", "plain1@example.com", "pw", is_staff=False)

    def test_login_page_ok_anonymous(self):
        r = self.client.get("/console/login/")
        self.assertEqual(r.status_code, 200)

    def test_dashboard_redirects_when_anonymous(self):
        r = self.client.get("/console/", follow=False)
        self.assertEqual(r.status_code, 302)
        self.assertIn("/console/login", r["Location"])

    def test_dashboard_forbidden_when_not_staff(self):
        self.assertTrue(self.client.login(username="plain1", password="pw"))
        r = self.client.get("/console/")
        self.assertEqual(r.status_code, 403)

    def test_dashboard_ok_when_staff(self):
        self.assertTrue(self.client.login(username="staff1", password="pw"))
        r = self.client.get("/console/")
        self.assertEqual(r.status_code, 200)

    def test_monitoring_json_exempt_from_session_auth(self):
        r = self.client.get("/console/api/monitoring.json?token=secret-token")
        self.assertEqual(r.status_code, 200)

    def test_login_rejects_non_staff_credentials(self):
        r = self.client.post(
            "/console/login/",
            {"username": "plain1", "password": "pw", "next": "/console/"},
        )
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "is_staff")

    def test_login_accepts_staff(self):
        r = self.client.post(
            "/console/login/",
            {"username": "staff1", "password": "pw", "next": "/console/"},
        )
        self.assertEqual(r.status_code, 302)
        self.assertTrue(r["Location"].endswith("/console/"))
