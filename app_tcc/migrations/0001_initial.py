# State-only migration for existing sf_tcc schema (tables already present).
# Apply with: python manage.py migrate app_tcc 0001 --fake
# (or --fake-initial when appropriate)

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.CreateModel(
                    name="TccParticipant",
                    fields=[
                        ("id", models.BigAutoField(primary_key=True, serialize=False)),
                        ("access_key", models.CharField(db_index=True, max_length=128, unique=True)),
                        ("name", models.CharField(blank=True, default="", max_length=255)),
                        (
                            "status",
                            models.SmallIntegerField(
                                choices=[(0, "DISABLED"), (1, "ENABLED")],
                                default=1,
                            ),
                        ),
                        ("ct", models.PositiveBigIntegerField(default=0)),
                        ("ut", models.PositiveBigIntegerField(default=0)),
                    ],
                    options={"db_table": "reg"},
                ),
                migrations.CreateModel(
                    name="TccBizMeta",
                    fields=[
                        ("id", models.BigAutoField(primary_key=True, serialize=False)),
                        (
                            "participant",
                            models.ForeignKey(
                                db_column="rid",
                                on_delete=models.CASCADE,
                                related_name="businesses",
                                to="app_tcc.tccparticipant",
                            ),
                        ),
                        ("name", models.CharField(blank=True, default="", max_length=255)),
                        ("ct", models.PositiveBigIntegerField(default=0)),
                        ("ut", models.PositiveBigIntegerField(default=0)),
                    ],
                    options={"db_table": "biz_meta", "ordering": ["id"]},
                ),
                migrations.CreateModel(
                    name="TccGlobalTransaction",
                    fields=[
                        ("id", models.BigAutoField(primary_key=True, serialize=False)),
                        ("status", models.PositiveSmallIntegerField(db_index=True, default=10)),
                        ("phase_started_at", models.BigIntegerField()),
                        ("phase_deadline_at", models.BigIntegerField(blank=True, null=True)),
                        ("await_confirm_deadline_at", models.BigIntegerField(blank=True, null=True)),
                        ("next_retry_at", models.BigIntegerField()),
                        ("retry_count", models.PositiveIntegerField(default=0)),
                        ("auto_confirm", models.BooleanField(default=True)),
                        ("manual_reason", models.TextField(blank=True, default="")),
                        ("context", models.TextField(blank=True, default="{}")),
                        ("idem_key", models.BigIntegerField(unique=True)),
                        ("ct", models.PositiveBigIntegerField(default=0)),
                        ("ut", models.PositiveBigIntegerField(default=0)),
                    ],
                    options={
                        "db_table": "tx",
                        "indexes": [
                            models.Index(fields=["status", "next_retry_at"]),
                            models.Index(fields=["status", "await_confirm_deadline_at"]),
                        ],
                    },
                ),
                migrations.CreateModel(
                    name="TccBranchMeta",
                    fields=[
                        ("id", models.BigAutoField(primary_key=True, serialize=False)),
                        (
                            "biz",
                            models.ForeignKey(
                                db_column="biz_id",
                                on_delete=models.CASCADE,
                                related_name="branch_defs",
                                to="app_tcc.tccbizmeta",
                            ),
                        ),
                        ("branch_index", models.PositiveIntegerField()),
                        ("try_url", models.CharField(max_length=2048)),
                        ("confirm_url", models.CharField(max_length=2048)),
                        ("cancel_url", models.CharField(max_length=2048)),
                        ("ct", models.PositiveBigIntegerField(default=0)),
                        ("ut", models.PositiveBigIntegerField(default=0)),
                    ],
                    options={
                        "db_table": "branch_meta",
                        "ordering": ["branch_index", "id"],
                        "constraints": [
                            models.UniqueConstraint(
                                fields=("biz", "branch_index"),
                                name="tcc_branch_meta_unique_biz_branch_index",
                            ),
                        ],
                    },
                ),
                migrations.CreateModel(
                    name="TccBranch",
                    fields=[
                        ("id", models.BigAutoField(primary_key=True, serialize=False)),
                        (
                            "global_tx",
                            models.ForeignKey(
                                db_column="tid",
                                on_delete=models.CASCADE,
                                related_name="branches",
                                to="app_tcc.tccglobaltransaction",
                            ),
                        ),
                        (
                            "branch_meta",
                            models.ForeignKey(
                                db_column="branch_meta_id",
                                on_delete=models.PROTECT,
                                related_name="branch_runs",
                                to="app_tcc.tccbranchmeta",
                            ),
                        ),
                        ("branch_index", models.PositiveIntegerField()),
                        ("status", models.PositiveSmallIntegerField(default=10)),
                        ("idem_key", models.BigIntegerField()),
                        ("payload", models.TextField(blank=True, default="{}")),
                        ("last_http_status", models.PositiveSmallIntegerField(blank=True, null=True)),
                        ("last_error", models.TextField(blank=True, default="")),
                        ("ct", models.PositiveBigIntegerField(default=0)),
                        ("ut", models.PositiveBigIntegerField(default=0)),
                    ],
                    options={
                        "db_table": "tx_branch",
                        "ordering": ["branch_index"],
                        "constraints": [
                            models.UniqueConstraint(
                                fields=("global_tx", "branch_index"),
                                name="tcc_tx_branch_unique_gtx_branch_index",
                            ),
                        ],
                    },
                ),
                migrations.CreateModel(
                    name="TccManualReview",
                    fields=[
                        ("id", models.BigAutoField(primary_key=True, serialize=False)),
                        (
                            "global_tx",
                            models.OneToOneField(
                                db_column="tid",
                                on_delete=models.CASCADE,
                                related_name="manual_review",
                                to="app_tcc.tccglobaltransaction",
                            ),
                        ),
                        ("snapshot", models.TextField(default="{}")),
                        ("ct", models.PositiveBigIntegerField(default=0)),
                        ("ut", models.PositiveBigIntegerField(default=0)),
                    ],
                    options={"db_table": "tx_manual_review"},
                ),
            ],
        ),
    ]
