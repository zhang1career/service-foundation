-- Perspective and Insight tables for Phase 3
-- Run against know_rw database

CREATE TABLE `batch`
(
    `id`          BIGINT(20) UNSIGNED NOT NULL AUTO_INCREMENT,
    `source_type` TINYINT(4)          NOT NULL DEFAULT '0' COMMENT '0-instant, 1-file',
    `content`     TEXT                NULL     DEFAULT NULL,
    `ct`          BIGINT(20) UNSIGNED NOT NULL DEFAULT '0' COMMENT '创建时间',
    `ut`          BIGINT(20) UNSIGNED NOT NULL DEFAULT '0' COMMENT '更新时间',
    PRIMARY KEY (`id`) USING BTREE,
    INDEX `idx_src` (`ut`) USING BTREE
);

CREATE TABLE `knowledge`
(
    `id`             BIGINT(20) UNSIGNED NOT NULL AUTO_INCREMENT,
    `batch_id`       BIGINT(20) UNSIGNED NOT NULL DEFAULT 0,
    `content`        TEXT                NULL     DEFAULT NULL COMMENT '知识内容',
    `seq`            INT(10) UNSIGNED    NOT NULL DEFAULT '0',
    `brief`          VARCHAR(512)        NOT NULL DEFAULT '',
    `graph_brief`    VARCHAR(512)        NOT NULL DEFAULT '',
    `graph_subject`  VARCHAR(256)        NOT NULL DEFAULT '',
    `graph_object`   VARCHAR(256)        NOT NULL DEFAULT '',
    `classification` TINYINT(4)          NOT NULL DEFAULT '0',
    `stage`          TINYINT(4)          NOT NULL DEFAULT '0',
    `status`         TINYINT(4)          NOT NULL DEFAULT '0',
    `ct`             BIGINT(20) UNSIGNED NOT NULL DEFAULT '0' COMMENT '创建时间',
    `ut`             BIGINT(20) UNSIGNED NOT NULL DEFAULT '0' COMMENT '更新时间',
    PRIMARY KEY (`id`) USING BTREE,
    INDEX `idx_src` (`ut`) USING BTREE
);


CREATE TABLE IF NOT EXISTS `insight`
(
    `id`          BIGINT   NOT NULL AUTO_INCREMENT,
    `content`     TEXT     NOT NULL,
    `perspective` INT      NOT NULL DEFAULT 0,
    `type`        SMALLINT NOT NULL DEFAULT 0,
    `status`      SMALLINT NOT NULL DEFAULT 0,
    `ct`          BIGINT   NOT NULL DEFAULT 0,
    `ut`          BIGINT   NOT NULL DEFAULT 0,
    PRIMARY KEY (`id`),
    INDEX `idx_insight_ut` (`ut`)
);
