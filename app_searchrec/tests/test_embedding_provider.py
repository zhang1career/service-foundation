from django.test import SimpleTestCase

from app_searchrec.providers.embedding_provider import SimpleTextEmbeddingProvider


class TestSimpleTextEmbeddingProvider(SimpleTestCase):
    def test_encode_returns_fixed_length_vector(self):
        v = SimpleTextEmbeddingProvider.encode("Hello Search recommend")
        self.assertEqual(len(v), 4)
        self.assertTrue(all(isinstance(x, float) for x in v))

    def test_encode_empty_string(self):
        v = SimpleTextEmbeddingProvider.encode("")
        self.assertEqual(v[0], 0.0)
