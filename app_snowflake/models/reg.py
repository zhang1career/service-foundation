from django.db import models


class SnowflakeReg(models.Model):
    """使用方注册表 `sf_snowflake.reg`（表由运维/迁移创建，ORM 仅查询）。"""

    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=128, default="")
    access_key = models.CharField(max_length=64, default="")
    status = models.SmallIntegerField(default=0)
    ct = models.PositiveBigIntegerField(default=0)
    ut = models.PositiveBigIntegerField(default=0)

    class Meta:
        app_label = "app_snowflake"
        db_table = "reg"
        managed = False
