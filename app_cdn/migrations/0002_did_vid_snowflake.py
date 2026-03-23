# Generated manually - migration to did/vid with app_snowflake
#
# Note: Drops and recreates tables. Existing data will be lost.
# For fresh deploy or when migrating from old schema without production data.

from django.db import migrations, models


def _sql_list(*statements):
    """Return list of SQL statements for RunSQL."""
    return [s.strip() for s in statements if s and s.strip()]


class Migration(migrations.Migration):

    dependencies = [
        ("app_cdn", "0001_initial"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterModelTable(name="distribution", table="d"),
                migrations.AlterModelTable(name="invalidation", table="invalid"),
                migrations.RemoveField(
                    model_name="distribution",
                    name="distribution_id",
                ),
                migrations.AddField(
                    model_name="distribution",
                    name="did",
                    field=models.BigIntegerField(db_index=True, unique=True),
                ),
                migrations.RemoveField(
                    model_name="invalidation",
                    name="invalidation_id",
                ),
                migrations.AddField(
                    model_name="invalidation",
                    name="vid",
                    field=models.BigIntegerField(db_index=True, unique=True),
                ),
            ],
            database_operations=[
                migrations.RunSQL(
                    sql=_sql_list(
                        "DROP TABLE IF EXISTS `cdn_invalidation`",
                        "DROP TABLE IF EXISTS `cdn_distribution`",
                        """CREATE TABLE `d` (
                            `id` BIGINT(20) NOT NULL AUTO_INCREMENT,
                            `did` BIGINT(20) NOT NULL,
                            `arn` VARCHAR(256) NOT NULL DEFAULT '',
                            `status` VARCHAR(32) NOT NULL DEFAULT 'Deployed',
                            `domain_name` VARCHAR(256) NOT NULL,
                            `origin_config` LONGTEXT NOT NULL,
                            `aliases` LONGTEXT NOT NULL,
                            `enabled` TINYINT(1) NOT NULL DEFAULT 1,
                            `comment` VARCHAR(256) NOT NULL DEFAULT '',
                            `etag` VARCHAR(64) NOT NULL DEFAULT '',
                            `ct` BIGINT(20) NOT NULL DEFAULT 0,
                            `ut` BIGINT(20) NOT NULL DEFAULT 0,
                            PRIMARY KEY (`id`),
                            UNIQUE INDEX `uni_did` (`did`)
                        )""",
                        """CREATE TABLE `invalid` (
                            `id` BIGINT(20) NOT NULL AUTO_INCREMENT,
                            `vid` BIGINT(20) NOT NULL,
                            `caller_reference` VARCHAR(128) NOT NULL,
                            `paths` LONGTEXT NOT NULL,
                            `status` VARCHAR(32) NOT NULL DEFAULT 'Completed',
                            `create_time` BIGINT(20) NOT NULL DEFAULT 0,
                            `distribution_id` BIGINT(20) NOT NULL,
                            PRIMARY KEY (`id`),
                            UNIQUE INDEX `uni_vid` (`vid`),
                            INDEX `invalid_distribution_id_idx` (`distribution_id`),
                            CONSTRAINT `invalid_distribution_id_fk` FOREIGN KEY (`distribution_id`) REFERENCES `d` (`id`) ON DELETE CASCADE
                        )""",
                    ),
                    reverse_sql=_sql_list(
                        "DROP TABLE IF EXISTS `invalid`",
                        "DROP TABLE IF EXISTS `d`",
                        """CREATE TABLE `cdn_distribution` (
                            `id` BIGINT(20) NOT NULL AUTO_INCREMENT,
                            `distribution_id` VARCHAR(64) NOT NULL,
                            `arn` VARCHAR(256) NOT NULL DEFAULT '',
                            `status` VARCHAR(32) NOT NULL DEFAULT 'Deployed',
                            `domain_name` VARCHAR(256) NOT NULL,
                            `origin_config` LONGTEXT NOT NULL,
                            `aliases` LONGTEXT NOT NULL,
                            `enabled` TINYINT(1) NOT NULL DEFAULT 1,
                            `comment` VARCHAR(256) NOT NULL DEFAULT '',
                            `etag` VARCHAR(64) NOT NULL DEFAULT '',
                            `ct` BIGINT(20) NOT NULL DEFAULT 0,
                            `ut` BIGINT(20) NOT NULL DEFAULT 0,
                            PRIMARY KEY (`id`),
                            UNIQUE INDEX `cdn_distribution_distribution_id` (`distribution_id`)
                        )""",
                        """CREATE TABLE `cdn_invalidation` (
                            `id` BIGINT(20) NOT NULL AUTO_INCREMENT,
                            `invalidation_id` VARCHAR(64) NOT NULL,
                            `caller_reference` VARCHAR(128) NOT NULL,
                            `paths` LONGTEXT NOT NULL,
                            `status` VARCHAR(32) NOT NULL DEFAULT 'Completed',
                            `create_time` BIGINT(20) NOT NULL DEFAULT 0,
                            `distribution_id` BIGINT(20) NOT NULL,
                            PRIMARY KEY (`id`),
                            UNIQUE INDEX `cdn_invalidation_invalidation_id` (`invalidation_id`),
                            CONSTRAINT `cdn_invalidation_distribution_id_fk` FOREIGN KEY (`distribution_id`) REFERENCES `cdn_distribution` (`id`) ON DELETE CASCADE
                        )""",
                    ),
                ),
            ],
        ),
    ]
