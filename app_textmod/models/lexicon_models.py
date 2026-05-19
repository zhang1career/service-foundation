from __future__ import annotations

from django.db import models

from app_textmod.enums.lexicon_biz_type_enum import LexiconBizTypeEnum
from app_textmod.enums.lexicon_version_status_enum import LexiconVersionStatusEnum


class Lexicon(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=128, unique=True)
    biz_type = models.PositiveSmallIntegerField(
        default=int(LexiconBizTypeEnum.DEFAULT),
        db_index=True,
        choices=[(int(v), v.name) for v in LexiconBizTypeEnum],
    )
    ct = models.PositiveBigIntegerField(default=0)
    ut = models.PositiveBigIntegerField(default=0)

    class Meta:
        db_table = "lex"


class LexiconVersion(models.Model):
    id = models.BigAutoField(primary_key=True)
    lex_id = models.PositiveBigIntegerField(db_index=True)
    seq = models.PositiveIntegerField(default=1)
    status = models.SmallIntegerField(
        choices=[(int(v), v.name) for v in LexiconVersionStatusEnum],
        default=int(LexiconVersionStatusEnum.DRAFT),
        db_index=True,
    )
    blob_relpath = models.CharField(max_length=512, default="")
    blob_checksum = models.CharField(max_length=64, default="")
    entry_count = models.PositiveIntegerField(default=0)
    published_at = models.PositiveBigIntegerField(default=0)
    ct = models.PositiveBigIntegerField(default=0)

    class Meta:
        db_table = "lex_ver"
        indexes = [
            models.Index(fields=["lex_id", "status"]),
            models.Index(fields=["lex_id", "seq"]),
        ]


class LexiconEntry(models.Model):
    id = models.BigAutoField(primary_key=True)
    lex_id = models.PositiveBigIntegerField(db_index=True)
    word = models.CharField(max_length=512, db_index=True)
    label_id = models.PositiveIntegerField(default=0, db_index=True)
    suggestion = models.SmallIntegerField(default=0, db_index=True)
    priority = models.IntegerField(default=0)
    enabled = models.SmallIntegerField(default=1, db_index=True)
    ct = models.PositiveBigIntegerField(default=0)

    class Meta:
        db_table = "lex_entry"
        indexes = [
            models.Index(fields=["lex_id", "enabled"]),
        ]
