from django.db import models


class SearchRecDocument(models.Model):
    biz_doc_id = models.CharField(max_length=128, unique=True)
    title = models.CharField(max_length=512)
    content = models.TextField()
    tags_json = models.JSONField(default=list, blank=True)
    score_boost = models.FloatField(default=1.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "app_searchrec"
        db_table = "searchrec_document"
