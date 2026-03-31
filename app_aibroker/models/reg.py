from django.db import models


class Reg(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=128)
    access_key = models.CharField(max_length=64)
    callback_secret = models.CharField(max_length=128)
    status = models.SmallIntegerField(default=0)
    ct = models.PositiveBigIntegerField(default=0)
    ut = models.PositiveBigIntegerField(default=0)

    class Meta:
        db_table = "reg"
        constraints = [
            models.UniqueConstraint(fields=["access_key"], name="uni_ai_reg_access"),
        ]
