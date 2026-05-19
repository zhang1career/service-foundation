from __future__ import annotations

import json
from unittest.mock import patch

from django.test import SimpleTestCase
from rest_framework import status
from rest_framework.test import APIRequestFactory

from app_textmod.enums.suggestion_enum import TextmodSuggestionEnum
from app_textmod.services.ac_automaton import build_ac_from_normalized_patterns
from app_textmod.views.scan_view import TextmodScanView
from common.consts.response_const import RET_OK


class TextmodScanViewTest(SimpleTestCase):
    def setUp(self) -> None:
        self.factory = APIRequestFactory()

    @patch("app_textmod.views.scan_view.TextmodScanService.scan")
    def test_scan_ok(self, scan) -> None:
        scan.return_value = {"lexicon_id": 1, "suggestion": "pass", "label_id": 0, "hits": []}
        request = self.factory.post("/api/textmod/scan", data={"text": "hi", "lexicon_id": 1}, format="json")
        response = TextmodScanView.as_view()(request)
        response.render()
        payload = json.loads(response.content)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(payload["errorCode"], RET_OK)
        self.assertEqual(payload["data"]["suggestion"], "pass")

    @patch("app_textmod.services.textmod_scan_service.load_automaton_for_version")
    @patch("app_textmod.services.textmod_scan_service.get_published_version")
    def test_scan_service_maps_positions(self, get_ver, load_auto) -> None:
        from app_textmod.models import LexiconVersion

        ver = LexiconVersion(
            id=9,
            lex_id=1,
            seq=3,
            status=1,
            blob_relpath="1/3.bin",
            blob_checksum="x",
            entry_count=1,
            published_at=1,
            ct=1,
        )
        get_ver.return_value = ver
        auto = build_ac_from_normalized_patterns(
            [("bad", 3, "bad", 42, 7, int(TextmodSuggestionEnum.BLOCK), 0)]
        )
        load_auto.return_value = auto

        from app_textmod.services.textmod_scan_service import TextmodScanService

        out = TextmodScanService.scan(text="xxbadxx", lexicon_id=1)
        self.assertEqual(out["suggestion"], "block")
        self.assertEqual(len(out["hits"]), 1)
        self.assertEqual(out["hits"][0]["word"], "bad")
        self.assertEqual((out["hits"][0]["start_pos"], out["hits"][0]["end_pos"]), (2, 5))
