CREATE DATABASE IF NOT EXISTS `sf` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci */;
USE `sf`;

-- Dumping structure for table sf.auth_group
CREATE TABLE IF NOT EXISTS `auth_group` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Data exporting was unselected.

-- Dumping structure for table sf.auth_group_permissions
CREATE TABLE IF NOT EXISTS `auth_group_permissions` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `group_id` int(11) NOT NULL,
  `permission_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_group_permissions_group_id_permission_id_0cd325b0_uniq` (`group_id`,`permission_id`),
  KEY `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_group_permissions_group_id_b120cbf9_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Data exporting was unselected.

-- Dumping structure for table sf.auth_permission
CREATE TABLE IF NOT EXISTS `auth_permission` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `content_type_id` int(11) NOT NULL,
  `codename` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_permission_content_type_id_codename_01ab375a_uniq` (`content_type_id`,`codename`),
  CONSTRAINT `auth_permission_content_type_id_2f476e4b_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2565 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Data exporting was unselected.

-- Dumping structure for table sf.auth_user
CREATE TABLE IF NOT EXISTS `auth_user` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `password` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `last_login` datetime(6) DEFAULT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `username` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `first_name` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `last_name` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `email` varchar(254) COLLATE utf8mb4_unicode_ci NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `date_joined` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Data exporting was unselected.

-- Dumping structure for table sf.auth_user_groups
CREATE TABLE IF NOT EXISTS `auth_user_groups` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `group_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_user_groups_user_id_group_id_94350c0c_uniq` (`user_id`,`group_id`),
  KEY `auth_user_groups_group_id_97559544_fk_auth_group_id` (`group_id`),
  CONSTRAINT `auth_user_groups_group_id_97559544_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`),
  CONSTRAINT `auth_user_groups_user_id_6a12ed8b_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Data exporting was unselected.

-- Dumping structure for table sf.auth_user_user_permissions
CREATE TABLE IF NOT EXISTS `auth_user_user_permissions` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `permission_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_user_user_permissions_user_id_permission_id_14a6b632_uniq` (`user_id`,`permission_id`),
  KEY `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_user_user_permissions_user_id_a95ead1b_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Data exporting was unselected.

-- Dumping structure for table sf.django_admin_log
CREATE TABLE IF NOT EXISTS `django_admin_log` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `action_time` datetime(6) NOT NULL,
  `object_id` longtext COLLATE utf8mb4_unicode_ci,
  `object_repr` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `action_flag` smallint(5) unsigned NOT NULL,
  `change_message` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `content_type_id` int(11) DEFAULT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `django_admin_log_content_type_id_c4bce8eb_fk_django_co` (`content_type_id`),
  KEY `django_admin_log_user_id_c564eba6_fk_auth_user_id` (`user_id`),
  CONSTRAINT `django_admin_log_content_type_id_c4bce8eb_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  CONSTRAINT `django_admin_log_user_id_c564eba6_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Data exporting was unselected.

-- Dumping structure for table sf.django_content_type
CREATE TABLE IF NOT EXISTS `django_content_type` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `app_label` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `model` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `django_content_type_app_label_model_76bd3d3b_uniq` (`app_label`,`model`)
) ENGINE=InnoDB AUTO_INCREMENT=642 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Data exporting was unselected.

-- Dumping structure for table sf.django_migrations
CREATE TABLE IF NOT EXISTS `django_migrations` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `app` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `applied` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=28 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Data exporting was unselected.

-- Dumping structure for table sf.django_session
CREATE TABLE IF NOT EXISTS `django_session` (
  `session_key` varchar(40) COLLATE utf8mb4_unicode_ci NOT NULL,
  `session_data` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `expire_date` datetime(6) NOT NULL,
  PRIMARY KEY (`session_key`),
  KEY `django_session_expire_date_a5c62663` (`expire_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Data exporting was unselected.


-- Dumping database structure for sf_ai
CREATE DATABASE IF NOT EXISTS `sf_ai` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci */;
USE `sf_ai`;

-- Dumping structure for table sf_ai.ai_asset
CREATE TABLE IF NOT EXISTS `ai_asset` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `reg_id` bigint(20) unsigned NOT NULL DEFAULT '0',
  `oss_bucket` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `oss_key` varchar(512) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `content_type` tinyint(4) NOT NULL DEFAULT '0',
  `ct` bigint(20) unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`) USING BTREE,
  KEY `idx_ai_asset_reg` (`reg_id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Data exporting was unselected.

-- Dumping structure for table sf_ai.ai_idem
CREATE TABLE IF NOT EXISTS `ai_idem` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `reg_id` bigint(20) unsigned NOT NULL DEFAULT '0',
  `idem_key` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `req_hash` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `resp_json` text COLLATE utf8mb4_unicode_ci,
  `ct` bigint(20) unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE KEY `uni_ai_idem_reg` (`reg_id`,`idem_key`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='幂等控制';

-- Data exporting was unselected.

-- Dumping structure for table sf_ai.ai_job
CREATE TABLE IF NOT EXISTS `ai_job` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `reg_id` bigint(20) unsigned NOT NULL DEFAULT '0',
  `job_type` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `status` tinyint(3) unsigned NOT NULL DEFAULT '0' COMMENT '0=pending,1=running,2=done,3=failed',
  `callback_url` varchar(1024) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `payload_json` text COLLATE utf8mb4_unicode_ci,
  `result_json` text COLLATE utf8mb4_unicode_ci,
  `message` varchar(512) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `ct` bigint(20) unsigned NOT NULL DEFAULT '0',
  `ut` bigint(20) unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`) USING BTREE,
  KEY `idx_ai_job_reg_status` (`reg_id`,`status`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Data exporting was unselected.

-- Dumping structure for table sf_ai.ai_model
CREATE TABLE IF NOT EXISTS `ai_model` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `provider_id` bigint(20) unsigned NOT NULL DEFAULT '0',
  `model_name` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `capability` tinyint(3) unsigned NOT NULL DEFAULT '0' COMMENT '0=chat,1=image,2=video',
  `status` tinyint(2) NOT NULL DEFAULT '0',
  `ct` bigint(20) unsigned NOT NULL DEFAULT '0',
  `ut` bigint(20) unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`) USING BTREE,
  KEY `idx_ai_model_provider` (`provider_id`,`status`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Data exporting was unselected.

-- Dumping structure for table sf_ai.ai_provider
CREATE TABLE IF NOT EXISTS `ai_provider` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `base_url` varchar(512) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `api_key` varchar(512) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `status` tinyint(2) NOT NULL DEFAULT '0',
  `ct` bigint(20) unsigned NOT NULL DEFAULT '0',
  `ut` bigint(20) unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Data exporting was unselected.

-- Dumping structure for table sf_ai.call_log
CREATE TABLE IF NOT EXISTS `call_log` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `reg_id` bigint(20) unsigned NOT NULL DEFAULT '0',
  `template_id` bigint(20) unsigned NOT NULL DEFAULT '0',
  `provider_id` bigint(20) unsigned NOT NULL DEFAULT '0',
  `model_id` bigint(20) unsigned NOT NULL DEFAULT '0',
  `latency_ms` int(11) unsigned NOT NULL DEFAULT '0',
  `success` tinyint(2) NOT NULL DEFAULT '0',
  `error_message` varchar(512) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `ct` bigint(20) unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`) USING BTREE,
  KEY `idx_ai_log_reg` (`reg_id`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='调用日志';

-- Data exporting was unselected.

-- Dumping structure for table sf_ai.prompt_tpl
CREATE TABLE IF NOT EXISTS `prompt_tpl` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `template_key` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `description` varchar(512) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `body` text COLLATE utf8mb4_unicode_ci,
  `input_variables` text COLLATE utf8mb4_unicode_ci COMMENT 'json',
  `output_variables` text COLLATE utf8mb4_unicode_ci COMMENT 'json',
  `constraint_type` tinyint(3) unsigned NOT NULL DEFAULT '0' COMMENT '0=weak,1=strong',
  `status` tinyint(2) NOT NULL DEFAULT '0',
  `ct` bigint(20) unsigned NOT NULL DEFAULT '0',
  `ut` bigint(20) unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE KEY `uni_ai_tpl` (`template_key`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='提示词模版';

-- Data exporting was unselected.

-- Dumping structure for table sf_ai.reg
CREATE TABLE IF NOT EXISTS `reg` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT '名称',
  `access_key` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `callback_secret` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `status` tinyint(2) NOT NULL DEFAULT '0' COMMENT '状态',
  `ct` bigint(20) unsigned NOT NULL DEFAULT '0' COMMENT '创建时间',
  `ut` bigint(20) unsigned NOT NULL DEFAULT '0' COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE KEY `uni_ai_reg_access` (`access_key`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Data exporting was unselected.


-- Dumping database structure for sf_cdn
CREATE DATABASE IF NOT EXISTS `sf_cdn` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci */;
USE `sf_cdn`;

-- Dumping structure for table sf_cdn.d
CREATE TABLE IF NOT EXISTS `d` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `arn` varchar(256) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `status` tinyint(4) NOT NULL DEFAULT '0',
  `domain_name` varchar(256) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `origin_config` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `aliases` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `enabled` tinyint(1) NOT NULL DEFAULT '0',
  `comment` varchar(256) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `etag` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `ct` bigint(20) unsigned NOT NULL DEFAULT '0',
  `ut` bigint(20) unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='CDN distribution';

-- Data exporting was unselected.

-- Dumping structure for table sf_cdn.invalid
CREATE TABLE IF NOT EXISTS `invalid` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `did` bigint(20) NOT NULL DEFAULT '0',
  `caller_reference` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `paths` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `status` smallint(6) NOT NULL DEFAULT '0',
  `ct` bigint(20) unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='CDN cache invalidation';

-- Data exporting was unselected.


-- Dumping database structure for sf_know
CREATE DATABASE IF NOT EXISTS `sf_know` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci */;
USE `sf_know`;

-- Dumping structure for table sf_know.batch
CREATE TABLE IF NOT EXISTS `batch` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `source_type` tinyint(4) NOT NULL DEFAULT '0' COMMENT '0-instant, 1-file',
  `content` text COLLATE utf8mb4_unicode_ci,
  `ct` bigint(20) unsigned NOT NULL DEFAULT '0' COMMENT '创建时间',
  `ut` bigint(20) unsigned NOT NULL DEFAULT '0' COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  KEY `idx_src` (`ut`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=73 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

-- Data exporting was unselected.

-- Dumping structure for table sf_know.insight
CREATE TABLE IF NOT EXISTS `insight` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `content` text COLLATE utf8mb4_unicode_ci,
  `perspective` int(11) NOT NULL DEFAULT '0' COMMENT '0-persion, 1-concept, 2-metric',
  `type` int(11) NOT NULL DEFAULT '0' COMMENT '0-contradiction, 1-path_reasoning, 2-cross_text',
  `status` int(11) NOT NULL DEFAULT '0' COMMENT '0-draft, 1-adopted',
  `ct` bigint(20) unsigned NOT NULL DEFAULT '0' COMMENT '创建时间',
  `ut` bigint(20) unsigned NOT NULL DEFAULT '0' COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  KEY `idx_src` (`ut`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

-- Data exporting was unselected.

-- Dumping structure for table sf_know.knowledge
CREATE TABLE IF NOT EXISTS `knowledge` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `batch_id` bigint(20) unsigned NOT NULL DEFAULT '0',
  `content` text COLLATE utf8mb4_unicode_ci COMMENT '知识内容',
  `seq` int(10) unsigned NOT NULL DEFAULT '0',
  `classification` tinyint(4) NOT NULL DEFAULT '0',
  `stage` tinyint(4) NOT NULL DEFAULT '0',
  `status` tinyint(4) NOT NULL DEFAULT '0',
  `brief` varchar(512) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `g_brief` varchar(512) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `g_brief_hash` int(11) unsigned NOT NULL DEFAULT '0',
  `g_sub` varchar(256) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `g_sub_hash` int(11) unsigned NOT NULL DEFAULT '0',
  `v_sub_deco_id` char(32) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `g_obj` varchar(256) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `g_obj_hash` int(11) unsigned NOT NULL DEFAULT '0',
  `v_obj_deco_id` char(32) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `ct` bigint(20) unsigned NOT NULL DEFAULT '0' COMMENT '创建时间',
  `ut` bigint(20) unsigned NOT NULL DEFAULT '0' COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  KEY `idx_src` (`ut`) USING BTREE,
  KEY `idx_graph_sub` (`g_sub_hash`) USING BTREE,
  KEY `idx_graph_obj` (`g_obj_hash`) USING BTREE,
  KEY `idx_vec_sub` (`v_sub_deco_id`) USING BTREE,
  KEY `idx_vec_obj` (`v_obj_deco_id`) USING BTREE,
  KEY `idx_graph_brief` (`g_brief_hash`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=78 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

-- Data exporting was unselected.

-- Dumping structure for table sf_know.knowledge_bkp
CREATE TABLE IF NOT EXISTS `knowledge_bkp` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `title` varchar(512) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT '名称',
  `description` text COLLATE utf8mb4_unicode_ci COMMENT '描述',
  `content` text COLLATE utf8mb4_unicode_ci COMMENT '知识内容',
  `source_type` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `ct` bigint(20) unsigned NOT NULL DEFAULT '0' COMMENT '创建时间',
  `ut` bigint(20) unsigned NOT NULL DEFAULT '0' COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  KEY `idx_src` (`source_type`,`ut`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=58 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

-- Data exporting was unselected.


-- Dumping database structure for sf_mailserver
CREATE DATABASE IF NOT EXISTS `sf_mailserver` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci */;
USE `sf_mailserver`;

-- Dumping structure for table sf_mailserver.mailbox
CREATE TABLE IF NOT EXISTS `mailbox` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT COMMENT 'primary key id',
  `account_id` bigint(20) NOT NULL DEFAULT '0' COMMENT 'mail account id (maintained by application)',
  `name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT 'mailbox name (e.g., INBOX, Sent, Drafts, Trash)',
  `path` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT 'mailbox path (IMAP format, e.g., INBOX, INBOX.Sent)',
  `message_count` int(11) NOT NULL DEFAULT '0' COMMENT 'number of messages',
  `unread_count` int(11) NOT NULL DEFAULT '0' COMMENT 'number of unread messages',
  `ct` bigint(20) NOT NULL DEFAULT '0' COMMENT 'creation time, UNIX timestamp in milliseconds',
  `ut` bigint(20) NOT NULL DEFAULT '0' COMMENT 'update time, UNIX timestamp in milliseconds',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE KEY `uni_account_path` (`account_id`,`path`) USING BTREE,
  KEY `idx_mailbox_name` (`name`) USING BTREE,
  KEY `idx_mailbox_path` (`path`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='mailbox (folder)';

-- Data exporting was unselected.

-- Dumping structure for table sf_mailserver.mail_account
CREATE TABLE IF NOT EXISTS `mail_account` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT COMMENT 'primary key id',
  `username` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT 'email address (username)',
  `password` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT 'encrypted password',
  `domain` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT 'domain name',
  `is_active` tinyint(1) NOT NULL DEFAULT '0' COMMENT 'whether account is active',
  `ct` bigint(20) NOT NULL DEFAULT '0' COMMENT 'creation time, UNIX timestamp in milliseconds',
  `ut` bigint(20) NOT NULL DEFAULT '0' COMMENT 'update time, UNIX timestamp in milliseconds',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE KEY `uni_username` (`username`) USING BTREE,
  KEY `idx_mail_account_domain` (`domain`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='mail account';

-- Data exporting was unselected.

-- Dumping structure for table sf_mailserver.mail_attachment
CREATE TABLE IF NOT EXISTS `mail_attachment` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT COMMENT 'primary key id',
  `message_id` bigint(20) NOT NULL DEFAULT '0' COMMENT 'mail message id (maintained by application)',
  `filename` varchar(512) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT 'attachment filename',
  `content_type` int(10) NOT NULL DEFAULT '0' COMMENT 'MIME type, 0=application/octet-stream',
  `size` bigint(20) NOT NULL DEFAULT '0' COMMENT 'attachment size in bytes',
  `oss_bucket` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT 'OSS bucket name',
  `oss_key` varchar(512) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT 'OSS object key (path)',
  `content_id` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT 'Content-ID (for embedded images, etc.)',
  `content_disposition` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'attachment' COMMENT 'Content-Disposition (attachment or inline)',
  `ct` bigint(20) NOT NULL DEFAULT '0' COMMENT 'creation time, UNIX timestamp in milliseconds',
  PRIMARY KEY (`id`) USING BTREE,
  KEY `idx_mail_attachment_message` (`message_id`) USING BTREE,
  KEY `idx_mail_attachment_oss` (`oss_bucket`,`oss_key`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='mail attachment table';

-- Data exporting was unselected.

-- Dumping structure for table sf_mailserver.mail_message
CREATE TABLE IF NOT EXISTS `mail_message` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT COMMENT 'primary key id',
  `account_id` bigint(20) NOT NULL DEFAULT '0' COMMENT 'mail account id (maintained by application)',
  `message_id` varchar(512) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT 'email message-id (unique identifier)',
  `mailbox_id` bigint(20) NOT NULL DEFAULT '0' COMMENT 'mailbox id (maintained by application)',
  `subject` text COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'email subject',
  `from` varchar(512) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT 'sender address',
  `to` text COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'recipient addresses (comma-separated)',
  `cc` text COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'CC addresses (comma-separated)',
  `bcc` text COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'BCC addresses (comma-separated)',
  `text_body` text COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'email text body',
  `html_body` text COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'email HTML body',
  `mt` bigint(20) NOT NULL DEFAULT '0' COMMENT 'email date, UNIX timestamp in milliseconds',
  `is_read` tinyint(1) NOT NULL DEFAULT '0' COMMENT 'whether message is read',
  `is_flagged` tinyint(1) NOT NULL DEFAULT '0' COMMENT 'whether message is flagged',
  `size` bigint(20) NOT NULL DEFAULT '0' COMMENT 'email size in bytes',
  `raw_message` text COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'raw email content (for complete reconstruction)',
  `ct` bigint(20) NOT NULL DEFAULT '0' COMMENT 'creation time, UNIX timestamp in milliseconds',
  `ut` bigint(20) NOT NULL DEFAULT '0' COMMENT 'update time, UNIX timestamp in milliseconds',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE KEY `uni_account_message` (`account_id`,`message_id`) USING BTREE,
  KEY `idx_mail_message_account_mailbox_date` (`account_id`,`mailbox_id`,`mt`) USING BTREE,
  KEY `idx_mail_message_mailbox` (`mailbox_id`) USING BTREE,
  KEY `idx_mail_message_message` (`message_id`) USING BTREE,
  KEY `idx_mail_message_date` (`mt`) USING BTREE,
  KEY `idx_mail_message_account_is_read` (`account_id`,`is_read`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='mail message table';

-- Data exporting was unselected.


-- Dumping database structure for sf_notice
CREATE DATABASE IF NOT EXISTS `sf_notice` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci */;
USE `sf_notice`;

-- Dumping structure for table sf_notice.notice
CREATE TABLE IF NOT EXISTS `notice` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `reg_id` bigint(20) unsigned NOT NULL DEFAULT '0' COMMENT '注册ID',
  `event_id` bigint(20) unsigned NOT NULL DEFAULT '0' COMMENT '事件ID',
  `channel` tinyint(3) unsigned NOT NULL DEFAULT '0',
  `target` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `subject` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `content` text COLLATE utf8mb4_unicode_ci,
  `status` tinyint(2) NOT NULL DEFAULT '0',
  `provider` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `message` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `ct` bigint(20) NOT NULL DEFAULT '0',
  `ut` bigint(20) NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`) USING BTREE,
  KEY `idx_notice_channel_status_ct` (`channel`,`status`,`ct`) USING BTREE,
  KEY `idx_notice_target_ct` (`target`,`ct`) USING BTREE,
  KEY `idx_notice_reg_event` (`reg_id`,`event_id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='通知记录';

-- Data exporting was unselected.

-- Dumping structure for table sf_notice.reg
CREATE TABLE IF NOT EXISTS `reg` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `access_key` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `status` tinyint(2) NOT NULL DEFAULT '0',
  `ct` bigint(20) unsigned NOT NULL DEFAULT '0',
  `ut` bigint(20) unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE KEY `uni_notice_reg_access_key` (`access_key`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='注册表';

-- Data exporting was unselected.


-- Dumping database structure for sf_oss
CREATE DATABASE IF NOT EXISTS `sf_oss` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci */;
USE `sf_oss`;

-- Dumping structure for table sf_oss.m
CREATE TABLE IF NOT EXISTS `m` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT COMMENT 'primary key id',
  `bucket_name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT 'bucket name',
  `object_key` varchar(512) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT 'object key (path)',
  `content_type` int(11) NOT NULL DEFAULT '0' COMMENT 'content type enum id (0=application/octet-stream)',
  `content_length` bigint(20) NOT NULL DEFAULT '0' COMMENT 'content length in bytes',
  `etag` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT 'ETag (MD5 hash)',
  `size` bigint(20) NOT NULL DEFAULT '0' COMMENT 'file size in bytes',
  `metadata` text COLLATE utf8mb4_unicode_ci COMMENT 'user-defined metadata (JSON format)',
  `ut` bigint(20) NOT NULL COMMENT 'update (last modification) time, UNIX timestamp in ms',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE KEY `uni_bucket_key` (`bucket_name`,`object_key`) USING BTREE,
  KEY `idx_object_key` (`object_key`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=34 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='OSS object metadata table';

-- Data exporting was unselected.


-- Dumping database structure for sf_searchrec
CREATE DATABASE IF NOT EXISTS `sf_searchrec` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci */;
USE `sf_searchrec`;

-- Dumping structure for table sf_searchrec.searchrec_document
CREATE TABLE IF NOT EXISTS `searchrec_document` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `biz_doc_id` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `title` varchar(512) COLLATE utf8mb4_unicode_ci NOT NULL,
  `content` mediumtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `tags` json DEFAULT NULL,
  `score_boost` decimal(8,4) NOT NULL DEFAULT '1.0000',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `biz_doc_id` (`biz_doc_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Data exporting was unselected.

-- Dumping structure for table sf_searchrec.searchrec_event_log
CREATE TABLE IF NOT EXISTS `searchrec_event_log` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `user_id` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `event_type` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `event_payload` json DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_event_type_ct` (`event_type`,`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Data exporting was unselected.


-- Dumping database structure for sf_snowflake
CREATE DATABASE IF NOT EXISTS `sf_snowflake` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci */;
USE `sf_snowflake`;

-- Dumping structure for table sf_snowflake.event
CREATE TABLE IF NOT EXISTS `event` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT COMMENT 'Primary key ID',
  `dcid` int(10) unsigned NOT NULL DEFAULT '0' COMMENT 'datacenter id',
  `mid` int(10) unsigned NOT NULL DEFAULT '0' COMMENT 'machine id',
  `event_type` int(11) NOT NULL DEFAULT '0' COMMENT 'event type',
  `brief` text COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'event message',
  `detail` text COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'detailed information (JSON format)',
  `ct` bigint(20) unsigned NOT NULL DEFAULT '0' COMMENT 'creation time, UNIX timestamp in ms',
  PRIMARY KEY (`id`),
  KEY `idx_dc_mac` (`dcid`,`mid`,`event_type`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=196 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='event log';

-- Data exporting was unselected.

-- Dumping structure for table sf_snowflake.recounter
CREATE TABLE IF NOT EXISTS `recounter` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT COMMENT 'primary key id',
  `dcid` int(10) unsigned NOT NULL DEFAULT '0' COMMENT 'datacenter id (0-3)',
  `mid` int(10) unsigned NOT NULL DEFAULT '0' COMMENT 'machine id (0-7)',
  `rc` int(10) unsigned NOT NULL DEFAULT '0' COMMENT 're-counter (0-3)',
  `ct` bigint(20) unsigned NOT NULL DEFAULT '0' COMMENT 'create time, UNIX timestamp in ms',
  `ut` bigint(20) DEFAULT '0' COMMENT 'update time, UNIX timestamp in ms',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE KEY `uni_dc_mac` (`dcid`,`mid`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=131 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='re-counter for restart/clockback';

-- Data exporting was unselected.


-- Dumping database structure for sf_test
CREATE DATABASE IF NOT EXISTS `sf_test` /*!40100 DEFAULT CHARACTER SET latin1 */;
USE `sf_test`;

-- Dumping structure for table sf_test.auth_group
CREATE TABLE IF NOT EXISTS `auth_group` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(150) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- Data exporting was unselected.

-- Dumping structure for table sf_test.auth_group_permissions
CREATE TABLE IF NOT EXISTS `auth_group_permissions` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `group_id` int(11) NOT NULL,
  `permission_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_group_permissions_group_id_permission_id_0cd325b0_uniq` (`group_id`,`permission_id`),
  KEY `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_group_permissions_group_id_b120cbf9_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- Data exporting was unselected.

-- Dumping structure for table sf_test.auth_permission
CREATE TABLE IF NOT EXISTS `auth_permission` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `content_type_id` int(11) NOT NULL,
  `codename` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_permission_content_type_id_codename_01ab375a_uniq` (`content_type_id`,`codename`),
  CONSTRAINT `auth_permission_content_type_id_2f476e4b_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=85 DEFAULT CHARSET=latin1;

-- Data exporting was unselected.

-- Dumping structure for table sf_test.auth_user
CREATE TABLE IF NOT EXISTS `auth_user` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `password` varchar(128) NOT NULL,
  `last_login` datetime(6) DEFAULT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `username` varchar(150) NOT NULL,
  `first_name` varchar(150) NOT NULL,
  `last_name` varchar(150) NOT NULL,
  `email` varchar(254) NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `date_joined` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- Data exporting was unselected.

-- Dumping structure for table sf_test.auth_user_groups
CREATE TABLE IF NOT EXISTS `auth_user_groups` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `group_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_user_groups_user_id_group_id_94350c0c_uniq` (`user_id`,`group_id`),
  KEY `auth_user_groups_group_id_97559544_fk_auth_group_id` (`group_id`),
  CONSTRAINT `auth_user_groups_group_id_97559544_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`),
  CONSTRAINT `auth_user_groups_user_id_6a12ed8b_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- Data exporting was unselected.

-- Dumping structure for table sf_test.auth_user_user_permissions
CREATE TABLE IF NOT EXISTS `auth_user_user_permissions` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `permission_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_user_user_permissions_user_id_permission_id_14a6b632_uniq` (`user_id`,`permission_id`),
  KEY `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_user_user_permissions_user_id_a95ead1b_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- Data exporting was unselected.

-- Dumping structure for table sf_test.django_admin_log
CREATE TABLE IF NOT EXISTS `django_admin_log` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `action_time` datetime(6) NOT NULL,
  `object_id` longtext,
  `object_repr` varchar(200) NOT NULL,
  `action_flag` smallint(5) unsigned NOT NULL,
  `change_message` longtext NOT NULL,
  `content_type_id` int(11) DEFAULT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `django_admin_log_content_type_id_c4bce8eb_fk_django_co` (`content_type_id`),
  KEY `django_admin_log_user_id_c564eba6_fk_auth_user_id` (`user_id`),
  CONSTRAINT `django_admin_log_content_type_id_c4bce8eb_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  CONSTRAINT `django_admin_log_user_id_c564eba6_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- Data exporting was unselected.

-- Dumping structure for table sf_test.django_content_type
CREATE TABLE IF NOT EXISTS `django_content_type` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `app_label` varchar(100) NOT NULL,
  `model` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `django_content_type_app_label_model_76bd3d3b_uniq` (`app_label`,`model`)
) ENGINE=InnoDB AUTO_INCREMENT=22 DEFAULT CHARSET=latin1;

-- Data exporting was unselected.

-- Dumping structure for table sf_test.django_migrations
CREATE TABLE IF NOT EXISTS `django_migrations` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `app` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `applied` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=27 DEFAULT CHARSET=latin1;

-- Data exporting was unselected.

-- Dumping structure for table sf_test.django_session
CREATE TABLE IF NOT EXISTS `django_session` (
  `session_key` varchar(40) NOT NULL,
  `session_data` longtext NOT NULL,
  `expire_date` datetime(6) NOT NULL,
  PRIMARY KEY (`session_key`),
  KEY `django_session_expire_date_a5c62663` (`expire_date`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- Data exporting was unselected.

-- Dumping structure for table sf_test.mailbox
CREATE TABLE IF NOT EXISTS `mailbox` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `account_id` bigint(20) NOT NULL,
  `name` varchar(100) NOT NULL,
  `path` varchar(255) NOT NULL,
  `message_count` int(11) NOT NULL,
  `unread_count` int(11) NOT NULL,
  `ct` bigint(20) NOT NULL,
  `ut` bigint(20) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `mailbox_account_id_path_a9a5a180_uniq` (`account_id`,`path`),
  KEY `mailbox_account_id_825addea` (`account_id`),
  KEY `mailbox_name_b5d5ec3a` (`name`),
  KEY `mailbox_path_5dfdf365` (`path`),
  KEY `mailbox_ct_f1d02de1` (`ct`),
  KEY `mailbox_ut_75a18b36` (`ut`),
  KEY `mailbox_account_7156f3_idx` (`account_id`,`name`),
  KEY `mailbox_account_d1075c_idx` (`account_id`,`path`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- Data exporting was unselected.

-- Dumping structure for table sf_test.mail_account
CREATE TABLE IF NOT EXISTS `mail_account` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `username` varchar(255) NOT NULL,
  `password` varchar(255) NOT NULL,
  `domain` varchar(255) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `ct` bigint(20) NOT NULL,
  `ut` bigint(20) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`),
  KEY `mail_account_domain_ba3cce4f` (`domain`),
  KEY `mail_account_ct_09283952` (`ct`),
  KEY `mail_account_ut_5ae4cea9` (`ut`),
  KEY `mail_accoun_usernam_9e4ccb_idx` (`username`),
  KEY `mail_accoun_domain_a3f733_idx` (`domain`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- Data exporting was unselected.

-- Dumping structure for table sf_test.mail_attachment
CREATE TABLE IF NOT EXISTS `mail_attachment` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `message_id` bigint(20) NOT NULL,
  `filename` varchar(512) NOT NULL,
  `content_type` int(11) NOT NULL,
  `size` bigint(20) NOT NULL,
  `oss_bucket` varchar(255) NOT NULL,
  `oss_key` varchar(1024) NOT NULL,
  `content_id` varchar(255) NOT NULL,
  `content_disposition` varchar(50) NOT NULL,
  `ct` bigint(20) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `mail_attachment_message_id_12abed35` (`message_id`),
  KEY `mail_attachment_ct_f7b401af` (`ct`),
  KEY `mail_attach_message_837844_idx` (`message_id`),
  KEY `mail_attach_oss_buc_8c0fd9_idx` (`oss_bucket`,`oss_key`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- Data exporting was unselected.

-- Dumping structure for table sf_test.mail_message
CREATE TABLE IF NOT EXISTS `mail_message` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `account_id` bigint(20) NOT NULL,
  `mailbox_id` bigint(20) NOT NULL,
  `message_id` varchar(512) NOT NULL,
  `subject` longtext NOT NULL,
  `from` varchar(512) NOT NULL,
  `to` longtext NOT NULL,
  `cc` longtext NOT NULL,
  `bcc` longtext NOT NULL,
  `text_body` longtext NOT NULL,
  `html_body` longtext NOT NULL,
  `mt` bigint(20) NOT NULL,
  `is_read` tinyint(1) NOT NULL,
  `is_flagged` tinyint(1) NOT NULL,
  `size` bigint(20) NOT NULL,
  `raw_message` longtext NOT NULL,
  `ct` bigint(20) NOT NULL,
  `ut` bigint(20) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `mail_message_account_id_message_id_35767989_uniq` (`account_id`,`message_id`),
  KEY `mail_message_account_id_174a598c` (`account_id`),
  KEY `mail_message_mailbox_id_3e3ef837` (`mailbox_id`),
  KEY `mail_message_message_id_fd6a0095` (`message_id`),
  KEY `mail_message_mt_a4f546bd` (`mt`),
  KEY `mail_message_ct_bdf0b427` (`ct`),
  KEY `mail_message_ut_5cc87ac0` (`ut`),
  KEY `mail_messag_account_650d98_idx` (`account_id`,`mailbox_id`,`mt`),
  KEY `mail_messag_account_3dc1b7_idx` (`account_id`,`is_read`),
  KEY `mail_messag_message_0c099a_idx` (`message_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- Data exporting was unselected.


-- Dumping database structure for sf_user
CREATE DATABASE IF NOT EXISTS `sf_user` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci */;
USE `sf_user`;

-- Dumping structure for table sf_user.event
CREATE TABLE IF NOT EXISTS `event` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `biz_type` tinyint(4) NOT NULL DEFAULT '0' COMMENT '0-unknown, 1- register, 2-update_profile',
  `status` tinyint(2) NOT NULL DEFAULT '0',
  `level` tinyint(3) unsigned NOT NULL DEFAULT '3',
  `verify_code_id` bigint(20) unsigned NOT NULL DEFAULT '0',
  `verify_ref_id` bigint(20) unsigned NOT NULL DEFAULT '0',
  `notice_target` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `notice_channel` tinyint(3) unsigned NOT NULL DEFAULT '0',
  `payload_json` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `message` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `ct` bigint(20) unsigned NOT NULL DEFAULT '0',
  `ut` bigint(20) unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`) USING BTREE,
  KEY `idx_event_biz_status_ct` (`biz_type`,`status`,`ct`) USING BTREE,
  KEY `idx_event_verify_code_id` (`verify_code_id`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Data exporting was unselected.

-- Dumping structure for table sf_user.user
CREATE TABLE IF NOT EXISTS `user` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `pw_hash` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT 'password hash',
  `email` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `phone` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `avatar` varchar(512) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT 'avatar url',
  `status` tinyint(2) NOT NULL DEFAULT '0' COMMENT '用户状态，0-未激活，1-激活',
  `auth_status` smallint(5) unsigned NOT NULL DEFAULT '0' COMMENT '认证状态 bitmask，0-未认证',
  `ext` text COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '扩展',
  `ct` bigint(20) unsigned NOT NULL DEFAULT '0',
  `ut` bigint(20) unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE KEY `uni_user_email` (`email`) USING BTREE,
  UNIQUE KEY `uni_user_phone` (`phone`) USING BTREE,
  UNIQUE KEY `uni_user_name` (`name`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- Data exporting was unselected.


-- Dumping database structure for sf_verify
CREATE DATABASE IF NOT EXISTS `sf_verify` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci */;
USE `sf_verify`;

-- Dumping structure for table sf_verify.reg
CREATE TABLE IF NOT EXISTS `reg` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `access_key` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `status` tinyint(2) NOT NULL DEFAULT '0',
  `ct` bigint(20) unsigned NOT NULL DEFAULT '0',
  `ut` bigint(20) unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE KEY `uni_verify_reg_access_key` (`access_key`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户注册';

-- Data exporting was unselected.

-- Dumping structure for table sf_verify.verify_code
CREATE TABLE IF NOT EXISTS `verify_code` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `level` tinyint(4) NOT NULL DEFAULT '0' COMMENT '安全等级：0-pass, 1-low, 2-medium, 3-high',
  `code` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `reg_id` bigint(20) unsigned NOT NULL DEFAULT '0' COMMENT '注册ID',
  `ref_id` bigint(20) unsigned NOT NULL DEFAULT '0',
  `expires_at` bigint(20) unsigned NOT NULL DEFAULT '0',
  `used_at` bigint(20) unsigned NOT NULL DEFAULT '0',
  `ct` bigint(20) unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`) USING BTREE,
  KEY `idx_verify_exp` (`expires_at`) USING BTREE,
  KEY `idx_verify_reg_ref` (`reg_id`,`ref_id`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='验证码';
