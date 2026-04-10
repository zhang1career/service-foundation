class SimpleTextEmbeddingProvider:
    """
    Minimal deterministic embedding for local/prototype usage.
    """

    @staticmethod
    def encode(text):
        normalized = str(text or "").lower()
        terms = normalized.split()
        return [
            float(len(normalized)),
            float(normalized.count("search")),
            float(normalized.count("recommend")),
            float(len(set(terms))),
        ]
