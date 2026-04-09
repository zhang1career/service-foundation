"""Enumerations for app_searchrec."""

from django.db import models


class SearchRecEventType(models.IntegerChoices):
    """Integer values stored in sf_searchrec.event.event_type."""

    UNKNOWN = 0
    SEARCH_QUERY = 1
    IMPRESSION = 2
    CLICK = 3
    UPSERT = 4
