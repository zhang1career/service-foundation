from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="SearchRecDocument",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("biz_doc_id", models.CharField(max_length=128, unique=True)),
                ("title", models.CharField(max_length=512)),
                ("content", models.TextField()),
                ("tags_json", models.JSONField(blank=True, default=list)),
                ("score_boost", models.FloatField(default=1.0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"db_table": "searchrec_document"},
        ),
    ]
