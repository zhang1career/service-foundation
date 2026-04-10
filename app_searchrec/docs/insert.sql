-- Derived from app_searchrec migrations (Django). MySQL 8.0.16+ for CHECK constraints on `doc`.
-- MySQL / InnoDB / utf8mb4. Create `reg` first (referenced by other tables).

CREATE TABLE `reg` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `name` varchar(128) NOT NULL,
  `access_key` varchar(64) NOT NULL,
  `status` smallint(6) NOT NULL DEFAULT 0,
  `ct` bigint(20) UNSIGNED NOT NULL DEFAULT 0,
  `ut` bigint(20) UNSIGNED NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uni_search_reg_access_key` (`access_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `doc` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `rid` bigint(20) NOT NULL,
  `doc_key` varchar(191) NOT NULL COMMENT 'business document id',
  `title` varchar(512) NOT NULL,
  `content` longtext NOT NULL,
  `tags` longtext NOT NULL,
  `lexical_norm_sq` bigint(20) NOT NULL DEFAULT 0 COMMENT 'sum(tf^2), tf integer',
  `score_boost` decimal(4,2) NOT NULL DEFAULT 1.00,
  `popularity_score` decimal(5,4) NOT NULL DEFAULT 0.0000,
  `freshness_score` decimal(5,4) NOT NULL DEFAULT 0.0000,
  `ct` bigint(20) NOT NULL,
  `ut` bigint(20) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uni_search_doc_doc` (`rid`, `doc_key`),
  CONSTRAINT `searchrec_doc_popularity_unit` CHECK (`popularity_score` >= 0 AND `popularity_score` <= 1),
  CONSTRAINT `searchrec_doc_freshness_unit` CHECK (`freshness_score` >= 0 AND `freshness_score` <= 1)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `doc_term` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `rid` bigint(20) NOT NULL,
  `doc_key` varchar(191) NOT NULL,
  `term` varchar(191) NOT NULL,
  `tf` int(10) UNSIGNED NOT NULL DEFAULT 1,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uni_search_doc_term` (`rid`, `doc_key`, `term`),
  KEY `uni_search_doc_term_term` (`term`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `event` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `rid` bigint(20) NOT NULL,
  `event_type` int(11) NOT NULL,
  `payload` longtext NOT NULL,
  `uid` bigint(20) DEFAULT NULL,
  `did` varchar(191) DEFAULT NULL,
  `ct` bigint(20) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_search_event_type` (`rid`, `event_type`, `ct`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
