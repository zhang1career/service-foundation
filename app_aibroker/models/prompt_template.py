from django.db import models


class PromptTemplate(models.Model):
    id = models.BigAutoField(primary_key=True)
    template_key = models.CharField(max_length=128)
    version = models.IntegerField(default=1)
    constraint_type = models.PositiveSmallIntegerField(default=0)  # 0 weak, 1 strong
    body = models.TextField()
    variables_schema_json = models.TextField(null=True, blank=True)
    output_schema_json = models.TextField(null=True, blank=True)
    status = models.SmallIntegerField(default=1)
    ct = models.PositiveBigIntegerField(default=0)
    ut = models.PositiveBigIntegerField(default=0)

    class Meta:
        db_table = "prompt_template"
        constraints = [
            models.UniqueConstraint(
                fields=["template_key", "version"],
                name="aibroker_tpl_key_ver_uniq",
            ),
        ]
        indexes = [
            models.Index(fields=["template_key"], name="aibroker_tpl_key_idx"),
        ]
