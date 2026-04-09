from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="SearchRecDocument",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("biz_doc_id", models.BigIntegerField(unique=True)),
                ("title", models.CharField(max_length=512)),
                ("content", models.TextField()),
                ("tags", models.TextField(default="")),
                ("score_boost", models.FloatField(default=1.0)),
                ("ct", models.BigIntegerField()),
                ("ut", models.BigIntegerField()),
            ],
            options={"db_table": "doc"},
        ),
        migrations.CreateModel(
            name="SearchRecEvent",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("uid", models.BigIntegerField(blank=True, null=True)),
                (
                    "did",
                    models.CharField(blank=True, max_length=128, null=True),
                ),
                (
                    "event_type",
                    models.IntegerField(
                        choices=[
                            (0, "Unknown"),
                            (1, "Search Query"),
                            (2, "Impression"),
                            (3, "Click"),
                            (4, "Upsert"),
                        ]
                    ),
                ),
                ("payload", models.TextField(default="{}")),
                ("ct", models.BigIntegerField()),
            ],
            options={"db_table": "event"},
        ),
    ]
