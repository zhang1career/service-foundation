from typing import Any

from common.components.singleton import Singleton


class TextHelper(Singleton):
    def __init__(self):
        # lazy load
        from sentence_transformers import SentenceTransformer
        # initialize properties
        self._trans = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

    def generate_vector(self, text: str) -> list[float]:
        # calculate
        embedding = self._trans.encode(text)
        embedded_vect = embedding.tolist()
        return embedded_vect

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
