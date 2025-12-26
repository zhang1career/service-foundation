from openai import OpenAI

from common.components.singleton import Singleton


class AigcBestAPI(Singleton):

    def __init__(self, base_url, api_key, model):
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
