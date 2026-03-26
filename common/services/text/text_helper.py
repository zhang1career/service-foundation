import os
from typing import Any

from common.components.singleton import Singleton
from common.services.aibroker_client import aibroker_embed

# Vector dimension for compatibility with MongoDB index and component_repo.NAME_VEC_DIM
VEC_DIM = 384


class TextHelper(Singleton):
    """
    Text embeddings via app_aibroker HTTP only (no in-process OpenAI client).
    Register an ai_model with capability=3 (embedding) in the broker.
    """

    def __init__(self):
        self._dimensions = int(os.environ.get("AIGC_EMBEDDING_DIMENSIONS", str(VEC_DIM)))

    def generate_vector(self, text: str) -> list[float]:
        return aibroker_embed(text, dimensions=self._dimensions)

    def find_most_similar_str(self, text_list: list[str], match_text: str) -> tuple[str, Any]:
        import numpy as np
        from sklearn.metrics.pairwise import cosine_similarity

        querying_vector = self.generate_vector(match_text)
        querying_vector_ndarray = np.array(querying_vector)
        similarities = []
        for _text in text_list:
            _existed_vector = self.generate_vector(_text)
            _existed_vector_ndarray = np.array(_existed_vector)
            _similarity = cosine_similarity([querying_vector_ndarray], [_existed_vector_ndarray])[0][0]
            similarities.append((_similarity, _text))
        similarities.sort(key=lambda x: x[0], reverse=True)
        similarity, matched_text = similarities[0]
        return matched_text, similarity
