# Generated manually - d.status to SMALLINT (DistributionStatusEnum id)

from django.db import migrations, models

from app_cdn.enums.distribution_status_enum import DistributionStatusEnum


class Migration(migrations.Migration):

    dependencies = [
        ("app_cdn", "0002_did_vid_snowflake"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterField(
                    model_name="distribution",
                    name="status",
                    field=models.SmallIntegerField(
                        db_index=True,
                        default=DistributionStatusEnum.DEPLOYED,
                    ),
                ),
            ],
            database_operations=[
                migrations.RunSQL(
                    sql=[
                        "ALTER TABLE `d` ADD COLUMN `status_new` SMALLINT NOT NULL DEFAULT 1",
                        "UPDATE `d` SET `status_new` = CASE WHEN `status` = 'InProgress' THEN 0 ELSE 1 END",
                        "ALTER TABLE `d` DROP COLUMN `status`",
                        "ALTER TABLE `d` CHANGE COLUMN `status_new` `status` SMALLINT NOT NULL DEFAULT 1",
                    ],
                    reverse_sql=[
                        "ALTER TABLE `d` ADD COLUMN `status_old` VARCHAR(32) NOT NULL DEFAULT 'Deployed'",
                        "UPDATE `d` SET `status_old` = CASE WHEN `status` = 0 THEN 'InProgress' ELSE 'Deployed' END",
                        "ALTER TABLE `d` DROP COLUMN `status`",
                        "ALTER TABLE `d` CHANGE COLUMN `status_old` `status` VARCHAR(32) NOT NULL DEFAULT 'Deployed'",
                    ],
                ),
            ],
        ),
    ]
