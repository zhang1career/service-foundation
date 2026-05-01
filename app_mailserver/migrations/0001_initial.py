# Generated manually for app_mailserver — aligns with models under app_mailserver.models

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="MailAccount",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("username", models.CharField(db_index=True, max_length=255, unique=True)),
                ("password", models.CharField(max_length=255)),
                ("domain", models.CharField(db_index=True, max_length=255)),
                ("is_active", models.BooleanField(default=True)),
                ("ct", models.BigIntegerField(db_index=True, default=0)),
                ("ut", models.BigIntegerField(db_index=True, default=0)),
            ],
            options={
                "db_table": "mail_account",
                "indexes": [
                    models.Index(fields=["username"], name="mail_account_username_idx"),
                    models.Index(fields=["domain"], name="mail_account_domain_idx"),
                ],
            },
        ),
        migrations.CreateModel(
            name="Mailbox",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("account_id", models.BigIntegerField(db_index=True)),
                ("name", models.CharField(db_index=True, max_length=100)),
                ("path", models.CharField(db_index=True, max_length=255)),
                ("message_count", models.IntegerField(default=0)),
                ("unread_count", models.IntegerField(default=0)),
                ("ct", models.BigIntegerField(db_index=True, default=0)),
                ("ut", models.BigIntegerField(db_index=True, default=0)),
            ],
            options={
                "db_table": "mailbox",
                "indexes": [
                    models.Index(
                        fields=["account_id", "name"],
                        name="mailbox_account_id_name_idx",
                    ),
                    models.Index(
                        fields=["account_id", "path"],
                        name="mailbox_account_id_path_idx",
                    ),
                ],
                "unique_together": {("account_id", "path")},
            },
        ),
        migrations.CreateModel(
            name="MailMessage",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("account_id", models.BigIntegerField(db_index=True)),
                ("mailbox_id", models.BigIntegerField(db_index=True)),
                ("message_id", models.CharField(db_index=True, max_length=512)),
                ("subject", models.TextField(default="")),
                (
                    "from_address",
                    models.CharField(db_column="from", max_length=512),
                ),
                (
                    "to_addresses",
                    models.TextField(db_column="to", default=""),
                ),
                (
                    "cc_addresses",
                    models.TextField(db_column="cc", default=""),
                ),
                (
                    "bcc_addresses",
                    models.TextField(db_column="bcc", default=""),
                ),
                ("text_body", models.TextField(default="")),
                ("html_body", models.TextField(default="")),
                ("mt", models.BigIntegerField(db_index=True)),
                ("is_read", models.BooleanField(default=False)),
                ("is_flagged", models.BooleanField(default=False)),
                ("size", models.BigIntegerField(default=0)),
                ("raw_message", models.TextField(default="")),
                ("ct", models.BigIntegerField(db_index=True, default=0)),
                ("ut", models.BigIntegerField(db_index=True, default=0)),
            ],
            options={
                "db_table": "mail_message",
                "indexes": [
                    models.Index(
                        fields=["account_id", "mailbox_id", "mt"],
                        name="mail_message_acc_mail_mt_idx",
                    ),
                    models.Index(
                        fields=["account_id", "is_read"],
                        name="mail_message_acc_read_idx",
                    ),
                    models.Index(
                        fields=["message_id"],
                        name="mail_message_message_id_idx",
                    ),
                ],
                "unique_together": {("account_id", "message_id")},
            },
        ),
        migrations.CreateModel(
            name="MailAttachment",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("message_id", models.BigIntegerField(db_index=True)),
                ("filename", models.CharField(max_length=512)),
                ("content_type", models.IntegerField(default=0)),
                ("size", models.BigIntegerField(default=0)),
                ("oss_bucket", models.CharField(max_length=255)),
                ("oss_key", models.CharField(max_length=1024)),
                ("content_id", models.CharField(blank=True, default="", max_length=255)),
                (
                    "content_disposition",
                    models.CharField(default="attachment", max_length=50),
                ),
                ("ct", models.BigIntegerField(db_index=True, default=0)),
            ],
            options={
                "db_table": "mail_attachment",
                "indexes": [
                    models.Index(
                        fields=["message_id"],
                        name="mail_attachment_message_id_idx",
                    ),
                    models.Index(
                        fields=["oss_bucket", "oss_key"],
                        name="mail_attachment_oss_idx",
                    ),
                ],
            },
        ),
    ]
