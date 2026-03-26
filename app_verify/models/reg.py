from django.db import models


class Reg(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=128)
    access_key = models.CharField(max_length=64)
    status = models.SmallIntegerField(default=0)
    ct = models.PositiveBigIntegerField(default=0)
    ut = models.PositiveBigIntegerField(default=0)

    class Meta:
        db_table = "reg"
        constraints = [
            models.UniqueConstraint(fields=["access_key"], name="verify_reg_access_key_uniq"),
        ]
        indexes = [
            models.Index(fields=["name"], name="verify_reg_name_idx"),
            models.Index(fields=["status"], name="verify_reg_status_idx"),
            models.Index(fields=["ct"], name="verify_reg_ct_idx"),
            models.Index(fields=["ut"], name="verify_reg_ut_idx"),
        ]
