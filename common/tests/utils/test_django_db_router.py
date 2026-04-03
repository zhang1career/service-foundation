from types import SimpleNamespace

from django.test import SimpleTestCase

from common.utils.django_db_router import AppLabelDatabaseRouter


class _UserRouter(AppLabelDatabaseRouter):
    route_app_labels = frozenset({"app_user"})
    route_db_alias = "user_rw"


def _model(app_label: str):
    return SimpleNamespace(_meta=SimpleNamespace(app_label=app_label))


class AppLabelDatabaseRouterTests(SimpleTestCase):
    def setUp(self):
        self.router = _UserRouter()

    def test_db_for_read_routed_app(self):
        self.assertEqual(self.router.db_for_read(_model("app_user")), "user_rw")

    def test_db_for_read_other_app(self):
        self.assertIsNone(self.router.db_for_read(_model("other")))

    def test_allow_migrate_matching_db(self):
        self.assertTrue(self.router.allow_migrate("user_rw", "app_user"))

    def test_allow_migrate_wrong_db(self):
        self.assertFalse(self.router.allow_migrate("default", "app_user"))

    def test_allow_migrate_untracked_app(self):
        self.assertIsNone(self.router.allow_migrate("default", "other"))

    def test_allow_relation_involving_routed_app(self):
        u = _model("app_user")
        o = _model("other")
        self.assertTrue(self.router.allow_relation(u, o))

    def test_allow_relation_no_routed_app(self):
        self.assertIsNone(self.router.allow_relation(_model("a"), _model("b")))
