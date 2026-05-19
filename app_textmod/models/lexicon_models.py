from __future__ import annotations

from django.db import models

from app_textmod.enums.lexicon_biz_type_enum import LexiconBizTypeEnum
from app_textmod.enums.lexicon_version_status_enum import LexiconVersionStatusEnum


class Lexicon(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=128, unique=True)
    biz_type = models.PositiveSmallIntegerField(
        default=int(LexiconBizTypeEnum.DEFAULT),
        choices=[(int(v), v.name) for v in LexiconBizTypeEnum],
    )
    ct = models.PositiveBigIntegerField(default=0)
    ut = models.PositiveBigIntegerField(default=0)

    class Meta:
        db_table = "lex"
        indexes = [
            models.Index(
                fields=["biz_type"],
                name="idx_tm_lex_biz",
            ),
        ]


class LexiconVersion(models.Model):
    id = models.BigAutoField(primary_key=True)
    lex_id = models.PositiveBigIntegerField()
    seq = models.PositiveIntegerField(default=1)
    status = models.SmallIntegerField(
        choices=[(int(v), v.name) for v in LexiconVersionStatusEnum],
        default=int(LexiconVersionStatusEnum.DRAFT),
    )
    blob_relpath = models.CharField(max_length=512, default="")
    blob_checksum = models.CharField(max_length=64, default="")
    entry_count = models.PositiveIntegerField(default=0)
    published_at = models.PositiveBigIntegerField(default=0)
    ct = models.PositiveBigIntegerField(default=0)

    class Meta:
        db_table = "lex_ver"
        indexes = [
            models.Index(
                fields=["status"],
                name="idx_tm_lex_ver_status",
            ),
            models.Index(
                fields=["lex_id", "status", "seq"],
                name="idx_tm_lex_ver_lex_status_seq",
            ),
        ]


class LexiconEntry(models.Model):
    id = models.BigAutoField(primary_key=True)
    lex_id = models.PositiveBigIntegerField()
    word = models.CharField(max_length=512)
    label_id = models.PositiveIntegerField(default=0)
    suggestion = models.SmallIntegerField(default=0)
    priority = models.IntegerField(default=0)
    enabled = models.SmallIntegerField(default=1)
    ct = models.PositiveBigIntegerField(default=0)

    class Meta:
        db_table = "lex_entry"
        indexes = [
            models.Index(
                fields=["lex_id", "enabled"],
                name="idx_tm_lex_entry_lex_enabled",
            ),
            models.Index(
                fields=["lex_id", "label_id", "id"],
                name="idx_tm_lex_entry_lex_label",
            ),
            models.Index(
                fields=["lex_id", "suggestion", "id"],
                name="idx_tm_lex_entry_lex_suggestion",
            ),
            models.Index(
                fields=["lex_id", "word", "id"],
                name="idx_tm_lex_entry_lex_word",
            ),
            models.Index(
                fields=["lex_id", "priority", "id"],
                name="idx_tm_lex_entry_lex_priority",
            ),
            models.Index(
                fields=["lex_id", "ct", "id"],
                name="idx_tm_lex_entry_lex_ct",
            ),
            models.Index(
                fields=["enabled"],
                name="idx_tm_lex_entry_enabled",
            ),
            models.Index(
                fields=["suggestion"],
                name="idx_tm_lex_entry_suggestion",
            ),
            models.Index(
                fields=["label_id"],
                name="idx_tm_lex_entry_label",
            ),
            models.Index(
                fields=["word"],
                name="idx_tm_lex_entry_word",
            ),
        ]
