from django.db import models


class AiProvider(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=128)
    base_url = models.CharField(max_length=512)
    url_path = models.CharField(
        max_length=512,
        default="/v1/chat/completions",
        help_text="POST path for this provider (e.g. /v1/chat/completions or /v1/embeddings); host from base_url.",
    )
    api_key = models.CharField(max_length=512)
    status = models.SmallIntegerField(default=1)
    ct = models.PositiveBigIntegerField(default=0)
    ut = models.PositiveBigIntegerField(default=0)

    class Meta:
        db_table = "ai_provider"
