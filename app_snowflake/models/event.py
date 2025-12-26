from django.db import models


class Event(models.Model):
    id = models.BigAutoField(primary_key=True)

    # datacenter id
    dcid = models.BigIntegerField(default=0)

    # machine id
    mid = models.BigIntegerField(default=0)

    # event type
    event_type = models.IntegerField(default=0)

    # event brief information
    brief = models.TextField(default="")

    # event detail information
    detail = models.TextField(default="")

    # create time
    ct = models.BigIntegerField(default=0)

    class Meta:
        db_table = "event"


class EventDetail:

    def __init__(self,
                 recount: int):
        self.recount = recount

    def to_dict(self) -> dict:
        return {
            "recount": self.recount,
        }

