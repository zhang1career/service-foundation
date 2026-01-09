-- OSS Metadata Table Schema
-- Database: sf_oss
-- Table: m (metadata)

-- Create database (if not exists)
-- CREATE DATABASE IF NOT EXISTS `sf_oss` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
-- USE `sf_oss`;

-- Metadata table for OSS objects
CREATE TABLE `m` (
	`id` BIGINT(20) UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'primary key id',
	`bucket_name` VARCHAR(255) NOT NULL DEFAULT '' COMMENT 'bucket name',
	`object_key` VARCHAR(1024) NOT NULL DEFAULT '' COMMENT 'object key (path)',
	`content_type` INT(11) NOT NULL DEFAULT '0' COMMENT 'content type enum id (0=application/octet-stream)',
	`content_length` BIGINT(20) NOT NULL DEFAULT '0' COMMENT 'content length in bytes',
	`etag` VARCHAR(64) NOT NULL DEFAULT '' COMMENT 'ETag (MD5 hash)',
	`size` BIGINT(20) NOT NULL DEFAULT '0' COMMENT 'file size in bytes',
	`metadata` TEXT NULL COMMENT 'user-defined metadata (JSON format)',
	`ut` BIGINT(20) NOT NULL COMMENT 'update (last modification) time, UNIX timestamp in ms',
	PRIMARY KEY (`id`) USING BTREE,
	UNIQUE INDEX `uni_bucket_key` (`bucket_name`, `object_key`) USING BTREE,
	INDEX `idx_object_key` (`object_key`) USING BTREE
)
COMMENT='OSS object metadata table'
COLLATE='utf8mb4_unicode_ci'
ENGINE=InnoDB
AUTO_INCREMENT=1;

-- Content Type Enum Reference:
-- 0  = APPLICATION_OCTET_STREAM (application/octet-stream)
-- 1  = TEXT_PLAIN (text/plain)
-- 2  = TEXT_HTML (text/html)
-- 3  = TEXT_CSS (text/css)
-- 4  = TEXT_JAVASCRIPT (text/javascript)
-- 5  = TEXT_CSV (text/csv)
-- 6  = TEXT_XML (text/xml)
-- 10 = IMAGE_JPEG (image/jpeg)
-- 11 = IMAGE_PNG (image/png)
-- 12 = IMAGE_GIF (image/gif)
-- 13 = IMAGE_WEBP (image/webp)
-- 14 = IMAGE_SVG (image/svg+xml)
-- 15 = IMAGE_BMP (image/bmp)
-- 16 = IMAGE_ICO (image/x-icon)
-- 20 = AUDIO_MPEG (audio/mpeg)
-- 21 = AUDIO_OGG (audio/ogg)
-- 22 = AUDIO_WAV (audio/wav)
-- 23 = AUDIO_WEBM (audio/webm)
-- 30 = VIDEO_MP4 (video/mp4)
-- 31 = VIDEO_OGG (video/ogg)
-- 32 = VIDEO_WEBM (video/webm)
-- 33 = VIDEO_QUICKTIME (video/quicktime)
-- 40 = APPLICATION_JSON (application/json)
-- 41 = APPLICATION_XML (application/xml)
-- 42 = APPLICATION_PDF (application/pdf)
-- 43 = APPLICATION_ZIP (application/zip)
-- 44 = APPLICATION_GZIP (application/gzip)
-- 45 = APPLICATION_X_TAR (application/x-tar)
-- 50 = APPLICATION_MSWORD (application/msword)
-- 51 = APPLICATION_VND_MS_EXCEL (application/vnd.ms-excel)
-- 52 = APPLICATION_VND_MS_POWERPOINT (application/vnd.ms-powerpoint)
-- 53 = APPLICATION_VND_OPENXMLFORMATS_OFFICEDOCUMENT_WORDPROCESSINGML_DOCUMENT
-- 54 = APPLICATION_VND_OPENXMLFORMATS_OFFICEDOCUMENT_SPREADSHEETML_SHEET
-- 55 = APPLICATION_VND_OPENXMLFORMATS_OFFICEDOCUMENT_PRESENTATIONML_PRESENTATION

-- Query examples

-- Query metadata by bucket and key
-- SELECT * FROM `m` WHERE `bucket_name` = 'my-bucket' AND `object_key` = 'my-object-key';

-- Query all objects in a bucket
-- SELECT * FROM `m` WHERE `bucket_name` = 'my-bucket' ORDER BY `ut` DESC;

-- Query objects by content type
-- SELECT * FROM `m` WHERE `content_type` = 10; -- JPEG images

-- Query objects with prefix
-- SELECT * FROM `m` WHERE `bucket_name` = 'my-bucket' AND `object_key` LIKE 'prefix/%';

-- Count objects in a bucket
-- SELECT COUNT(*) FROM `m` WHERE `bucket_name` = 'my-bucket';

-- Get total size of objects in a bucket
-- SELECT SUM(`size`) as total_size FROM `m` WHERE `bucket_name` = 'my-bucket';

-- Query objects modified in last 24 hours (ut is Unix timestamp in milliseconds)
-- SELECT * FROM `m` 
-- WHERE `bucket_name` = 'my-bucket' 
-- AND `ut` >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 24 HOUR)) * 1000
-- ORDER BY `ut` DESC;

-- Query objects by size range
-- SELECT * FROM `m` 
-- WHERE `bucket_name` = 'my-bucket' 
-- AND `size` >= 1024 AND `size` <= 1048576; -- 1KB to 1MB

-- Query objects with specific metadata key (metadata is stored as TEXT/JSON string)
-- SELECT * FROM `m` 
-- WHERE `bucket_name` = 'my-bucket' 
-- AND `metadata` LIKE '%"custom_key"%';

-- Statistics by content type
-- SELECT `content_type`, COUNT(*) as count, SUM(`size`) as total_size
-- FROM `m`
-- WHERE `bucket_name` = 'my-bucket'
-- GROUP BY `content_type`
-- ORDER BY count DESC;

-- Find duplicate ETags (potential duplicate files)
-- SELECT `etag`, COUNT(*) as count, GROUP_CONCAT(CONCAT(`bucket_name`, '/', `object_key`) SEPARATOR ', ') as objects
-- FROM `m`
-- GROUP BY `etag`
-- HAVING count > 1;

