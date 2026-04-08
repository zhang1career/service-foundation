from __future__ import annotations

from django.db.models.signals import post_delete
from django.dispatch import receiver

from app_cms.models.content_meta import CmsContentMeta
from app_cms.services.content_physical_table_service import ContentPhysicalTableService


@receiver(post_delete, sender=CmsContentMeta)
def content_meta_drop_physical_table(sender, instance: CmsContentMeta, **kwargs) -> None:
    ContentPhysicalTableService().drop_if_exists(instance)
