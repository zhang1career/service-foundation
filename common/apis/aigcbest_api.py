from django.conf import settings
from openai import OpenAI

from common.components.singleton import Singleton


def _effective_credential(override: str | None, setting_attr: str) -> str:
    """Use stripped non-empty override; otherwise read settings (single fallback)."""
    if override is not None:
        s = str(override).strip()
        if s:
            return s
    return str(getattr(settings, setting_attr, "")).strip()


class AigcBestAPI(Singleton):

    def __init__(self, model, base_url: str | None = None, api_key: str | None = None):
        base_url = _effective_credential(base_url, "AIGC_API_URL")
        api_key = _effective_credential(api_key, "AIGC_API_KEY")
        if not base_url or not api_key:
            raise RuntimeError(
                "OpenAI-compatible base URL and API key are required "
                "(set provider base_url/api_key or AIGC_API_URL and AIGC_API_KEY)"
            )
        self.client = OpenAI(
            base_url=base_url,
            api_key=api_key
        )
        self.model = model

    def chat(self, content: str, temperature):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": content
                },
            ],
            temperature=temperature
        )
        if not response:
            return None
        return response.choices[0].message.content

    def embed(self, input_text: str, dimensions=None):
        if dimensions is not None and int(dimensions) > 0:
            response = self.client.embeddings.create(
                model=self.model,
                input=input_text,
                dimensions=int(dimensions),
            )
        else:
            response = self.client.embeddings.create(
                model=self.model,
                input=input_text,
            )
        if not response or not response.data:
            raise RuntimeError("empty embedding response")
        return list(response.data[0].embedding)
