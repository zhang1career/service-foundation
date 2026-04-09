CREATE TABLE `doc` (
	`id` BIGINT(20) NOT NULL AUTO_INCREMENT,
	`doc_key` VARCHAR(191) NOT NULL COMMENT '业务方传入的文档 id' COLLATE 'utf8mb4_unicode_ci',
	`title` VARCHAR(512) NOT NULL COLLATE 'utf8mb4_unicode_ci',
	`content` TEXT NULL DEFAULT NULL COLLATE 'utf8mb4_unicode_ci',
	`tags` TEXT NULL DEFAULT NULL COMMENT '逗号分隔' COLLATE 'utf8mb4_unicode_ci',
	`lexical_norm_sq` BIGINT(20) NOT NULL DEFAULT '0' COMMENT 'sum(tf^2), tf integer',
	`score_boost` DECIMAL(4,2) NOT NULL DEFAULT '1.00',
	`ct` BIGINT(20) UNSIGNED NOT NULL DEFAULT '0' COMMENT 'Create time in Unix milliseconds',
	`ut` BIGINT(20) UNSIGNED NOT NULL DEFAULT '0' COMMENT 'Update time in Unix milliseconds',
	PRIMARY KEY (`id`) USING BTREE,
	UNIQUE INDEX `uni_doc_key` (`doc_key`) USING BTREE
)
COLLATE='utf8mb4_unicode_ci'
ENGINE=InnoDB
;

CREATE TABLE `doc_term` (
	`id` BIGINT(20) NOT NULL AUTO_INCREMENT,
	`doc_key` VARCHAR(191) NOT NULL COLLATE 'utf8mb4_unicode_ci',
	`term` VARCHAR(191) NOT NULL COLLATE 'utf8mb4_unicode_ci',
	`tf` INT(10) UNSIGNED NOT NULL DEFAULT '1',
	PRIMARY KEY (`id`) USING BTREE,
	UNIQUE INDEX `uni_doc_term` (`doc_key`, `term`) USING BTREE,
	INDEX `idx_doc_term_term` (`term`) USING BTREE
)
COLLATE='utf8mb4_unicode_ci'
ENGINE=InnoDB
;

CREATE TABLE `event` (
	`id` BIGINT(20) NOT NULL AUTO_INCREMENT,
	`uid` BIGINT(20) NOT NULL DEFAULT '0' COMMENT 'user ID',
	`did` VARCHAR(128) NOT NULL DEFAULT '' COMMENT 'device ID' COLLATE 'utf8mb4_unicode_ci',
	`event_type` TINYINT(3) UNSIGNED NOT NULL DEFAULT '0' COMMENT '0-UNKNOWN, 1-SEARCH_QUERY, 2-IMPRESSION, 3-CLICK, 4-UPSERT',
	`payload` TEXT NULL DEFAULT NULL COLLATE 'utf8mb4_unicode_ci',
	`ct` BIGINT(20) UNSIGNED NOT NULL DEFAULT '0' COMMENT 'Create time in Unix milliseconds',
	PRIMARY KEY (`id`) USING BTREE,
	INDEX `idx_event_type` (`event_type`) USING BTREE
)
COLLATE='utf8mb4_unicode_ci'
ENGINE=InnoDB
;
