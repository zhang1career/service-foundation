from unittest import TestCase
from unittest.mock import patch

from app_aibroker.outbound_client import (
    aibroker_ask_and_answer_with_template,
    aibroker_embed,
    aibroker_text_generate,
)


class OutboundClientTest(TestCase):
    @patch("app_aibroker.outbound_client.aibroker_http_post")
    def test_text_generate_success(self, http_post_mock):
        http_post_mock.return_value = {"text": " done "}
        result = aibroker_text_generate(
            "hello",
            idempotency_key="idem-1",
        )
        self.assertEqual(result, "done")
        http_post_mock.assert_called_once()
        payload = http_post_mock.call_args.args[0]
        self.assertEqual(payload["prompt"], "hello")
        self.assertEqual(http_post_mock.call_args.kwargs.get("idempotency_key"), "idem-1")

    @patch("app_aibroker.outbound_client.aibroker_http_post")
    def test_text_generate_error_raises(self, http_post_mock):
        http_post_mock.side_effect = RuntimeError("bad")
        with self.assertRaises(RuntimeError):
            aibroker_text_generate("hello")

    @patch("app_aibroker.outbound_client.aibroker_http_post_embeddings")
    def test_embed_success(self, http_post_embeddings_mock):
        http_post_embeddings_mock.return_value = {"embedding": [1, "2.5"]}
        vec = aibroker_embed("hello")
        self.assertEqual(vec, [1.0, 2.5])

    @patch("app_aibroker.outbound_client.aibroker_http_post")
    def test_text_generate_with_template_id_payload(self, http_post_mock):
        http_post_mock.return_value = {"text": "ok"}
        aibroker_text_generate(
            "",
            template_id=42,
            variables={"text": "t"},
        )
        payload = http_post_mock.call_args.args[0]
        self.assertEqual(payload["template_id"], 42)
        self.assertEqual(payload["prompt"], "")
        self.assertEqual(payload["variables"]["text"], "t")

    @patch("app_aibroker.outbound_client.aibroker_http_post")
    def test_ask_and_answer_with_template_uses_template_id_in_payload(self, http_post_mock):
        http_post_mock.return_value = {"text": "ans"}
        out = aibroker_ask_and_answer_with_template(
            "body",
            "role",
            "q",
            template_id=7,
        )
        self.assertEqual(out, "ans")
        payload = http_post_mock.call_args.args[0]
        self.assertEqual(payload["template_id"], 7)
        self.assertIn("question", payload["variables"])
