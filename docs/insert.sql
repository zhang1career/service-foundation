-- CDN Distribution Table (app_cdn)
CREATE TABLE `d` (
	`id` BIGINT(20) NOT NULL AUTO_INCREMENT,
	`arn` VARCHAR(256) NOT NULL DEFAULT '',
	`status` SMALLINT NOT NULL DEFAULT 1 COMMENT 'DistributionStatusEnum: 0=InProgress, 1=Deployed',
	`domain_name` VARCHAR(256) NOT NULL,
	`origin_config` LONGTEXT NOT NULL,
	`aliases` LONGTEXT NOT NULL,
	`enabled` TINYINT(1) NOT NULL DEFAULT 0,
	`comment` VARCHAR(256) NOT NULL DEFAULT '',
	`etag` VARCHAR(64) NOT NULL DEFAULT '',
	`ct` BIGINT(20) NOT NULL DEFAULT 0,
	`ut` BIGINT(20) NOT NULL DEFAULT 0,
	PRIMARY KEY (`id`)
) COMMENT='CDN distribution';

-- CDN Invalidation Table (app_cdn)
CREATE TABLE `invalid` (
	`id` BIGINT(20) NOT NULL AUTO_INCREMENT,
	`caller_reference` VARCHAR(128) NOT NULL,
	`paths` LONGTEXT NOT NULL,
	`status` SMALLINT NOT NULL DEFAULT 1 COMMENT 'InvalidationStatusEnum: 0=InProgress, 1=Completed',
	`ct` BIGINT(20) NOT NULL DEFAULT 0,
	`did` BIGINT(20) NOT NULL,
	PRIMARY KEY (`id`),
	INDEX `invalid_did_idx` (`did`),
	CONSTRAINT `invalid_did_fk` FOREIGN KEY (`did`) REFERENCES `d` (`id`) ON DELETE CASCADE
) COMMENT='CDN cache invalidation';