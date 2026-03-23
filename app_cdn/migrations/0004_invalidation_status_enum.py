# Generated manually - invalid.status to SMALLINT (InvalidationStatusEnum id)

from django.db import migrations, models

from app_cdn.enums.invalidation_status_enum import InvalidationStatusEnum


class Migration(migrations.Migration):

    dependencies = [
        ("app_cdn", "0003_distribution_status_enum"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterField(
                    model_name="invalidation",
                    name="status",
                    field=models.SmallIntegerField(
                        db_index=True,
                        default=InvalidationStatusEnum.COMPLETED,
                    ),
                ),
            ],
            database_operations=[
                migrations.RunSQL(
                    sql=[
                        "ALTER TABLE `invalid` ADD COLUMN `status_new` SMALLINT NOT NULL DEFAULT 1",
                        "UPDATE `invalid` SET `status_new` = CASE WHEN `status` = 'InProgress' THEN 0 ELSE 1 END",
                        "ALTER TABLE `invalid` DROP COLUMN `status`",
                        "ALTER TABLE `invalid` CHANGE COLUMN `status_new` `status` SMALLINT NOT NULL DEFAULT 1",
                    ],
                    reverse_sql=[
                        "ALTER TABLE `invalid` ADD COLUMN `status_old` VARCHAR(32) NOT NULL DEFAULT 'Completed'",
                        "UPDATE `invalid` SET `status_old` = CASE WHEN `status` = 0 THEN 'InProgress' ELSE 'Completed' END",
                        "ALTER TABLE `invalid` DROP COLUMN `status`",
                        "ALTER TABLE `invalid` CHANGE COLUMN `status_old` `status` VARCHAR(32) NOT NULL DEFAULT 'Completed'",
                    ],
                ),
            ],
        ),
    ]
