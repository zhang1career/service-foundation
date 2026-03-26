from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="AiAsset",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("reg_id", models.PositiveBigIntegerField()),
                ("oss_bucket", models.CharField(max_length=128)),
                ("oss_key", models.CharField(max_length=512)),
                ("content_type", models.IntegerField(default=0)),
                ("ct", models.PositiveBigIntegerField(default=0)),
            ],
            options={
                "db_table": "ai_asset",
            },
        ),
        migrations.CreateModel(
            name="AiCallLog",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("reg_id", models.PositiveBigIntegerField(default=0)),
                ("template_id", models.PositiveBigIntegerField(default=0)),
                ("provider_id", models.PositiveBigIntegerField(default=0)),
                ("model_id", models.PositiveBigIntegerField(default=0)),
                ("latency_ms", models.IntegerField(default=0)),
                ("success", models.SmallIntegerField(default=0)),
                ("error_message", models.CharField(default="", max_length=512)),
                ("ct", models.PositiveBigIntegerField(default=0)),
            ],
            options={
                "db_table": "ai_call_log",
            },
        ),
        migrations.CreateModel(
            name="AiIdempotency",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("reg_id", models.PositiveBigIntegerField()),
                ("idem_key", models.CharField(max_length=128)),
                ("req_hash", models.CharField(default="", max_length=64)),
                ("resp_json", models.TextField()),
                ("ct", models.PositiveBigIntegerField(default=0)),
            ],
            options={
                "db_table": "ai_idem",
            },
        ),
        migrations.CreateModel(
            name="AiJob",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("reg_id", models.PositiveBigIntegerField()),
                ("job_type", models.CharField(max_length=64)),
                ("status", models.PositiveSmallIntegerField(default=0)),
                ("callback_url", models.CharField(default="", max_length=1024)),
                ("payload_json", models.TextField(blank=True, null=True)),
                ("result_json", models.TextField(blank=True, null=True)),
                ("message", models.CharField(default="", max_length=512)),
                ("ct", models.PositiveBigIntegerField(default=0)),
                ("ut", models.PositiveBigIntegerField(default=0)),
            ],
            options={
                "db_table": "ai_job",
            },
        ),
        migrations.CreateModel(
            name="AiModel",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("provider_id", models.PositiveBigIntegerField(db_index=True, default=0)),
                ("model_name", models.CharField(max_length=128)),
                ("capability", models.PositiveSmallIntegerField(default=0)),
                ("status", models.SmallIntegerField(default=1)),
                ("ct", models.PositiveBigIntegerField(default=0)),
                ("ut", models.PositiveBigIntegerField(default=0)),
            ],
            options={
                "db_table": "ai_model",
            },
        ),
        migrations.CreateModel(
            name="AiProvider",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=128)),
                ("base_url", models.CharField(max_length=512)),
                ("api_key", models.CharField(max_length=512)),
                ("status", models.SmallIntegerField(default=1)),
                ("ct", models.PositiveBigIntegerField(default=0)),
                ("ut", models.PositiveBigIntegerField(default=0)),
            ],
            options={
                "db_table": "ai_provider",
            },
        ),
        migrations.CreateModel(
            name="PromptTemplate",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("template_key", models.CharField(max_length=128)),
                ("version", models.IntegerField(default=1)),
                ("constraint_type", models.PositiveSmallIntegerField(default=0)),
                ("body", models.TextField()),
                ("variables_schema_json", models.TextField(blank=True, null=True)),
                ("output_schema_json", models.TextField(blank=True, null=True)),
                ("status", models.SmallIntegerField(default=1)),
                ("ct", models.PositiveBigIntegerField(default=0)),
                ("ut", models.PositiveBigIntegerField(default=0)),
            ],
            options={
                "db_table": "prompt_template",
            },
        ),
        migrations.CreateModel(
            name="Reg",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=128)),
                ("access_key", models.CharField(max_length=64)),
                ("callback_secret", models.CharField(max_length=128)),
                ("status", models.SmallIntegerField(default=0)),
                ("ct", models.PositiveBigIntegerField(default=0)),
                ("ut", models.PositiveBigIntegerField(default=0)),
            ],
            options={
                "db_table": "reg",
            },
        ),
        migrations.AddConstraint(
            model_name="prompttemplate",
            constraint=models.UniqueConstraint(
                fields=("template_key", "version"),
                name="aibroker_tpl_key_ver_uniq",
            ),
        ),
        migrations.AddConstraint(
            model_name="reg",
            constraint=models.UniqueConstraint(
                fields=("access_key",),
                name="aibroker_reg_access_key_uniq",
            ),
        ),
        migrations.AddConstraint(
            model_name="aiidempotency",
            constraint=models.UniqueConstraint(
                fields=("reg_id", "idem_key"),
                name="aibroker_idem_reg_key_uniq",
            ),
        ),
        migrations.AddIndex(
            model_name="aiasset",
            index=models.Index(fields=["reg_id"], name="aibroker_asset_reg_idx"),
        ),
        migrations.AddIndex(
            model_name="aicalllog",
            index=models.Index(fields=["reg_id", "ct"], name="aibroker_log_reg_ct_idx"),
        ),
        migrations.AddIndex(
            model_name="aicalllog",
            index=models.Index(fields=["success", "ct"], name="aibroker_log_success_ct_idx"),
        ),
        migrations.AddIndex(
            model_name="aijob",
            index=models.Index(fields=["reg_id", "status"], name="aibroker_job_reg_status_idx"),
        ),
        migrations.AddIndex(
            model_name="aimodel",
            index=models.Index(fields=["provider_id", "status"], name="aibroker_model_provider_idx"),
        ),
        migrations.AddIndex(
            model_name="aiprovider",
            index=models.Index(fields=["status"], name="aibroker_provider_status_idx"),
        ),
        migrations.AddIndex(
            model_name="prompttemplate",
            index=models.Index(fields=["template_key"], name="aibroker_tpl_key_idx"),
        ),
        migrations.AddIndex(
            model_name="reg",
            index=models.Index(fields=["status"], name="aibroker_reg_status_idx"),
        ),
        migrations.AddIndex(
            model_name="reg",
            index=models.Index(fields=["ct"], name="aibroker_reg_ct_idx"),
        ),
    ]
