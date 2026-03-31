from django.db import models


class PromptTemplate(models.Model):
    id = models.BigAutoField(primary_key=True)
    template_key = models.CharField(max_length=128)
    constraint_type = models.PositiveSmallIntegerField(default=0)  # 0 weak, 1 strong
    description = models.CharField(max_length=512, default="")
    body = models.TextField()
    param_specs = models.TextField(null=True, blank=True)
    resp_specs = models.TextField(null=True, blank=True)
    status = models.SmallIntegerField(default=1)
    ct = models.PositiveBigIntegerField(default=0)
    ut = models.PositiveBigIntegerField(default=0)

    class Meta:
        db_table = "prompt_tpl"
        constraints = [
            models.UniqueConstraint(
                fields=["template_key"],
                name="aibroker_tpl_key_uniq",
            ),
        ]
