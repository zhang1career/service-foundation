-- Service Foundation Database Schema
-- This file contains the complete database schema for all databases used by the service_foundation project
-- 
-- Databases:
-- - service_foundation (default): Mail server tables
-- - sf_snowflake (snowflake_rw): Snowflake ID generator tables
-- - sf_oss (oss_rw): Object storage service metadata tables
--
-- Note: All tables use utf8mb4 character set and InnoDB engine
-- All timestamps are stored as DATETIME (for created_at/updated_at) or BIGINT (for Unix timestamps in milliseconds)

-- ============================================================================
-- Database: service_foundation (default)
-- ============================================================================

-- Create database (if not exists)
-- CREATE DATABASE IF NOT EXISTS `service_foundation` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
-- USE `service_foundation`;

-- Mail Account Table
CREATE TABLE `mail_account` (
	`id` BIGINT(20) UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'primary key id',
	`username` VARCHAR(255) NOT NULL DEFAULT '' COMMENT 'email address (username)',
	`password` VARCHAR(255) NOT NULL DEFAULT '' COMMENT 'encrypted password',
	`domain` VARCHAR(255) NOT NULL DEFAULT '' COMMENT 'domain name',
	`is_active` TINYINT(1) NOT NULL DEFAULT '0' COMMENT 'whether account is active',
	`ct` BIGINT(20) NOT NULL DEFAULT '0' COMMENT 'creation time, UNIX timestamp in milliseconds',
	`ut` BIGINT(20) NOT NULL DEFAULT '0' COMMENT 'update time, UNIX timestamp in milliseconds',
	PRIMARY KEY (`id`) USING BTREE,
	UNIQUE INDEX `uni_username` (`username`) USING BTREE,
	INDEX `idx_mail_account_domain` (`domain`) USING BTREE
)
COMMENT='mail account'
COLLATE='utf8mb4_unicode_ci'
ENGINE=InnoDB
AUTO_INCREMENT=1;

-- Mailbox Table
CREATE TABLE `mailbox` (
	`id` BIGINT(20) UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'primary key id',
	`account_id` BIGINT(20) NOT NULL DEFAULT '0' COMMENT 'mail account id (maintained by application)',
	`name` VARCHAR(100) NOT NULL DEFAULT '' COMMENT 'mailbox name (e.g., INBOX, Sent, Drafts, Trash)',
	`path` VARCHAR(255) NOT NULL DEFAULT '' COMMENT 'mailbox path (IMAP format, e.g., INBOX, INBOX.Sent)',
	`message_count` INT(11) NOT NULL DEFAULT '0' COMMENT 'number of messages',
	`unread_count` INT(11) NOT NULL DEFAULT '0' COMMENT 'number of unread messages',
	`ct` BIGINT(20) NOT NULL DEFAULT '0' COMMENT 'creation time, UNIX timestamp in milliseconds',
	`ut` BIGINT(20) NOT NULL DEFAULT '0' COMMENT 'update time, UNIX timestamp in milliseconds',
	PRIMARY KEY (`id`) USING BTREE,
	UNIQUE INDEX `uni_account_path` (`account_id`, `path`) USING BTREE,
	INDEX `idx_mailbox_name` (`name`) USING BTREE,
	INDEX `idx_mailbox_path` (`path`) USING BTREE
)
COMMENT='mailbox (folder)'
COLLATE='utf8mb4_unicode_ci'
ENGINE=InnoDB
AUTO_INCREMENT=1;

-- Mail Message Table
CREATE TABLE `mail_message` (
	`id` BIGINT(20) UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'primary key id',
	`account_id` BIGINT(20) NOT NULL DEFAULT '0' COMMENT 'mail account id (maintained by application)',
	`message_id` VARCHAR(512) NOT NULL DEFAULT '' COMMENT 'email message-id (unique identifier)',
	`mailbox_id` BIGINT(20) NOT NULL DEFAULT '0' COMMENT 'mailbox id (maintained by application)',
	`subject` TEXT NOT NULL COMMENT 'email subject',
	`from` VARCHAR(512) NOT NULL DEFAULT '' COMMENT 'sender address',
	`to` TEXT NOT NULL COMMENT 'recipient addresses (comma-separated)',
	`cc` TEXT NOT NULL COMMENT 'CC addresses (comma-separated)',
	`bcc` TEXT NOT NULL COMMENT 'BCC addresses (comma-separated)',
	`text_body` TEXT NOT NULL COMMENT 'email text body',
	`html_body` TEXT NOT NULL COMMENT 'email HTML body',
	`mt` BIGINT(20) NOT NULL DEFAULT '0' COMMENT 'email date, UNIX timestamp in milliseconds',
	`is_read` TINYINT(1) NOT NULL DEFAULT '0' COMMENT 'whether message is read',
	`is_flagged` TINYINT(1) NOT NULL DEFAULT '0' COMMENT 'whether message is flagged',
	`size` BIGINT(20) NOT NULL DEFAULT '0' COMMENT 'email size in bytes',
	`raw_message` TEXT NOT NULL COMMENT 'raw email content (for complete reconstruction)',
	`ct` BIGINT(20) NOT NULL DEFAULT '0' COMMENT 'creation time, UNIX timestamp in milliseconds',
	`ut` BIGINT(20) NOT NULL DEFAULT '0' COMMENT 'update time, UNIX timestamp in milliseconds',
	PRIMARY KEY (`id`) USING BTREE,
	UNIQUE INDEX `uni_account_message` (`account_id`, `message_id`) USING BTREE,
	INDEX `idx_mail_message_account_mailbox_date` (`account_id`, `mailbox_id`, `mt`) USING BTREE,
	INDEX `idx_mail_message_mailbox` (`mailbox_id`) USING BTREE,
	INDEX `idx_mail_message_message` (`message_id`) USING BTREE,
	INDEX `idx_mail_message_date` (`mt`) USING BTREE,
	INDEX `idx_mail_message_account_is_read` (`account_id`, `is_read`) USING BTREE
)
COMMENT='mail message table'
COLLATE='utf8mb4_unicode_ci'
ENGINE=InnoDB
AUTO_INCREMENT=1;

-- Mail Attachment Table
CREATE TABLE `mail_attachment` (
	`id` BIGINT(20) UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'primary key id',
	`message_id` BIGINT(20) NOT NULL DEFAULT '0' COMMENT 'mail message id (maintained by application)',
	`filename` VARCHAR(512) NOT NULL DEFAULT '' COMMENT 'attachment filename',
	`content_type` INT(10) NOT NULL DEFAULT '0' COMMENT 'MIME type, 0=application/octet-stream',
	`size` BIGINT(20) NOT NULL DEFAULT '0' COMMENT 'attachment size in bytes',
	`oss_bucket` VARCHAR(255) NOT NULL DEFAULT '' COMMENT 'OSS bucket name',
	`oss_key` VARCHAR(512) NOT NULL DEFAULT '' COMMENT 'OSS object key (path)',
	`content_id` VARCHAR(255) NOT NULL DEFAULT '' COMMENT 'Content-ID (for embedded images, etc.)',
	`content_disposition` VARCHAR(50) NOT NULL DEFAULT 'attachment' COMMENT 'Content-Disposition (attachment or inline)',
	`ct` BIGINT(20) NOT NULL DEFAULT '0' COMMENT 'creation time, UNIX timestamp in milliseconds',
	PRIMARY KEY (`id`) USING BTREE,
	INDEX `idx_mail_attachment_message` (`message_id`) USING BTREE,
	INDEX `idx_mail_attachment_oss` (`oss_bucket`, `oss_key`) USING BTREE
)
COMMENT='mail attachment table'
COLLATE='utf8mb4_unicode_ci'
ENGINE=InnoDB
AUTO_INCREMENT=1;
