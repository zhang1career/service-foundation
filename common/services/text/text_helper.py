import os
from typing import Any

from openai import OpenAI

from common.components.singleton import Singleton

# Vector dimension for compatibility with MongoDB index and component_repo.NAME_VEC_DIM
VEC_DIM = 384


class TextHelper(Singleton):
    def __init__(self):
        base_url = os.environ.get("AIGC_API_URL", "")
        api_key = os.environ.get("AIGC_API_KEY", "")
        embedding_model = os.environ.get("AIGC_EMBEDDING_MODEL", "text-embedding-3-small")
        self._client = OpenAI(base_url=base_url, api_key=api_key)
        self._model = embedding_model

    def generate_vector(self, text: str) -> list[float]:
        response = self._client.embeddings.create(
            model=self._model,
            input=text,
            dimensions=VEC_DIM,
        )
        return response.data[0].embedding

    def find_most_similar_str(self, text_list: list[str], match_text: str) -> tuple[str, Any]:
        # lazy load
        import numpy as np
        from sklearn.metrics.pairwise import cosine_similarity
        # prepare data
        querying_vector = self.generate_vector(match_text)
        querying_vector_ndarray = np.array(querying_vector)
        # query
        similarities = []
        for _text in text_list:
            _existed_vector = self.generate_vector(_text)
            _existed_vector_ndarray = np.array(_existed_vector)
            _similarity = cosine_similarity([querying_vector_ndarray], [_existed_vector_ndarray])[0][0]
            similarities.append((_similarity, _text))
        # sort by similarity and take top_k
        similarities.sort(key=lambda x: x[0], reverse=True)
        similarity, matched_text = similarities[0]
        # return
        return matched_text, similarity
