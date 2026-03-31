from django.db import models


class AiModel(models.Model):
    id = models.BigAutoField(primary_key=True)
    provider_id = models.PositiveBigIntegerField(default=0, db_index=True)
    model_name = models.CharField(max_length=128)
    capability = models.PositiveSmallIntegerField(default=0)  # 0 chat, 1 image, 2 video, 3 embedding
    status = models.SmallIntegerField(default=1)
    param_specs = models.TextField(
        default="",
        blank=True,
        help_text='JSON array: API kwargs schema; node x = top-level model_params key name whose value is copied into this row path; key content = rendered template + attachments (always set by server).',
    )
    ct = models.PositiveBigIntegerField(default=0)
    ut = models.PositiveBigIntegerField(default=0)

    class Meta:
        db_table = "ai_model"
        indexes = [
            models.Index(fields=["provider_id", "status"], name="idx_ai_model_provider"),
        ]
