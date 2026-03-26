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
            models.UniqueConstraint(fields=["access_key"], name="aibroker_reg_access_key_uniq"),
        ]
        indexes = [
            models.Index(fields=["status"], name="aibroker_reg_status_idx"),
            models.Index(fields=["ct"], name="aibroker_reg_ct_idx"),
        ]
