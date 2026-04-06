from types import SimpleNamespace

from django.test import SimpleTestCase

from app_user.utils.user_serialization import user_to_console_dict, user_to_public_dict


class TestUserSerialization(SimpleTestCase):
    def test_user_to_public_dict_parses_ext_json(self):
        user = SimpleNamespace(
            id=10,
            username="n",
            email="e@x",
            phone="",
            avatar="",
            status=1,
            auth_status=0,
            ctrl_status=0,
            ctrl_reason="",
            ext='{"role":"admin"}',
            ct=100,
            ut=200,
        )
        data = user_to_public_dict(user)
        self.assertEqual(data["id"], 10)
        self.assertEqual(data["ext"], {"role": "admin"})
        self.assertEqual(data["auth_status"], 0)
        self.assertEqual(data["ctrl_status"], 0)

    def test_user_to_public_dict_malformed_ext_becomes_empty_dict(self):
        user = SimpleNamespace(
            id=1,
            username="n",
            email="",
            phone="",
            avatar="",
            status=0,
            auth_status=None,
            ctrl_status=0,
            ctrl_reason="",
            ext="{",
            ct=0,
            ut=0,
        )
        data = user_to_public_dict(user)
        self.assertEqual(data["ext"], {})
        self.assertEqual(data["auth_status"], 0)

    def test_public_dict_never_exposes_ctrl_reason(self):
        user = SimpleNamespace(
            id=1,
            username="n",
            email="",
            phone="",
            avatar="",
            status=1,
            auth_status=0,
            ctrl_status=1,
            ctrl_reason="内部风控细节",
            ext="{}",
            ct=0,
            ut=0,
        )
        self.assertEqual(user_to_public_dict(user)["ctrl_reason"], "")
        self.assertEqual(user_to_console_dict(user)["ctrl_reason"], "内部风控细节")
