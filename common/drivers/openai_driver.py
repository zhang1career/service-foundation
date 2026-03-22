import os

from openai import OpenAI

from common.components.singleton import Singleton


class OpenAIDriver(Singleton):
    """Singleton driver for OpenAI client (e.g. AIGC embedding API)."""

    def __init__(self) -> None:
        base_url = os.environ.get("AIGC_API_URL", "")
        api_key = os.environ.get("AIGC_API_KEY", "")
        self._client = OpenAI(base_url=base_url, api_key=api_key)

    @property
    def client(self) -> OpenAI:
        return self._client
