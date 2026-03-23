# Generated manually - invalid: distribution_id -> did, create_time -> ct

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("app_cdn", "0005_remove_did_vid"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.RemoveField(
                    model_name="invalidation",
                    name="distribution",
                ),
                migrations.RemoveField(
                    model_name="invalidation",
                    name="create_time",
                ),
                migrations.AddField(
                    model_name="invalidation",
                    name="did",
                    field=models.ForeignKey(
                        db_column="did",
                        db_index=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="invalidations",
                        to="app_cdn.distribution",
                    ),
                ),
                migrations.AddField(
                    model_name="invalidation",
                    name="ct",
                    field=models.BigIntegerField(default=0),
                ),
            ],
            database_operations=[
                migrations.RunSQL(
                    sql=[
                        "ALTER TABLE `invalid` DROP FOREIGN KEY `invalid_distribution_id_fk`",
                        "ALTER TABLE `invalid` DROP INDEX `invalid_distribution_id_idx`",
                        "ALTER TABLE `invalid` CHANGE COLUMN `distribution_id` `did` BIGINT(20) NOT NULL",
                        "ALTER TABLE `invalid` ADD INDEX `invalid_did_idx` (`did`)",
                        "ALTER TABLE `invalid` ADD CONSTRAINT `invalid_did_fk` FOREIGN KEY (`did`) REFERENCES `d` (`id`) ON DELETE CASCADE",
                        "ALTER TABLE `invalid` CHANGE COLUMN `create_time` `ct` BIGINT(20) NOT NULL DEFAULT 0",
                    ],
                    reverse_sql=[
                        "ALTER TABLE `invalid` CHANGE COLUMN `ct` `create_time` BIGINT(20) NOT NULL DEFAULT 0",
                        "ALTER TABLE `invalid` DROP FOREIGN KEY `invalid_did_fk`",
                        "ALTER TABLE `invalid` DROP INDEX `invalid_did_idx`",
                        "ALTER TABLE `invalid` CHANGE COLUMN `did` `distribution_id` BIGINT(20) NOT NULL",
                        "ALTER TABLE `invalid` ADD INDEX `invalid_distribution_id_idx` (`distribution_id`)",
                        "ALTER TABLE `invalid` ADD CONSTRAINT `invalid_distribution_id_fk` FOREIGN KEY (`distribution_id`) REFERENCES `d` (`id`) ON DELETE CASCADE",
                    ],
                ),
            ],
        ),
    ]
