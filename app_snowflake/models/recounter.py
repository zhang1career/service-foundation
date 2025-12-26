from django.db import models


class Recounter(models.Model):
    id = models.BigAutoField(primary_key=True)

    # datacenter id
    dcid = models.BigIntegerField(default=0)

    # machine id
    mid = models.BigIntegerField(default=0)

    # recount
    rc = models.IntegerField(default=0)

    # create time
    ct = models.BigIntegerField(default=0)

    # update time
    ut = models.BigIntegerField(default=0)

    class Meta:
        db_table = "recounter"
