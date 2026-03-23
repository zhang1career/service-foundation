# Generated manually - remove did and vid, use id (PK) as external identifier

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("app_cdn", "0004_invalidation_status_enum"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.RemoveField(
                    model_name="distribution",
                    name="did",
                ),
                migrations.RemoveField(
                    model_name="invalidation",
                    name="vid",
                ),
            ],
            database_operations=[
                migrations.RunSQL(
                    sql=[
                        "ALTER TABLE `d` DROP COLUMN `did`",
                        "ALTER TABLE `invalid` DROP COLUMN `vid`",
                    ],
                    reverse_sql=[
                        "ALTER TABLE `d` ADD COLUMN `did` BIGINT(20) NOT NULL DEFAULT 0",
                        "UPDATE `d` SET `did` = `id`",
                        "ALTER TABLE `d` ADD UNIQUE INDEX `uni_did` (`did`)",
                        "ALTER TABLE `invalid` ADD COLUMN `vid` BIGINT(20) NOT NULL DEFAULT 0 AFTER `id`",
                        "UPDATE `invalid` SET `vid` = `id`",
                        "ALTER TABLE `invalid` ADD UNIQUE INDEX `uni_vid` (`vid`)",
                    ],
                ),
            ],
        ),
    ]
