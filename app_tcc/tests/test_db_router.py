"""TCC database router wiring."""

from django.test import SimpleTestCase

from app_tcc.db_routers import ReadWriteRouter
from app_tcc.models import TccParticipant


class TccReadWriteRouterTests(SimpleTestCase):
    def setUp(self):
        self.router = ReadWriteRouter()

    def test_routes_app_tcc_reads_and_writes(self):
        self.assertEqual(self.router.db_for_read(TccParticipant), "tcc_rw")
        self.assertEqual(self.router.db_for_write(TccParticipant), "tcc_rw")

    def test_allow_migrate_tcc_only_on_alias(self):
        self.assertTrue(self.router.allow_migrate("tcc_rw", "app_tcc"))
        self.assertFalse(self.router.allow_migrate("default", "app_tcc"))

    def test_allow_migrate_other_apps_not_forced(self):
        self.assertIsNone(self.router.allow_migrate("default", "auth"))
