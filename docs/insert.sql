-- --------------------------------------------------------
-- Host:                         127.0.0.1
-- Server version:               5.7.44 - MySQL Community Server (GPL)
-- Server OS:                    Linux
-- HeidiSQL Version:             11.2.0.6213
-- --------------------------------------------------------

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET NAMES utf8 */;
/*!50503 SET NAMES utf8mb4 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;


-- Dumping database structure for sf
CREATE DATABASE IF NOT EXISTS `sf` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci */;
USE `sf`;

-- Dumping structure for table sf.auth_group
CREATE TABLE IF NOT EXISTS `auth_group` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Dumping data for table sf.auth_group: ~0 rows (approximately)
/*!40000 ALTER TABLE `auth_group` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_group` ENABLE KEYS */;

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

-- Dumping data for table sf.auth_group_permissions: ~0 rows (approximately)
/*!40000 ALTER TABLE `auth_group_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_group_permissions` ENABLE KEYS */;

-- Dumping structure for table sf.auth_permission
CREATE TABLE IF NOT EXISTS `auth_permission` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `content_type_id` int(11) NOT NULL,
  `codename` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_permission_content_type_id_codename_01ab375a_uniq` (`content_type_id`,`codename`),
  CONSTRAINT `auth_permission_content_type_id_2f476e4b_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=10081 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Dumping data for table sf.auth_permission: ~128 rows (approximately)
/*!40000 ALTER TABLE `auth_permission` DISABLE KEYS */;
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES
	(9953, 'Can add log entry', 2489, 'add_logentry'),
	(9954, 'Can change log entry', 2489, 'change_logentry'),
	(9955, 'Can delete log entry', 2489, 'delete_logentry'),
	(9956, 'Can view log entry', 2489, 'view_logentry'),
	(9957, 'Can add permission', 2490, 'add_permission'),
	(9958, 'Can change permission', 2490, 'change_permission'),
	(9959, 'Can delete permission', 2490, 'delete_permission'),
	(9960, 'Can view permission', 2490, 'view_permission'),
	(9961, 'Can add group', 2491, 'add_group'),
	(9962, 'Can change group', 2491, 'change_group'),
	(9963, 'Can delete group', 2491, 'delete_group'),
	(9964, 'Can view group', 2491, 'view_group'),
	(9965, 'Can add user', 2492, 'add_user'),
	(9966, 'Can change user', 2492, 'change_user'),
	(9967, 'Can delete user', 2492, 'delete_user'),
	(9968, 'Can view user', 2492, 'view_user'),
	(9969, 'Can add content type', 2493, 'add_contenttype'),
	(9970, 'Can change content type', 2493, 'change_contenttype'),
	(9971, 'Can delete content type', 2493, 'delete_contenttype'),
	(9972, 'Can view content type', 2493, 'view_contenttype'),
	(9973, 'Can add session', 2494, 'add_session'),
	(9974, 'Can change session', 2494, 'change_session'),
	(9975, 'Can delete session', 2494, 'delete_session'),
	(9976, 'Can view session', 2494, 'view_session'),
	(9977, 'Can add distribution', 2495, 'add_distribution'),
	(9978, 'Can change distribution', 2495, 'change_distribution'),
	(9979, 'Can delete distribution', 2495, 'delete_distribution'),
	(9980, 'Can view distribution', 2495, 'view_distribution'),
	(9981, 'Can add invalidation', 2496, 'add_invalidation'),
	(9982, 'Can change invalidation', 2496, 'change_invalidation'),
	(9983, 'Can delete invalidation', 2496, 'delete_invalidation'),
	(9984, 'Can view invalidation', 2496, 'view_invalidation'),
	(9985, 'Can add cms content meta', 2497, 'add_cmscontentmeta'),
	(9986, 'Can change cms content meta', 2497, 'change_cmscontentmeta'),
	(9987, 'Can delete cms content meta', 2497, 'delete_cmscontentmeta'),
	(9988, 'Can view cms content meta', 2497, 'view_cmscontentmeta'),
	(9989, 'Can add cms media file', 2498, 'add_cmsmediafile'),
	(9990, 'Can change cms media file', 2498, 'change_cmsmediafile'),
	(9991, 'Can delete cms media file', 2498, 'delete_cmsmediafile'),
	(9992, 'Can view cms media file', 2498, 'view_cmsmediafile'),
	(9993, 'Can add knowledge point', 2499, 'add_knowledgepoint'),
	(9994, 'Can change knowledge point', 2499, 'change_knowledgepoint'),
	(9995, 'Can delete knowledge point', 2499, 'delete_knowledgepoint'),
	(9996, 'Can view knowledge point', 2499, 'view_knowledgepoint'),
	(9997, 'Can add insight', 2500, 'add_insight'),
	(9998, 'Can change insight', 2500, 'change_insight'),
	(9999, 'Can delete insight', 2500, 'delete_insight'),
	(10000, 'Can view insight', 2500, 'view_insight'),
	(10001, 'Can add batch', 2501, 'add_batch'),
	(10002, 'Can change batch', 2501, 'change_batch'),
	(10003, 'Can delete batch', 2501, 'delete_batch'),
	(10004, 'Can view batch', 2501, 'view_batch'),
	(10005, 'Can add mail account', 2502, 'add_mailaccount'),
	(10006, 'Can change mail account', 2502, 'change_mailaccount'),
	(10007, 'Can delete mail account', 2502, 'delete_mailaccount'),
	(10008, 'Can view mail account', 2502, 'view_mailaccount'),
	(10009, 'Can add mailbox', 2503, 'add_mailbox'),
	(10010, 'Can change mailbox', 2503, 'change_mailbox'),
	(10011, 'Can delete mailbox', 2503, 'delete_mailbox'),
	(10012, 'Can view mailbox', 2503, 'view_mailbox'),
	(10013, 'Can add mail message', 2504, 'add_mailmessage'),
	(10014, 'Can change mail message', 2504, 'change_mailmessage'),
	(10015, 'Can delete mail message', 2504, 'delete_mailmessage'),
	(10016, 'Can view mail message', 2504, 'view_mailmessage'),
	(10017, 'Can add mail attachment', 2505, 'add_mailattachment'),
	(10018, 'Can change mail attachment', 2505, 'change_mailattachment'),
	(10019, 'Can delete mail attachment', 2505, 'delete_mailattachment'),
	(10020, 'Can view mail attachment', 2505, 'view_mailattachment'),
	(10021, 'Can add notice record', 2506, 'add_noticerecord'),
	(10022, 'Can change notice record', 2506, 'change_noticerecord'),
	(10023, 'Can delete notice record', 2506, 'delete_noticerecord'),
	(10024, 'Can view notice record', 2506, 'view_noticerecord'),
	(10025, 'Can add reg', 2507, 'add_reg'),
	(10026, 'Can change reg', 2507, 'change_reg'),
	(10027, 'Can delete reg', 2507, 'delete_reg'),
	(10028, 'Can view reg', 2507, 'view_reg'),
	(10029, 'Can add metadata', 2508, 'add_metadata'),
	(10030, 'Can change metadata', 2508, 'change_metadata'),
	(10031, 'Can delete metadata', 2508, 'delete_metadata'),
	(10032, 'Can view metadata', 2508, 'view_metadata'),
	(10033, 'Can add search rec reg', 2509, 'add_searchrecreg'),
	(10034, 'Can change search rec reg', 2509, 'change_searchrecreg'),
	(10035, 'Can delete search rec reg', 2509, 'delete_searchrecreg'),
	(10036, 'Can view search rec reg', 2509, 'view_searchrecreg'),
	(10037, 'Can add search rec document', 2510, 'add_searchrecdocument'),
	(10038, 'Can change search rec document', 2510, 'change_searchrecdocument'),
	(10039, 'Can delete search rec document', 2510, 'delete_searchrecdocument'),
	(10040, 'Can view search rec document', 2510, 'view_searchrecdocument'),
	(10041, 'Can add search rec doc term', 2511, 'add_searchrecdocterm'),
	(10042, 'Can change search rec doc term', 2511, 'change_searchrecdocterm'),
	(10043, 'Can delete search rec doc term', 2511, 'delete_searchrecdocterm'),
	(10044, 'Can view search rec doc term', 2511, 'view_searchrecdocterm'),
	(10045, 'Can add search rec event', 2512, 'add_searchrecevent'),
	(10046, 'Can change search rec event', 2512, 'change_searchrecevent'),
	(10047, 'Can delete search rec event', 2512, 'delete_searchrecevent'),
	(10048, 'Can view search rec event', 2512, 'view_searchrecevent'),
	(10049, 'Can add recounter', 2513, 'add_recounter'),
	(10050, 'Can change recounter', 2513, 'change_recounter'),
	(10051, 'Can delete recounter', 2513, 'delete_recounter'),
	(10052, 'Can view recounter', 2513, 'view_recounter'),
	(10053, 'Can add snowflake reg', 2514, 'add_snowflakereg'),
	(10054, 'Can change snowflake reg', 2514, 'change_snowflakereg'),
	(10055, 'Can delete snowflake reg', 2514, 'delete_snowflakereg'),
	(10056, 'Can view snowflake reg', 2514, 'view_snowflakereg'),
	(10057, 'Can add event', 2515, 'add_event'),
	(10058, 'Can change event', 2515, 'change_event'),
	(10059, 'Can delete event', 2515, 'delete_event'),
	(10060, 'Can view event', 2515, 'view_event'),
	(10061, 'Can add token', 2516, 'add_token'),
	(10062, 'Can change token', 2516, 'change_token'),
	(10063, 'Can delete token', 2516, 'delete_token'),
	(10064, 'Can view token', 2516, 'view_token'),
	(10065, 'Can add user', 2517, 'add_user'),
	(10066, 'Can change user', 2517, 'change_user'),
	(10067, 'Can delete user', 2517, 'delete_user'),
	(10068, 'Can view user', 2517, 'view_user'),
	(10069, 'Can add reg', 2518, 'add_reg'),
	(10070, 'Can change reg', 2518, 'change_reg'),
	(10071, 'Can delete reg', 2518, 'delete_reg'),
	(10072, 'Can view reg', 2518, 'view_reg'),
	(10073, 'Can add verify code', 2519, 'add_verifycode'),
	(10074, 'Can change verify code', 2519, 'change_verifycode'),
	(10075, 'Can delete verify code', 2519, 'delete_verifycode'),
	(10076, 'Can view verify code', 2519, 'view_verifycode'),
	(10077, 'Can add verify log', 2520, 'add_verifylog'),
	(10078, 'Can change verify log', 2520, 'change_verifylog'),
	(10079, 'Can delete verify log', 2520, 'delete_verifylog'),
	(10080, 'Can view verify log', 2520, 'view_verifylog');
/*!40000 ALTER TABLE `auth_permission` ENABLE KEYS */;

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

-- Dumping data for table sf.auth_user: ~0 rows (approximately)
/*!40000 ALTER TABLE `auth_user` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_user` ENABLE KEYS */;

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

-- Dumping data for table sf.auth_user_groups: ~0 rows (approximately)
/*!40000 ALTER TABLE `auth_user_groups` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_user_groups` ENABLE KEYS */;

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

-- Dumping data for table sf.auth_user_user_permissions: ~0 rows (approximately)
/*!40000 ALTER TABLE `auth_user_user_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_user_user_permissions` ENABLE KEYS */;

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

-- Dumping data for table sf.django_admin_log: ~0 rows (approximately)
/*!40000 ALTER TABLE `django_admin_log` DISABLE KEYS */;
/*!40000 ALTER TABLE `django_admin_log` ENABLE KEYS */;

-- Dumping structure for table sf.django_content_type
CREATE TABLE IF NOT EXISTS `django_content_type` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `app_label` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `model` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `django_content_type_app_label_model_76bd3d3b_uniq` (`app_label`,`model`)
) ENGINE=InnoDB AUTO_INCREMENT=2521 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Dumping data for table sf.django_content_type: ~32 rows (approximately)
/*!40000 ALTER TABLE `django_content_type` DISABLE KEYS */;
INSERT INTO `django_content_type` (`id`, `app_label`, `model`) VALUES
	(2489, 'admin', 'logentry'),
	(2495, 'app_cdn', 'distribution'),
	(2496, 'app_cdn', 'invalidation'),
	(2497, 'app_cms', 'cmscontentmeta'),
	(2498, 'app_cms', 'cmsmediafile'),
	(2501, 'app_know', 'batch'),
	(2500, 'app_know', 'insight'),
	(2499, 'app_know', 'knowledgepoint'),
	(2502, 'app_mailserver', 'mailaccount'),
	(2505, 'app_mailserver', 'mailattachment'),
	(2503, 'app_mailserver', 'mailbox'),
	(2504, 'app_mailserver', 'mailmessage'),
	(2506, 'app_notice', 'noticerecord'),
	(2507, 'app_notice', 'reg'),
	(2508, 'app_oss', 'metadata'),
	(2511, 'app_searchrec', 'searchrecdocterm'),
	(2510, 'app_searchrec', 'searchrecdocument'),
	(2512, 'app_searchrec', 'searchrecevent'),
	(2509, 'app_searchrec', 'searchrecreg'),
	(2513, 'app_snowflake', 'recounter'),
	(2514, 'app_snowflake', 'snowflakereg'),
	(2515, 'app_user', 'event'),
	(2516, 'app_user', 'token'),
	(2517, 'app_user', 'user'),
	(2518, 'app_verify', 'reg'),
	(2519, 'app_verify', 'verifycode'),
	(2520, 'app_verify', 'verifylog'),
	(2491, 'auth', 'group'),
	(2490, 'auth', 'permission'),
	(2492, 'auth', 'user'),
	(2493, 'contenttypes', 'contenttype'),
	(2494, 'sessions', 'session');
/*!40000 ALTER TABLE `django_content_type` ENABLE KEYS */;

-- Dumping structure for table sf.django_migrations
CREATE TABLE IF NOT EXISTS `django_migrations` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `app` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `applied` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=34 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Dumping data for table sf.django_migrations: ~18 rows (approximately)
/*!40000 ALTER TABLE `django_migrations` DISABLE KEYS */;
INSERT INTO `django_migrations` (`id`, `app`, `name`, `applied`) VALUES
	(1, 'contenttypes', '0001_initial', '2025-12-26 09:44:51.252366'),
	(2, 'auth', '0001_initial', '2025-12-26 09:44:51.692048'),
	(3, 'admin', '0001_initial', '2025-12-26 09:44:51.778492'),
	(4, 'admin', '0002_logentry_remove_auto_add', '2025-12-26 09:44:51.788767'),
	(5, 'admin', '0003_logentry_add_action_flag_choices', '2025-12-26 09:44:51.798511'),
	(6, 'contenttypes', '0002_remove_content_type_name', '2025-12-26 09:44:51.858613'),
	(7, 'auth', '0002_alter_permission_name_max_length', '2025-12-26 09:44:51.897263'),
	(8, 'auth', '0003_alter_user_email_max_length', '2025-12-26 09:44:51.918546'),
	(9, 'auth', '0004_alter_user_username_opts', '2025-12-26 09:44:51.930783'),
	(10, 'auth', '0005_alter_user_last_login_null', '2025-12-26 09:44:51.969746'),
	(11, 'auth', '0006_require_contenttypes_0002', '2025-12-26 09:44:51.975339'),
	(12, 'auth', '0007_alter_validators_add_error_messages', '2025-12-26 09:44:51.984506'),
	(13, 'auth', '0008_alter_user_username_max_length', '2025-12-26 09:44:52.018520'),
	(14, 'auth', '0009_alter_user_last_name_max_length', '2025-12-26 09:44:52.054825'),
	(15, 'auth', '0010_alter_group_name_max_length', '2025-12-26 09:44:52.073823'),
	(16, 'auth', '0011_update_proxy_permissions', '2025-12-26 09:44:52.085157'),
	(17, 'auth', '0012_alter_user_first_name_max_length', '2025-12-26 09:44:52.122421'),
	(18, 'sessions', '0001_initial', '2025-12-26 09:44:52.151519');
/*!40000 ALTER TABLE `django_migrations` ENABLE KEYS */;

-- Dumping structure for table sf.django_session
CREATE TABLE IF NOT EXISTS `django_session` (
  `session_key` varchar(40) COLLATE utf8mb4_unicode_ci NOT NULL,
  `session_data` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `expire_date` datetime(6) NOT NULL,
  PRIMARY KEY (`session_key`),
  KEY `django_session_expire_date_a5c62663` (`expire_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Dumping data for table sf.django_session: ~0 rows (approximately)
/*!40000 ALTER TABLE `django_session` DISABLE KEYS */;
/*!40000 ALTER TABLE `django_session` ENABLE KEYS */;


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

-- Dumping data for table sf_ai.ai_asset: ~0 rows (approximately)
/*!40000 ALTER TABLE `ai_asset` DISABLE KEYS */;
/*!40000 ALTER TABLE `ai_asset` ENABLE KEYS */;

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

-- Dumping data for table sf_ai.ai_idem: ~0 rows (approximately)
/*!40000 ALTER TABLE `ai_idem` DISABLE KEYS */;
/*!40000 ALTER TABLE `ai_idem` ENABLE KEYS */;

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

-- Dumping data for table sf_ai.ai_job: ~0 rows (approximately)
/*!40000 ALTER TABLE `ai_job` DISABLE KEYS */;
/*!40000 ALTER TABLE `ai_job` ENABLE KEYS */;

-- Dumping structure for table sf_ai.ai_model
CREATE TABLE IF NOT EXISTS `ai_model` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `provider_id` bigint(20) unsigned NOT NULL DEFAULT '0',
  `model_name` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `param_specs` varchar(1024) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `capability` tinyint(3) unsigned NOT NULL DEFAULT '0' COMMENT '0=chat,1=image,2=video',
  `status` tinyint(2) NOT NULL DEFAULT '0',
  `ct` bigint(20) unsigned NOT NULL DEFAULT '0',
  `ut` bigint(20) unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`) USING BTREE,
  KEY `idx_ai_model_provider` (`provider_id`,`status`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Dumping data for table sf_ai.ai_model: ~5 rows (approximately)
/*!40000 ALTER TABLE `ai_model` DISABLE KEYS */;
INSERT INTO `ai_model` (`id`, `provider_id`, `model_name`, `param_specs`, `capability`, `status`, `ct`, `ut`) VALUES
	(1, 1, 'gpt-5', '[{"n":"model","d":"","t":"STRING","r":{},"x":"model"},{"n":"messages","d":"","t":"OBJECT_ARRAY","r":{},"c":[{"n":"role","d":"","t":"STRING","r":{},"default":"user"},{"n":"content","d":"","t":"STRING","r":{},"x":"content"}]}]', 0, 1, 1774523992221, 1774803331385),
	(2, 4, 'text-embedding-3-small', '[{"n":"model","d":"","t":"STRING","r":{},"x":"model"},{"n":"input","d":"","t":"STRING","r":{},"x":"content"},{"n":"encoding_format","d":"","t":"ENUM","r":{"values":["float","base64"]},"x":"encoding_format","default":"float"},{"n":"dimensions","d":"","t":"INT","r":{},"x":"dimensions","default":"384"}]', 3, 1, 1774524008443, 1774940010048),
	(3, 2, 'kling-v1', '[{"n":"model","d":"","t":"STRING","r":{},"x":"model"},{"n":"prompt","d":"","t":"STRING","r":{},"x":"content"},{"n":"image","d":"","t":"STRING","r":{},"x":"image"},{"n":"duration","d":"","t":"INT","r":{},"x":"duration","default":"5"},{"n":"width","d":"","t":"INT","r":{},"x":"width","default":"360"},{"n":"height","d":"","t":"INT","r":{},"x":"height","default":"640"}]', 2, 1, 1774541885192, 1774948518363),
	(4, 3, 'gpt-image-1.5', '[{"n":"model","d":"","t":"STRING","r":{},"x":"model"},{"n":"prompt","d":"","t":"STRING","r":{},"x":"content"},{"n":"n","d":"","t":"INT","r":{},"x":"n","default":"1"},{"n":"size","d":"","t":"STRING","r":{},"x":"size","default":"1024x1024"}]', 1, 1, 1774755017816, 1774803482089);
/*!40000 ALTER TABLE `ai_model` ENABLE KEYS */;

-- Dumping structure for table sf_ai.ai_provider
CREATE TABLE IF NOT EXISTS `ai_provider` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `base_url` varchar(512) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `url_path` varchar(512) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `api_key` varchar(512) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `status` tinyint(2) NOT NULL DEFAULT '0',
  `ct` bigint(20) unsigned NOT NULL DEFAULT '0',
  `ut` bigint(20) unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Dumping data for table sf_ai.ai_provider: ~4 rows (approximately)
/*!40000 ALTER TABLE `ai_provider` DISABLE KEYS */;
INSERT INTO `ai_provider` (`id`, `name`, `base_url`, `url_path`, `api_key`, `status`, `ct`, `ut`) VALUES
	(1, 'OpenAI', 'api2.aigcbest.top', '/v1/chat/completions', 'sk-L62iXrTzCl46yfxkEO0j6nPJ0pjq8bF07WNtP3gymmMpY6dD', 1, 1774523927298, 1774523957059),
	(2, 'Kling-图生视频', 'api2.aigcbest.top', '/v1/video/generations', 'sk-L62iXrTzCl46yfxkEO0j6nPJ0pjq8bF07WNtP3gymmMpY6dD', 1, 1774541833521, 1774752709443),
	(3, 'OpenAI-文生图', 'api2.aigcbest.top', '/v1/images/generations', 'sk-L62iXrTzCl46yfxkEO0j6nPJ0pjq8bF07WNtP3gymmMpY6dD', 1, 1774752146310, 1774752146310),
	(4, 'OpenAI-文本嵌入', 'api2.aigcbest.top', '/v1/embeddings', 'sk-L62iXrTzCl46yfxkEO0j6nPJ0pjq8bF07WNtP3gymmMpY6dD', 1, 1774752807483, 1774752807483),
	(5, '查询视频', 'api2.aigcbest.top', '/v1/video/generations/:task_id', 'sk-L62iXrTzCl46yfxkEO0j6nPJ0pjq8bF07WNtP3gymmMpY6dD', 1, 1774948772712, 1774948772712);
/*!40000 ALTER TABLE `ai_provider` ENABLE KEYS */;

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
) ENGINE=InnoDB AUTO_INCREMENT=28 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='调用日志';

-- Dumping data for table sf_ai.call_log: ~15 rows (approximately)
/*!40000 ALTER TABLE `call_log` DISABLE KEYS */;
INSERT INTO `call_log` (`id`, `reg_id`, `template_id`, `provider_id`, `model_id`, `latency_ms`, `success`, `error_message`, `ct`) VALUES
	(11, 1, 7, 1, 1, 54549, 1, '', 1774936267055),
	(12, 1, 10, 4, 2, 2100, 1, '', 1774937677242),
	(13, 1, 10, 4, 2, 1466, 1, '', 1774937876994),
	(14, 1, 10, 4, 2, 951, 0, 'HTTP 500: Mismatch type int64 with value string "at index 78: mismatched type with value\\n\\n\\t, \\"dimensions\\": \\"384\\", \\"input\\": \\n\\t................^...............\\n" (request id: 20260331062631476586781lwncCzmN)', 1774938391497),
	(15, 1, 10, 4, 2, 1430, 1, '', 1774938683354),
	(16, 1, 10, 4, 2, 1851, 1, '', 1774939284226),
	(17, 1, 10, 4, 2, 1245, 0, 'empty embedding response', 1774940093974),
	(18, 1, 10, 4, 2, 472, 1, '', 1774940111613),
	(19, 1, 10, 3, 4, 6, 0, 'capability IMAGE is not supported for AigcBestAPI.invoke (CHAT, EMBEDDING only)', 1774940400089),
	(20, 1, 10, 3, 4, 56447, 1, '', 1774941369562),
	(21, 1, 10, 3, 4, 54633, 1, '', 1774943158460),
	(22, 1, 10, 2, 3, 1410, 0, 'HTTP 403: {"code":"pre_consume_token_quota_failed","message":"token quota is not enough, token remain quota: ＄0.822658, need quota: ＄1.000000","data":null}', 1774943742349),
	(23, 1, 10, 2, 3, 2591, 0, 'HTTP 400: {"code":"fail_to_fetch_task","message":"{\\"code\\":400,\\"message\\":\\"File is not in a valid base64 format (request id: 9e4dcd454e90ccd3-LAX)\\"}","data":null}', 1774943832832),
	(24, 1, 10, 2, 3, 2941, 0, 'HTTP 400: {"code":"fail_to_fetch_task","message":"{\\"code\\":400,\\"message\\":\\"duration value \'3\' is invalid (request id: 9e4e37d62cc63393-LAX)\\"}","data":null}', 1774948198487),
	(25, 1, 10, 2, 3, 22364, 0, 'HTTP 400: {"code":"fail_to_fetch_task","message":"{\\"code\\":400,\\"message\\":\\"duration value \'3\' is invalid (request id: 9e4e3a117ff53393-LAX)\\"}","data":null}', 1774948296698),
	(26, 1, 10, 2, 3, 18651, 1, '', 1774948433203),
	(27, 1, 10, 2, 3, 38226, 1, '', 1774953832179);
/*!40000 ALTER TABLE `call_log` ENABLE KEYS */;

-- Dumping structure for table sf_ai.prompt_tpl
CREATE TABLE IF NOT EXISTS `prompt_tpl` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `template_key` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `description` varchar(512) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `body` text COLLATE utf8mb4_unicode_ci,
  `param_specs` text COLLATE utf8mb4_unicode_ci COMMENT 'json',
  `resp_specs` text COLLATE utf8mb4_unicode_ci COMMENT 'json',
  `constraint_type` tinyint(3) unsigned NOT NULL DEFAULT '0' COMMENT '0=weak,1=strong',
  `status` tinyint(2) NOT NULL DEFAULT '0',
  `ct` bigint(20) unsigned NOT NULL DEFAULT '0',
  `ut` bigint(20) unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE KEY `uni_ai_tpl` (`template_key`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='提示词模版';

-- Dumping data for table sf_ai.prompt_tpl: ~8 rows (approximately)
/*!40000 ALTER TABLE `prompt_tpl` DISABLE KEYS */;
INSERT INTO `prompt_tpl` (`id`, `template_key`, `description`, `body`, `param_specs`, `resp_specs`, `constraint_type`, `status`, `ct`, `ut`) VALUES
	(1, '[DEBUG] single-choice', '', 'You are a {role}. Regarding the content enclosed by triple backticks, please answer the question:\r\nWhich of the following options is most appropriate for {question}:\r\n\r\n{options}\r\n\r\nOr, if you cannot find any appropriate one from the options, try to explain the reason.\r\n```\r\n{text}\r\n```\r\n\r\nNotes:\r\n1. Each option is prefixed by \'☐\', a symbol. This symbol should not appear in your answer.\r\n2. If you have selected one option, answer the option itself — no need to say more words.', '[{"name":"role"},{"name":"question"},{"name":"options"},{"name":"text"}]', '[]', 0, 1, 1774542134558, 1774690664028),
	(2, '[RELEASE] single-choice', '', 'You are a {role}. Regarding the content enclosed by triple backticks, please answer the question:\r\nWhich of the following options is most appropriate for {question}:\r\n\r\n{options}\r\n\r\nOr, if any new, appropriate option has not been mentioned above, what is it?\r\nIf you believe the answer is not in the options and cannot provide a more appropriate option, please answer \'no\'.\r\n```\r\n{text}\r\n```\r\n\r\nNotes:\r\n1. Each option is prefixed by \'☐\', a symbol. This symbol should not appear in your answer.\r\n2. If you have selected one option, answer the option itself — no need to say more words.', '[{"name":"role"},{"name":"question"},{"name":"options"},{"name":"text"}]', '[]', 0, 1, 1774542222683, 1774690672084),
	(3, '[DEBUG] multiple-choice', '', 'You are a {role}. Regarding the content enclosed by triple backticks, please answer the question:\r\nWhich of the following options are appropriate for {question}:\r\n\r\n{options}\r\n\r\nOr, if you cannot find any appropriate ones from the options, try to explain the reasons.\r\n```\r\n{text}\r\n```\r\n\r\nNotes:\r\n1. Each option is prefixed by \'☐\', a symbol. This symbol should not appear in your answer.\r\n2. If you have selected some options, answer the options themselves, join them with comma — no need to say more words.', '[{"name":"role"},{"name":"question"},{"name":"options"},{"name":"text"}]', '[]', 0, 1, 1774542460804, 1774689658901),
	(4, '[RELEASE] multiple-choice', '', 'You are a {role}. Regarding the content enclosed by triple backticks, please answer the question:\r\nWhich of the following options are appropriate for {question}:\r\n\r\n{options}\r\n\r\nOr, if any new, appropriate options have not been mentioned above, what are they?\r\nIf you believe the answer is not in the options and cannot provide some more appropriate options, please answer \'no\'.\r\n```\r\n{text}\r\n```\r\n\r\nNotes:\r\n1. Each option is prefixed by \'☐\', a symbol. This symbol should not appear in your answer.\r\n2. If you have selected some options, answer the options themselves, join them with comma — no need to say more words.', '[{"name":"role"},{"name":"question"},{"name":"options"},{"name":"text"}]', '[]', 0, 1, 1774542502038, 1774690563240),
	(5, '[DEBUG] true-or-false', '', 'You are a {role}. Regarding the content enclosed by triple backticks, please answer the question:\r\nIs it true or false, that {assertion}?\r\n\r\nOr, if you are not sure it is true or false, try to explain the reason.\r\n\r\n```\r\n{text}\r\n```\r\n\r\nNotes:\r\n1. Just answer \'true\' or \'false\'. No need to say more words.', '[{"name":"role"},{"name":"assertion"},{"name":"text"}]', '[]', 0, 1, 1774542824046, 1774690510230),
	(6, '[RELEASE] true-or-false', '', 'You are a {role}. Regarding the content enclosed by triple backticks, please answer the question:\r\nIs it true or false, that {assertion}?\r\n\r\nIf you are not sure it is true or false, please answer \'no\'.\r\n\r\n```\r\n{text}\r\n```\r\n\r\nNotes:\r\n1. Just answer \'true\' or \'false\'. No need to say more words.', '[{"name":"role"},{"name":"assertion"},{"name":"text"}]', '[]', 0, 1, 1774542922521, 1774690656905),
	(7, '[DEBUG] ask-and-answer', '', 'You are a {role}. Regarding the content enclosed by triple backticks, please answer:\r\n\r\n{question}\r\n\r\nOr, if you do not know how to answer, try to explain the reason.\r\n\r\n```\r\n{text}\r\n```', '[{"name":"role"},{"name":"question"},{"name":"text"}]', '[]', 0, 1, 1774543778707, 1774685866657),
	(8, '[RELEASE] ask-and-answer', '', 'You are a {role}. Regarding the content enclosed by triple backticks, please answer:\r\n\r\n{question}\r\n\r\nIf you do not know how to answer, please answer \'no\'.\r\n\r\n```\r\n{text}\r\n```', '[{"name":"role"},{"name":"question"},{"name":"text"}]', '[]', 0, 1, 1774543797364, 1774690537947),
	(10, 'passthrough', '', '{text}', '[{"name":"text"}]', '[]', 0, 1, 1774716038806, 1774716038806);
/*!40000 ALTER TABLE `prompt_tpl` ENABLE KEYS */;

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
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Dumping data for table sf_ai.reg: ~2 rows (approximately)
/*!40000 ALTER TABLE `reg` DISABLE KEYS */;
INSERT INTO `reg` (`id`, `name`, `access_key`, `callback_secret`, `status`, `ct`, `ut`) VALUES
	(1, '测试', '3b6bf135486d4759840f4fe20becded3', 'bd96f8fc50fd48de8a3f30b3337a1bbbdceb16f77dea465e82a95b7a0ab42d3a', 1, 1774696263857, 1774696263857),
	(2, '知识中心', '229233ceec1846419d860a8b7f74c018', '08cfb9310b094f2a956e0965071d1686509c792b5c1044b093433069e8dcd807', 1, 1774488218043, 1774488218043);
/*!40000 ALTER TABLE `reg` ENABLE KEYS */;


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

-- Dumping data for table sf_cdn.d: ~1 rows (approximately)
/*!40000 ALTER TABLE `d` DISABLE KEYS */;
INSERT INTO `d` (`id`, `arn`, `status`, `domain_name`, `origin_config`, `aliases`, `enabled`, `comment`, `etag`, `ct`, `ut`) VALUES
	(1, '', 1, 'localhost:8000', '{"Origins": {"Items": [{"Id": "default", "DomainName": "localhost:8000", "OriginPath": "/api/oss", "CustomOriginConfig": {"HTTPPort": 80, "HTTPSPort": 443, "OriginProtocolPolicy": "http-only"}}], "Quantity": 1}, "OriginBucket": "mall", "DefaultCacheBehavior": {"TargetOriginId": "default"}, "Comment": "mall", "Enabled": true}', '[]', 1, 'mall', '52caeec75c8b4575b395b3887d30ad40', 1774254530983, 1775643333198);
/*!40000 ALTER TABLE `d` ENABLE KEYS */;

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

-- Dumping data for table sf_cdn.invalid: ~0 rows (approximately)
/*!40000 ALTER TABLE `invalid` DISABLE KEYS */;
/*!40000 ALTER TABLE `invalid` ENABLE KEYS */;


-- Dumping database structure for sf_cms
CREATE DATABASE IF NOT EXISTS `sf_cms` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci */;
USE `sf_cms`;

-- Dumping structure for table sf_cms.content_meta
CREATE TABLE IF NOT EXISTS `content_meta` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'Logical key; must match config cms.models',
  `fields` text COLLATE utf8mb4_unicode_ci COMMENT 'fields definition, encoded in json',
  `Column 4` text COLLATE utf8mb4_unicode_ci,
  `ct` bigint(20) unsigned NOT NULL DEFAULT '0' COMMENT 'Create time in Unix milliseconds',
  `ut` bigint(20) unsigned NOT NULL DEFAULT '0' COMMENT 'Update time in Unix milliseconds',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uni_cms_content_meta_name` (`name`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Content type registry';

-- Dumping data for table sf_cms.content_meta: ~1 rows (approximately)
/*!40000 ALTER TABLE `content_meta` DISABLE KEYS */;
INSERT INTO `content_meta` (`id`, `name`, `fields`, `Column 4`, `ct`, `ut`) VALUES
	(5, 'product', '{"schema_version": 1, "columns": [{"name": "title", "physical": "varchar(512)", "nullable": false, "index": "none", "comment": "\\u6807\\u9898", "validation": {"type": "string", "required": true}, "default": ""}, {"name": "description", "physical": "text", "nullable": true, "index": "none", "comment": "\\u63cf\\u8ff0", "validation": {"type": "string"}}, {"name": "thumbnail", "physical": "varchar(512)", "nullable": false, "index": "none", "comment": "\\u7f29\\u7565\\u56fe", "validation": {"type": "string"}, "default": ""}, {"name": "main_media", "physical": "varchar(512)", "nullable": false, "index": "none", "comment": "\\u4e3b\\u56fe", "validation": {"type": "string"}, "default": ""}, {"name": "ext_media", "physical": "varchar(512)", "nullable": false, "index": "none", "comment": "\\u6269\\u5c55\\u56fe", "validation": {"type": "string"}, "default": ""}], "indexes": []}', NULL, 1775541127748, 1775565571776);
/*!40000 ALTER TABLE `content_meta` ENABLE KEYS */;

-- Dumping structure for table sf_cms.c_product
CREATE TABLE IF NOT EXISTS `c_product` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `title` varchar(512) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT '标题',
  `description` text COLLATE utf8mb4_unicode_ci COMMENT '描述',
  `thumbnail` varchar(512) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT '缩略图',
  `main_media` varchar(512) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT '主图',
  `ext_media` varchar(512) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT '扩展图',
  `ct` bigint(20) unsigned NOT NULL DEFAULT '0' COMMENT 'Create time in Unix milliseconds',
  `ut` bigint(20) unsigned NOT NULL DEFAULT '0' COMMENT 'Update time in Unix milliseconds',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Dumping data for table sf_cms.c_product: ~1 rows (approximately)
/*!40000 ALTER TABLE `c_product` DISABLE KEYS */;
INSERT INTO `c_product` (`id`, `title`, `description`, `thumbnail`, `main_media`, `ext_media`, `ct`, `ut`) VALUES
	(1, '蝌蚪啃蜡', '居家旅行，必备良药', 'products/6e54ed40-8426-4343-ade0-21b80277375c.png', 'products/f2202e04-efd7-4657-a7f2-6634e53e385d.png,products/c1d475db-9dce-48df-b82d-c5195066839a.png', 'products/e05c60da-9cff-4f53-bd41-e7c506b42f6c.jpg', 1775642179706, 1775840389939);
/*!40000 ALTER TABLE `c_product` ENABLE KEYS */;

-- Dumping structure for table sf_cms.media_file
CREATE TABLE IF NOT EXISTS `media_file` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `original_name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'Original file name',
  `mime_type` tinyint(3) unsigned NOT NULL DEFAULT '0' COMMENT 'MIME enum code (see MediaFile::MIME_*)',
  `size_bytes` bigint(20) unsigned NOT NULL DEFAULT '0' COMMENT 'File size in bytes',
  `raw_path` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'Object storage source key',
  `transcoded_path` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'Transcoded object key',
  `cdn_url` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'Public CDN URL when ready',
  `status` tinyint(3) unsigned NOT NULL DEFAULT '0' COMMENT '0-init,1-uploaded,2-transcoding,3-ready,4-failed',
  `error_message` text COLLATE utf8mb4_unicode_ci COMMENT 'Error detail when processing failed',
  `ct` bigint(20) unsigned NOT NULL COMMENT 'Create time (Unix ms)',
  `ut` bigint(20) unsigned NOT NULL COMMENT 'Update time (Unix ms)',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='File metadata and processing status';

-- Dumping data for table sf_cms.media_file: ~0 rows (approximately)
/*!40000 ALTER TABLE `media_file` DISABLE KEYS */;
/*!40000 ALTER TABLE `media_file` ENABLE KEYS */;


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

-- Dumping data for table sf_know.batch: ~2 rows (approximately)
/*!40000 ALTER TABLE `batch` DISABLE KEYS */;
INSERT INTO `batch` (`id`, `source_type`, `content`, `ct`, `ut`) VALUES
	(71, 0, '20世纪初，科学给美国带来了第二次革命。一个马背上的国家很快就被内燃机、载人飞行和其他众多发明所改变，普通人的生活很快也因为这些技术创新发生了变化。但与此同时，一群高深莫测的科学家正在缔造一场更加深刻的变革，全世界的理论物理学家开始改变我们对空间和时间的理解。1896年，法国物理学家亨利·贝克勒尔发现了放射现象；马克斯·普朗克、玛丽·居里和皮埃尔·居里等人进一步深化了我们对原子性质的认识；1905年，爱因斯坦发表了他的狭义相对论。突然之间，宇宙的面貌似乎也就此改变。', 1773555891763, 1773555891763),
	(72, 0, '宇文泰初掌軍隊不久便與諸將「刑牲盟誓，同獎王室」，遇大事必定上表朝廷，表中言詞恭順，更高舉「君臣大義」的旗幟討伐侯莫陳悅，往後又 「請奉迎輿駕」，無疑給王思政等人很好的印象。加上關中「有崤函之固」104 又「金城千里，天下之強國也。」荊州則是「危亡是懼」，投奔宇文泰以對抗高歡也是理所應然。', 1773560603025, 1773565209114);
/*!40000 ALTER TABLE `batch` ENABLE KEYS */;

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

-- Dumping data for table sf_know.insight: ~0 rows (approximately)
/*!40000 ALTER TABLE `insight` DISABLE KEYS */;
/*!40000 ALTER TABLE `insight` ENABLE KEYS */;

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

-- Dumping data for table sf_know.knowledge: ~8 rows (approximately)
/*!40000 ALTER TABLE `knowledge` DISABLE KEYS */;
INSERT INTO `knowledge` (`id`, `batch_id`, `content`, `seq`, `classification`, `stage`, `status`, `brief`, `g_brief`, `g_brief_hash`, `g_sub`, `g_sub_hash`, `v_sub_deco_id`, `g_obj`, `g_obj_hash`, `v_obj_deco_id`, `ct`, `ut`) VALUES
	(70, 71, '20世纪初，科学给美国带来了第二次革命。', 0, 0, 2, 1, '20世纪初，科学给美国带来第二次革命。', '(s:svo_core {name: \'科学\'})-[r:`导致`]-(o:svo_core {name: \'产业革命\'})', 2754810200, '(attr:svo_attr {name: \'20世纪初\'})-[:ATTR]->(c:svo_core {name: \'科学\'})', 1499148668, '69b7a085a2215d715d05037c', '(attr:svo_attr {name: \'美国\'})-[:ATTR]->(c:svo_core {name: \'产业革命\'})', 3598435587, '69b7a086a2215d715d05037d', 1773558706981, 1773677348989),
	(71, 71, '一个马背上的国家很快就被内燃机、载人飞行和其他众多发明所改变，普通人的生活很快也因为这些技术创新发生了变化。', 1, 1, 0, 0, '', '', 0, '', 0, '', '', 0, '', 1773558706983, 1773558706983),
	(72, 71, '但与此同时，一群高深莫测的科学家正在缔造一场更加深刻的变革，全世界的理论物理学家开始改变我们对空间和时间的理解。', 2, 0, 0, 0, '', '', 0, '', 0, '', '', 0, '', 1773558706984, 1773558706984),
	(73, 71, '1896年，法国物理学家亨利·贝克勒尔发现了放射现象；马克斯·普朗克、玛丽·居里和皮埃尔·居里等人进一步深化了我们对原子性质的认识；1905年，爱因斯坦发表了他的狭义相对论。', 3, 2, 0, 0, '', '', 0, '', 0, '', '', 0, '', 1773558706986, 1773558706986),
	(74, 71, '突然之间，宇宙的面貌似乎也就此改变。', 4, 2, 0, 0, '', '', 0, '', 0, '', '', 0, '', 1773558706987, 1773558706987),
	(75, 72, '宇文泰初掌軍隊不久便與諸將「刑牲盟誓，同獎王室」，遇大事必定上表朝廷，表中言詞恭順，更高舉「君臣大義」的旗幟討伐侯莫陳悅，往後又 「請奉迎輿駕」，無疑給王思政等人很好的印象。', 0, 2, 0, 0, '', '', 0, '', 0, '', '', 0, '', 1773560627580, 1773560627580),
	(76, 72, '加上關中「有崤函之固」104 又「金城千里，天下之強國也。', 1, 5, 0, 0, '', '', 0, '', 0, '', '', 0, '', 1773560627582, 1773560627582),
	(77, 72, '」荊州則是「危亡是懼」，投奔宇文泰以對抗高歡也是理所應然。', 2, 5, 0, 0, '', '', 0, '', 0, '', '', 0, '', 1773560627583, 1773560627583);
/*!40000 ALTER TABLE `knowledge` ENABLE KEYS */;

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

-- Dumping data for table sf_know.knowledge_bkp: ~9 rows (approximately)
/*!40000 ALTER TABLE `knowledge_bkp` DISABLE KEYS */;
INSERT INTO `knowledge_bkp` (`id`, `title`, `description`, `content`, `source_type`, `ct`, `ut`) VALUES
	(48, 'id generator', 'openapi: 3.0.3\ninfo:\n  title: ID Generator Service\n  description: Distributed ID generation service API\n  version: 1.0.0\n\nservers:\n  - url: https://api.example.com\n    description: Production Server\n  - url: http://localhost:8080\n    description: Local Development\n\ntags:\n  - name: ID Generator\n    description: ID generation APIs\n\npaths:\n  /api/v1/ids:\n    post:\n      tags:\n        - ID Generator\n      summary: Generate IDs\n      description: Generate one or more distributed unique IDs\n      requestBody:\n        required: true\n        content:\n          application/json:\n            schema:\n              $ref: \'#/components/schemas/IdGenerateRequest\'\n      responses:\n        \'200\':\n          description: Success\n          content:\n            application/json:\n              schema:\n                $ref: \'#/components/schemas/IdGenerateResponse\'\n        \'400\':\n          description: Bad Request\n        \'500\':\n          description: Internal Server Error\n\ncomponents:\n  schemas:\n\n    IdGenerateRequest:\n      type: object\n      required:\n        - bizKey\n      properties:\n        bizKey:\n          type: string\n          description: Business key (e.g. order, user, payment)\n          example: order\n        count:\n          type: integer\n          description: Number of IDs to generate (default 1, max 1000)\n          minimum: 1\n          maximum: 1000\n          default: 1\n        idType:\n          type: string\n          description: ID type\n          enum: [LONG, STRING]\n          default: LONG\n\n    IdGenerateResponse:\n      type: object\n      properties:\n        code:\n          type: integer\n          example: 0\n        message:\n          type: string\n          example: success\n        data:\n          $ref: \'#/components/schemas/IdGenerateData\'\n\n    IdGenerateData:\n      type: object\n      properties:\n        bizKey:\n          type: string\n          example: order\n        ids:\n          type: array\n          items:\n            oneOf:\n              - type: integer\n                format: int64\n              - type: string\n          example:\n            - 18273918273918273\n            - 18273918273918274', 'app_snowflake 服务可以生成唯一ID。', 'serv-found', 1771783883827, 1771905119622),
	(49, 'backend-dev', '{\n  "invocation": {\n    "type": "bro_submit",\n    "task_file": "workers/backend-dev.json",\n    "workspace": "docker/workspace",\n    "source": "{src_path}",\n    "local": true\n  },\n  "executors": {\n    "backend": {\n      "mode": "agent",\n      "method": "local"\n    },\n    "docker-agent": {\n      "mode": "agent",\n      "method": "docker"\n    }\n  },\n  "match_rules": {\n    "scope_patterns": [\n      "src/backend",\n      "src/api",\n      "server",\n      "backend"\n    ],\n    "keywords": [\n      "api",\n      "endpoint",\n      "database",\n      "auth",\n      "server",\n      "fastapi",\n      "flask",\n      "django",\n      "sqlalchemy",\n      "orm"\n    ]\n  }\n}', '后端开发：Python/FastAPI API 开发、数据库操作、服务端逻辑', 'mimi-bro', 1771905098638, 1772332660876),
	(50, 'frontend-dev', '{\n  "invocation": {\n    "type": "bro_submit",\n    "task_file": "workers/frontend-dev.json",\n    "workspace": "docker/workspace",\n    "source": "{src_path}",\n    "local": true\n  },\n  "executors": {\n    "backend": {\n      "mode": "agent",\n      "method": "local"\n    }\n  },\n  "match_rules": {\n    "scope_patterns": [\n      "src/frontend",\n      "src/web",\n      "apps/web",\n      "frontend",\n      "client"\n    ],\n    "keywords": [\n      "ui",\n      "component",\n      "page",\n      "form",\n      "react",\n      "vue",\n      "css",\n      "style",\n      "button",\n      "modal",\n      "layout"\n    ]\n  }\n}', '前端开发：React/TypeScript UI 组件、页面、交互逻辑', 'mimi-bro', 1771905544842, 1772332661998),
	(51, 'frontend-analysis', '{"executors":{"backend":{"mode":"agent","method":"local"}}}', 'frontend-analysis 是一个 agent，专注于前端需求分析。', 'mimi-bro', 1771906650567, 1771906676313),
	(52, 'code-review', '{"executors":{"reviewer":{"mode":"agent","method":"local"}}}', 'code-review 是一个 agent，专注于程序代码审查。', 'mimi-bro', 1771910259288, 1771910259288),
	(53, 'frontend-run-linter', '{"invocation":{"type":"shell","template":"npm run lint -- {src_path}"},"executors":{}}', 'frontend-run-linter 是一个 agent，专注于检查程序代码的语法错误、安全漏洞。', 'mimi-bro', 1771910605362, 1771910605362),
	(54, 'call-remote', '{"invocation":{"type":"http","method":"POST","url":"https://api.example.com/run","body":{"skill":"{skill_id}","params":"{params_json}"}},"executors":{}}', 'call-remote 是一个 agent，致力于执行远程接口调用。', 'mimi-bro', 1771911026993, 1771911026993),
	(55, 'test-worker', '{\n  "match_rules": {\n    "scope_patterns": [\n      "tests",\n      "test",\n      "spec",\n      "__tests__"\n    ],\n    "keywords": [\n      "test",\n      "spec",\n      "assert",\n      "expect",\n      "mock",\n      "fixture",\n      "pytest",\n      "jest",\n      "unittest"\n    ]\n  },\n  "invocation": {\n    "type": "bro_submit",\n    "task_file": "workers/test-worker.json",\n    "workspace": "docker/workspace",\n    "source": "{src_path}",\n    "local": true\n  },\n  "executors": {\n    "tester": {\n      "mode": "agent",\n      "method": "local"\n    }\n  }\n}', '测试开发：单元测试、集成测试、E2E 测试编写', 'mimi-bro', 1772332663046, 1772344438563),
	(57, 'test-git-committer', '{\n  "match_rules": {\n    "keywords": [\n      "git",\n      "commit"\n    ]\n  },\n  "invocation": {\n    "type": "bro_submit",\n    "task_file": "workers/test-git-committer.json",\n    "local": true,\n    "source": "{src_path}"\n  },\n  "executors": {\n    "cursor-agent": {\n      "mode": "agent"\n    }\n  }\n}', 'Execute exact file operations for git testing. Creates/modifies files as specified in requirement, then commits.', 'mimi-bro', 1772344438536, 1772442716509);
/*!40000 ALTER TABLE `knowledge_bkp` ENABLE KEYS */;


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

-- Dumping data for table sf_mailserver.mailbox: ~0 rows (approximately)
/*!40000 ALTER TABLE `mailbox` DISABLE KEYS */;
/*!40000 ALTER TABLE `mailbox` ENABLE KEYS */;

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

-- Dumping data for table sf_mailserver.mail_account: ~0 rows (approximately)
/*!40000 ALTER TABLE `mail_account` DISABLE KEYS */;
/*!40000 ALTER TABLE `mail_account` ENABLE KEYS */;

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

-- Dumping data for table sf_mailserver.mail_attachment: ~0 rows (approximately)
/*!40000 ALTER TABLE `mail_attachment` DISABLE KEYS */;
/*!40000 ALTER TABLE `mail_attachment` ENABLE KEYS */;

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

-- Dumping data for table sf_mailserver.mail_message: ~0 rows (approximately)
/*!40000 ALTER TABLE `mail_message` DISABLE KEYS */;
/*!40000 ALTER TABLE `mail_message` ENABLE KEYS */;


-- Dumping database structure for sf_notice
CREATE DATABASE IF NOT EXISTS `sf_notice` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci */;
USE `sf_notice`;

-- Dumping structure for table sf_notice.notice
CREATE TABLE IF NOT EXISTS `notice` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `reg_id` bigint(20) unsigned NOT NULL DEFAULT '0' COMMENT '注册ID',
  `event_id` bigint(20) unsigned NOT NULL DEFAULT '0' COMMENT '事件ID',
  `channel` tinyint(3) unsigned NOT NULL DEFAULT '0',
  `broker` tinyint(3) unsigned NOT NULL DEFAULT '0',
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
) ENGINE=InnoDB AUTO_INCREMENT=18 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='通知记录';

-- Dumping data for table sf_notice.notice: ~16 rows (approximately)
/*!40000 ALTER TABLE `notice` DISABLE KEYS */;
INSERT INTO `notice` (`id`, `reg_id`, `event_id`, `channel`, `broker`, `target`, `subject`, `content`, `status`, `provider`, `message`, `ct`, `ut`) VALUES
	(2, 1, 2, 0, 1, 'string', 'Register verify code', 'Your register verify code is 864783. Event ID: 2', 0, '', '[Errno 111] Connection refused', 1775119302699, 1775119302819),
	(3, 1, 3, 0, 1, 'test@example.com', 'Password reset verify code', 'Your password reset code is 466228. Event ID: 3', 0, '', '[Errno 111] Connection refused', 1775124541280, 1775124541306),
	(4, 1, 4, 0, 0, 'test@example.com', 'Password reset verify code', 'Your password reset code is 977368. Event ID: 4', 0, '', '[Errno 111] Connection refused', 1775129139557, 1775129139570),
	(5, 1, 5, 0, 0, 'test@example.com', 'Register verify code', 'Your register verify code is 121636. Event ID: 5', 0, '', '[Errno 111] Connection refused', 1775300302964, 1775300303061),
	(6, 1, 6, 0, 0, 'test@example.com', 'Register verify code', 'Your register verify code is 111531. Event ID: 6', 0, '', '[Errno 111] Connection refused', 1775302108666, 1775302108676),
	(7, 1, 7, 0, 0, 'test@example.com', 'Register verify code', 'Your register verify code is 299632. Event ID: 7', 0, '', '[Errno 111] Connection refused', 1775302530056, 1775302530062),
	(8, 1, 8, 0, 0, 'test@example.com', 'Register verify code', 'Your register verify code is 762764. Event ID: 8', 0, '', '[Errno 111] Connection refused', 1775303127276, 1775303127284),
	(9, 1, 9, 0, 0, 'test@example.com', 'Register verify code', 'Your register verify code is 548688. Event ID: 9', 0, '', '[Errno 111] Connection refused', 1775303154250, 1775303154256),
	(10, 1, 10, 0, 0, 'test@example.com', 'Register verify code', 'Your register verify code is 417042. Event ID: 10', 0, '', '[Errno 111] Connection refused', 1775308259426, 1775308259441),
	(11, 1, 11, 0, 0, 'test@example.com', 'Register verify code', 'Your register verify code is 960880. Event ID: 11', 0, '', '[Errno 111] Connection refused', 1775361570644, 1775361570658),
	(12, 1, 12, 0, 0, 'test@example.com', 'Register verify code', 'Your register verify code is 240168. Event ID: 12', 0, '', '[Errno 111] Connection refused', 1775361734429, 1775361734435),
	(13, 1, 13, 0, 0, 'test@example.com', 'Password reset verify code', 'Your password reset code is 089807. Event ID: 13', 0, '', '[Errno 111] Connection refused', 1775362761175, 1775362761181),
	(14, 1, 14, 0, 0, 'test@example.com', 'Password reset verify code', 'Your password reset code is 589287. Event ID: 14', 0, '', '[Errno 111] Connection refused', 1775364599448, 1775364599464),
	(15, 1, 1, 10, 1, '员工福利', '什么东西', '电力成本有优势', 1, 'broker_jiang', 'ok', 1775413773367, 1775413775122),
	(16, 1, 1, 10, 1, '', '冒烟测试', '**能收到吗？**\r\n\r\n```\r\nprint \'hello world!\';\r\n```', 1, 'broker_jiang', 'ok', 1775450554059, 1775453846828),
	(17, 1, 1, 10, 1, '', '再试一下', '# 哈哈哈哈\r\n\r\n## 八千八千', 1, 'broker_jiang', 'ok', 1775450765733, 1775450767087);
/*!40000 ALTER TABLE `notice` ENABLE KEYS */;

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

-- Dumping data for table sf_notice.reg: ~1 rows (approximately)
/*!40000 ALTER TABLE `reg` DISABLE KEYS */;
INSERT INTO `reg` (`id`, `name`, `access_key`, `status`, `ct`, `ut`) VALUES
	(1, '用户中心', '745d29a0251e4f6cb3533125dd5684e9', 1, 1774414360621, 1774418580302);
/*!40000 ALTER TABLE `reg` ENABLE KEYS */;


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
) ENGINE=InnoDB AUTO_INCREMENT=47 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='OSS object metadata table';

-- Dumping data for table sf_oss.m: ~12 rows (approximately)
/*!40000 ALTER TABLE `m` DISABLE KEYS */;
INSERT INTO `m` (`id`, `bucket_name`, `object_key`, `content_type`, `content_length`, `etag`, `size`, `metadata`, `ut`) VALUES
	(33, 'user', 'avatar/20260326/e1c10f744d8a45d0b4f90c769d1a3707.jpg', 10, 132890, '6695f07609db5c6912b4620cbc907704', 132890, '', 1774520533484),
	(35, 'ai', 'aibroker/mm/98bfaf7ed2644bf1b3e26941172abb44_football.png', 11, 2408055, 'ce7685fdcb9102f10a43a07316ab9787', 2408055, '', 1774947489602),
	(36, 'ai', 'aibroker/mm/0eda86fcec98425a93a5055367d5d78b_football.png', 11, 2408055, 'ce7685fdcb9102f10a43a07316ab9787', 2408055, '', 1774948256010),
	(37, 'ai', 'aibroker/mm/5be2339b26fa41a98ad758a9ad7f214a_football.png', 11, 2408055, 'ce7685fdcb9102f10a43a07316ab9787', 2408055, '', 1774953789087),
	(39, 'mall', 'products/6e54ed40-8426-4343-ade0-21b80277375c.png', 11, 2453504, 'c7653d5b699b453082531ce34cf48e10', 2453504, '', 1775642027186),
	(40, 'mall', 'products/f2202e04-efd7-4657-a7f2-6634e53e385d.png', 11, 2408055, 'ce7685fdcb9102f10a43a07316ab9787', 2408055, '', 1775642064237),
	(41, 'mall', 'products/e05c60da-9cff-4f53-bd41-e7c506b42f6c.jpg', 10, 132890, '6695f07609db5c6912b4620cbc907704', 132890, '', 1775642073366),
	(42, 'mall', 'products/c1d475db-9dce-48df-b82d-c5195066839a.png', 11, 793506, 'af3cda6df903116c3749cfe108685fe9', 793506, '', 1775642873485),
	(43, 'cdn-cache', '1/products/6e54ed40-8426-4343-ade0-21b80277375c.png', 11, 2453504, 'c7653d5b699b453082531ce34cf48e10', 2453504, '', 1775647516526),
	(44, 'cdn-cache', '1/products/e05c60da-9cff-4f53-bd41-e7c506b42f6c.jpg', 10, 132890, '6695f07609db5c6912b4620cbc907704', 132890, '', 1775648774906),
	(45, 'cdn-cache', '1/products/c1d475db-9dce-48df-b82d-c5195066839a.png', 11, 793506, 'af3cda6df903116c3749cfe108685fe9', 793506, '', 1775648774926),
	(46, 'cdn-cache', '1/products/f2202e04-efd7-4657-a7f2-6634e53e385d.png', 11, 2408055, 'ce7685fdcb9102f10a43a07316ab9787', 2408055, '', 1775648774941);
/*!40000 ALTER TABLE `m` ENABLE KEYS */;


-- Dumping database structure for sf_searchrec
CREATE DATABASE IF NOT EXISTS `sf_searchrec` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci */;
USE `sf_searchrec`;

-- Dumping structure for table sf_searchrec.doc
CREATE TABLE IF NOT EXISTS `doc` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `rid` bigint(20) unsigned NOT NULL DEFAULT '0' COMMENT 'reg ID',
  `doc_key` varchar(191) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '0' COMMENT 'API document ID',
  `title` varchar(512) COLLATE utf8mb4_unicode_ci NOT NULL,
  `content` text COLLATE utf8mb4_unicode_ci,
  `tags` text COLLATE utf8mb4_unicode_ci COMMENT '逗号分隔',
  `lexical_norm_sq` bigint(20) NOT NULL DEFAULT '0' COMMENT 'sum(tf^2) for lexical cosine',
  `score_boost` decimal(4,2) NOT NULL DEFAULT '1.00',
  `popularity_score` decimal(5,4) unsigned NOT NULL DEFAULT '0.0000' COMMENT '热度（归一化）',
  `freshness_score` decimal(5,4) unsigned NOT NULL DEFAULT '0.0000' COMMENT '新鲜度（归一化）',
  `ct` bigint(20) unsigned NOT NULL DEFAULT '0' COMMENT 'Create time in Unix milliseconds',
  `ut` bigint(20) unsigned NOT NULL DEFAULT '0' COMMENT 'Update time in Unix milliseconds',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uni_search_doc_doc` (`rid`,`doc_key`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Dumping data for table sf_searchrec.doc: ~1 rows (approximately)
/*!40000 ALTER TABLE `doc` DISABLE KEYS */;
INSERT INTO `doc` (`id`, `rid`, `doc_key`, `title`, `content`, `tags`, `lexical_norm_sq`, `score_boost`, `popularity_score`, `freshness_score`, `ct`, `ut`) VALUES
	(1, 10000001, '1', '蝌蚪啃蜡', '居家旅行，必备良药', '', 3, 1.00, 0.0000, 0.0000, 1775840389973, 1775840389973);
/*!40000 ALTER TABLE `doc` ENABLE KEYS */;

-- Dumping structure for table sf_searchrec.doc_term
CREATE TABLE IF NOT EXISTS `doc_term` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `rid` bigint(20) unsigned NOT NULL DEFAULT '0' COMMENT 'reg ID',
  `doc_key` varchar(191) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `term` varchar(191) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `tf` int(10) unsigned NOT NULL DEFAULT '0' COMMENT '词频',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE KEY `uni_search_doc_term` (`rid`,`doc_key`,`term`) USING BTREE,
  KEY `idx_search_doc_term_term` (`term`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Dumping data for table sf_searchrec.doc_term: ~3 rows (approximately)
/*!40000 ALTER TABLE `doc_term` DISABLE KEYS */;
INSERT INTO `doc_term` (`id`, `rid`, `doc_key`, `term`, `tf`) VALUES
	(1, 10000001, '1', '蝌蚪啃蜡', 1),
	(2, 10000001, '1', '居家旅行', 1),
	(3, 10000001, '1', '必备良药', 1);
/*!40000 ALTER TABLE `doc_term` ENABLE KEYS */;

-- Dumping structure for table sf_searchrec.event
CREATE TABLE IF NOT EXISTS `event` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `rid` bigint(20) unsigned NOT NULL DEFAULT '0' COMMENT 'reg ID',
  `event_type` tinyint(3) unsigned NOT NULL DEFAULT '0' COMMENT '0-UNKNOWN, 1-SEARCH_QUERY, 2-IMPRESSION, 3-CLICK, 4-UPSERT',
  `payload` text COLLATE utf8mb4_unicode_ci,
  `uid` bigint(20) NOT NULL DEFAULT '0' COMMENT 'user ID',
  `did` varchar(191) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT 'device ID',
  `ct` bigint(20) unsigned NOT NULL DEFAULT '0' COMMENT 'Create time in Unix milliseconds',
  PRIMARY KEY (`id`),
  KEY `idx_search_event_type` (`rid`,`event_type`,`ct`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Dumping data for table sf_searchrec.event: ~0 rows (approximately)
/*!40000 ALTER TABLE `event` DISABLE KEYS */;
/*!40000 ALTER TABLE `event` ENABLE KEYS */;

-- Dumping structure for table sf_searchrec.reg
CREATE TABLE IF NOT EXISTS `reg` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `access_key` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `status` tinyint(2) NOT NULL DEFAULT '0',
  `ct` bigint(20) unsigned NOT NULL DEFAULT '0',
  `ut` bigint(20) unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE KEY `uni_search_reg_access_key` (`access_key`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=10000002 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC COMMENT='注册表';

-- Dumping data for table sf_searchrec.reg: ~2 rows (approximately)
/*!40000 ALTER TABLE `reg` DISABLE KEYS */;
INSERT INTO `reg` (`id`, `name`, `access_key`, `status`, `ct`, `ut`) VALUES
	(10000000, '测试', 'd0723c304fb94b1abc3759565c9dcb5d', 1, 1775795277335, 1775795277335),
	(10000001, 'carnival', 'aa1fe1ae24a4401b906153e4cc63b05c', 1, 1775756192899, 1775756192899);
/*!40000 ALTER TABLE `reg` ENABLE KEYS */;


-- Dumping database structure for sf_snowflake
CREATE DATABASE IF NOT EXISTS `sf_snowflake` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci */;
USE `sf_snowflake`;

-- Dumping structure for table sf_snowflake.event
CREATE TABLE IF NOT EXISTS `event` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT COMMENT 'Primary key ID',
  `dcid` int(10) unsigned NOT NULL DEFAULT '0' COMMENT 'datacenter id',
  `mid` int(10) unsigned NOT NULL DEFAULT '0' COMMENT 'machine id',
  `event_type` int(11) NOT NULL DEFAULT '0' COMMENT 'event type',
  `brief` text COLLATE utf8mb4_unicode_ci COMMENT 'event message',
  `detail` text COLLATE utf8mb4_unicode_ci COMMENT 'detailed information (JSON format)',
  `ct` bigint(20) unsigned NOT NULL DEFAULT '0' COMMENT 'creation time, UNIX timestamp in ms',
  PRIMARY KEY (`id`),
  KEY `idx_dc_mac` (`dcid`,`mid`,`event_type`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=202 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='event log';

-- Dumping data for table sf_snowflake.event: ~201 rows (approximately)
/*!40000 ALTER TABLE `event` DISABLE KEYS */;
INSERT INTO `event` (`id`, `dcid`, `mid`, `event_type`, `brief`, `detail`, `ct`) VALUES
	(1, 0, 0, 0, '', '{"recount": 0}', 1766742291035),
	(2, 0, 0, 0, '', '{"recount": 1}', 1766742294325),
	(3, 0, 0, 0, '', '{"recount": 2}', 1766742300042),
	(4, 0, 0, 0, '', '{"recount": 3}', 1766742300428),
	(5, 0, 0, 0, '', '{"recount": 0}', 1766742324488),
	(6, 0, 0, 0, '', '{"recount": 1}', 1766897679799),
	(7, 0, 0, 0, '', '{"recount": 2}', 1766897682446),
	(8, 0, 0, 0, '', '{"recount": 3}', 1766898274431),
	(9, 0, 0, 0, '', '{"recount": 0}', 1766898276666),
	(10, 0, 0, 0, '', '{"recount": 1}', 1766898642129),
	(11, 0, 0, 0, '', '{"recount": 2}', 1766898644187),
	(12, 0, 0, 0, '', '{"recount": 3}', 1766923116240),
	(13, 0, 0, 0, '', '{"recount": 0}', 1766923119115),
	(14, 0, 0, 0, '', '{"recount": 1}', 1766923278208),
	(15, 0, 0, 0, '', '{"recount": 2}', 1766923280256),
	(16, 0, 0, 0, '', '{"recount": 3}', 1766923592107),
	(17, 0, 0, 0, '', '{"recount": 0}', 1766923593902),
	(18, 0, 0, 0, '', '{"recount": 1}', 1766923904358),
	(19, 0, 0, 0, '', '{"recount": 2}', 1766923906740),
	(20, 0, 0, 0, '', '{"recount": 3}', 1766924224506),
	(21, 0, 0, 0, '', '{"recount": 0}', 1766924226354),
	(22, 0, 0, 0, '', '{"recount": 1}', 1766924459444),
	(23, 0, 0, 0, '', '{"recount": 2}', 1766924461195),
	(24, 0, 0, 0, '', '{"recount": 3}', 1766924577448),
	(25, 0, 0, 0, '', '{"recount": 0}', 1766924579564),
	(26, 0, 0, 0, '', '{"recount": 1}', 1766924590907),
	(27, 0, 0, 0, '', '{"recount": 2}', 1766924593186),
	(28, 0, 0, 0, '', '{"recount": 3}', 1766924725010),
	(29, 0, 0, 0, '', '{"recount": 0}', 1766924726994),
	(30, 0, 0, 0, '', '{"recount": 1}', 1766925159547),
	(31, 0, 0, 0, '', '{"recount": 2}', 1766925162011),
	(32, 0, 0, 0, '', '{"recount": 3}', 1766925172123),
	(33, 0, 0, 0, '', '{"recount": 0}', 1766925174397),
	(34, 0, 0, 0, '', '{"recount": 1}', 1767024313426),
	(35, 0, 0, 0, '', '{"recount": 2}', 1767024316061),
	(36, 0, 0, 0, '', '{"recount": 3}', 1767180310575),
	(37, 0, 0, 0, '', '{"recount": 0}', 1767180313716),
	(38, 0, 0, 0, '', '{"recount": 1}', 1767180340734),
	(39, 0, 0, 0, '', '{"recount": 2}', 1767180343154),
	(40, 0, 0, 0, '', '{"recount": 3}', 1767241351908),
	(41, 0, 0, 0, '', '{"recount": 0}', 1767241360732),
	(42, 0, 0, 0, '', '{"recount": 1}', 1767244576320),
	(43, 0, 0, 0, '', '{"recount": 2}', 1767244580405),
	(44, 0, 0, 0, '', '{"recount": 3}', 1767245544729),
	(45, 0, 0, 0, '', '{"recount": 0}', 1767245548701),
	(46, 0, 0, 0, '', '{"recount": 1}', 1767246153585),
	(47, 0, 0, 0, '', '{"recount": 2}', 1767246158603),
	(48, 0, 0, 0, '', '{"recount": 3}', 1767246904009),
	(49, 0, 0, 0, '', '{"recount": 0}', 1767246908506),
	(50, 0, 0, 0, '', '{"recount": 1}', 1767253793444),
	(51, 0, 0, 0, '', '{"recount": 2}', 1767253795257),
	(52, 0, 0, 0, '', '{"recount": 3}', 1767939983477),
	(53, 0, 0, 0, '', '{"recount": 0}', 1767939986412),
	(54, 0, 0, 0, '', '{"recount": 1}', 1767942563717),
	(55, 0, 0, 0, '', '{"recount": 2}', 1767942565779),
	(56, 0, 0, 0, '', '{"recount": 3}', 1767943586246),
	(57, 0, 0, 0, '', '{"recount": 0}', 1767943588336),
	(58, 0, 0, 0, '', '{"recount": 1}', 1767957759525),
	(59, 0, 0, 0, '', '{"recount": 2}', 1767957761492),
	(60, 0, 0, 0, '', '{"recount": 3}', 1767957883593),
	(61, 0, 0, 0, '', '{"recount": 0}', 1767957886221),
	(62, 0, 0, 0, '', '{"recount": 1}', 1767958017403),
	(63, 0, 0, 0, '', '{"recount": 2}', 1767958019257),
	(64, 0, 0, 0, '', '{"recount": 3}', 1768045972951),
	(65, 0, 0, 0, '', '{"recount": 0}', 1768045974607),
	(66, 0, 0, 0, '', '{"recount": 1}', 1768045977868),
	(67, 0, 0, 0, '', '{"recount": 2}', 1768047002482),
	(68, 0, 0, 0, '', '{"recount": 3}', 1768047007129),
	(69, 0, 0, 0, '', '{"recount": 0}', 1768047009419),
	(70, 0, 0, 0, '', '{"recount": 1}', 1768047153188),
	(71, 0, 0, 0, '', '{"recount": 2}', 1768047154506),
	(72, 0, 0, 0, '', '{"recount": 3}', 1768047158139),
	(73, 0, 0, 0, '', '{"recount": 0}', 1768047536180),
	(74, 0, 0, 0, '', '{"recount": 1}', 1768047537497),
	(75, 0, 0, 0, '', '{"recount": 2}', 1768047540199),
	(76, 0, 0, 0, '', '{"recount": 3}', 1768047937497),
	(77, 0, 0, 0, '', '{"recount": 0}', 1768047939174),
	(78, 0, 0, 0, '', '{"recount": 1}', 1768047941855),
	(79, 0, 0, 0, '', '{"recount": 3}', 1768056708618),
	(80, 0, 0, 0, '', '{"recount": 0}', 1768056710229),
	(81, 0, 0, 0, '', '{"recount": 1}', 1768056712616),
	(82, 0, 0, 0, '', '{"recount": 3}', 1768057136676),
	(83, 0, 0, 0, '', '{"recount": 0}', 1768057138023),
	(84, 0, 0, 0, '', '{"recount": 1}', 1768057140693),
	(85, 0, 0, 0, '', '{"recount": 2}', 1768061875048),
	(86, 0, 0, 0, '', '{"recount": 3}', 1768061876541),
	(87, 0, 0, 0, '', '{"recount": 0}', 1768061879297),
	(88, 0, 0, 0, '', '{"recount": 2}', 1768067392013),
	(89, 0, 0, 0, '', '{"recount": 3}', 1768067393481),
	(90, 0, 0, 0, '', '{"recount": 0}', 1768067396049),
	(91, 0, 0, 0, '', '{"recount": 1}', 1768070091546),
	(92, 0, 0, 0, '', '{"recount": 2}', 1768070092990),
	(93, 0, 0, 0, '', '{"recount": 3}', 1768070096876),
	(94, 0, 0, 0, '', '{"recount": 0}', 1768071963877),
	(95, 0, 0, 0, '', '{"recount": 1}', 1768071966741),
	(96, 0, 0, 0, '', '{"recount": 2}', 1768071969536),
	(97, 0, 0, 0, '', '{"recount": 3}', 1768097728268),
	(98, 0, 0, 0, '', '{"recount": 0}', 1768097730176),
	(99, 0, 0, 0, '', '{"recount": 1}', 1768097733917),
	(100, 0, 0, 0, '', '{"recount": 2}', 1768098260628),
	(101, 0, 0, 0, '', '{"recount": 3}', 1768098262028),
	(102, 0, 0, 0, '', '{"recount": 0}', 1768098264864),
	(103, 0, 0, 0, '', '{"recount": 1}', 1768099338014),
	(104, 0, 0, 0, '', '{"recount": 2}', 1768099339914),
	(105, 0, 0, 0, '', '{"recount": 3}', 1768099342661),
	(106, 0, 0, 0, '', '{"recount": 0}', 1768100643639),
	(107, 0, 0, 0, '', '{"recount": 1}', 1768100645032),
	(108, 0, 0, 0, '', '{"recount": 2}', 1768100647649),
	(109, 0, 0, 0, '', '{"recount": 3}', 1768100933924),
	(110, 0, 0, 0, '', '{"recount": 0}', 1768100935615),
	(111, 0, 0, 0, '', '{"recount": 1}', 1768100938215),
	(112, 0, 0, 0, '', '{"recount": 2}', 1768120667770),
	(113, 0, 0, 0, '', '{"recount": 3}', 1768120670959),
	(114, 0, 0, 0, '', '{"recount": 0}', 1768120684913),
	(115, 0, 0, 0, '', '{"recount": 1}', 1768121421698),
	(116, 0, 0, 0, '', '{"recount": 2}', 1768121423474),
	(117, 0, 0, 0, '', '{"recount": 3}', 1768121426077),
	(118, 0, 0, 0, '', '{"recount": 0}', 1768122465665),
	(119, 0, 0, 0, '', '{"recount": 1}', 1768122467409),
	(120, 0, 0, 0, '', '{"recount": 2}', 1768122470923),
	(121, 0, 0, 0, '', '{"recount": 3}', 1768123686642),
	(122, 0, 0, 0, '', '{"recount": 0}', 1768123688824),
	(123, 0, 0, 0, '', '{"recount": 1}', 1768123692136),
	(124, 0, 0, 0, '', '{"recount": 2}', 1768124326432),
	(125, 0, 0, 0, '', '{"recount": 3}', 1768124327992),
	(126, 0, 0, 0, '', '{"recount": 0}', 1768124331118),
	(127, 0, 0, 0, '', '{"recount": 1}', 1768134056608),
	(128, 0, 0, 0, '', '{"recount": 2}', 1768134058541),
	(129, 0, 0, 0, '', '{"recount": 3}', 1768134063545),
	(130, 0, 0, 0, '', '{"recount": 0}', 1768145923578),
	(131, 0, 0, 0, '', '{"recount": 1}', 1768145925494),
	(132, 0, 0, 0, '', '{"recount": 2}', 1768145929909),
	(133, 0, 0, 0, '', '{"recount": 3}', 1768149234399),
	(134, 0, 0, 0, '', '{"recount": 0}', 1768149236895),
	(135, 0, 0, 0, '', '{"recount": 1}', 1768149240738),
	(136, 0, 0, 0, '', '{"recount": 2}', 1768150141627),
	(137, 0, 0, 0, '', '{"recount": 3}', 1768150144902),
	(138, 0, 0, 0, '', '{"recount": 0}', 1768150150061),
	(139, 0, 0, 0, '', '{"recount": 1}', 1768151920259),
	(140, 0, 0, 0, '', '{"recount": 2}', 1768151921875),
	(141, 0, 0, 0, '', '{"recount": 3}', 1768151927437),
	(142, 0, 0, 0, '', '{"recount": 0}', 1768154727382),
	(143, 0, 0, 0, '', '{"recount": 1}', 1768154729192),
	(144, 0, 0, 0, '', '{"recount": 2}', 1768154732387),
	(145, 0, 0, 0, '', '{"recount": 3}', 1768188732040),
	(146, 0, 0, 0, '', '{"recount": 0}', 1768188733976),
	(147, 0, 0, 0, '', '{"recount": 1}', 1768188738103),
	(148, 0, 0, 0, '', '{"recount": 2}', 1768191437327),
	(149, 0, 0, 0, '', '{"recount": 3}', 1768191439519),
	(150, 0, 0, 0, '', '{"recount": 0}', 1768191443563),
	(151, 0, 0, 0, '', '{"recount": 1}', 1768192378629),
	(152, 0, 0, 0, '', '{"recount": 2}', 1768192380853),
	(153, 0, 0, 0, '', '{"recount": 3}', 1768192388172),
	(154, 0, 0, 0, '', '{"recount": 0}', 1768192622904),
	(155, 0, 0, 0, '', '{"recount": 1}', 1768192627174),
	(156, 0, 0, 0, '', '{"recount": 2}', 1768192629042),
	(157, 0, 0, 0, '', '{"recount": 3}', 1768193557500),
	(158, 0, 0, 0, '', '{"recount": 0}', 1768193559851),
	(159, 0, 0, 0, '', '{"recount": 1}', 1768193562343),
	(160, 0, 0, 0, '', '{"recount": 2}', 1768220301835),
	(161, 0, 0, 0, '', '{"recount": 3}', 1768220304804),
	(162, 0, 0, 0, '', '{"recount": 0}', 1768220308343),
	(163, 0, 0, 0, '', '{"recount": 1}', 1768233268519),
	(164, 0, 0, 0, '', '{"recount": 2}', 1768233270212),
	(165, 0, 0, 0, '', '{"recount": 3}', 1768233272912),
	(166, 0, 0, 0, '', '{"recount": 0}', 1768563803346),
	(167, 0, 0, 0, '', '{"recount": 1}', 1768563806036),
	(168, 0, 0, 0, '', '{"recount": 2}', 1768563809402),
	(169, 0, 0, 0, '', '{"recount": 3}', 1768723748715),
	(170, 0, 0, 0, '', '{"recount": 0}', 1768723752473),
	(171, 0, 0, 0, '', '{"recount": 1}', 1768727023463),
	(172, 0, 0, 0, '', '{"recount": 2}', 1768727026882),
	(173, 0, 0, 0, '', '{"recount": 3}', 1768727030871),
	(174, 0, 0, 0, '', '{"recount": 0}', 1771514320402),
	(175, 0, 0, 0, '', '{"recount": 1}', 1771514323486),
	(176, 0, 0, 0, '', '{"recount": 2}', 1771514327863),
	(177, 0, 0, 0, '', '{"recount": 3}', 1771902393612),
	(178, 0, 0, 0, '', '{"recount": 0}', 1772046928602),
	(179, 0, 0, 0, '', '{"recount": 1}', 1772046931162),
	(180, 0, 0, 0, '', '{"recount": 2}', 1772046934870),
	(181, 0, 0, 0, '', '{"recount": 3}', 1772532547630),
	(182, 0, 0, 0, '', '{"recount": 0}', 1772532550907),
	(183, 0, 0, 0, '', '{"recount": 1}', 1772532554467),
	(184, 0, 0, 0, '', '{"recount": 2}', 1772866503915),
	(185, 0, 0, 0, '', '{"recount": 3}', 1772866506769),
	(186, 0, 0, 0, '', '{"recount": 0}', 1772866510254),
	(187, 0, 0, 0, '', '{"recount": 1}', 1772884888871),
	(188, 0, 0, 0, '', '{"recount": 2}', 1772884895403),
	(189, 0, 0, 0, '', '{"recount": 3}', 1772884898766),
	(190, 0, 0, 0, '', '{"recount": 0}', 1773377736911),
	(191, 0, 0, 0, '', '{"recount": 1}', 1773377740026),
	(192, 0, 0, 0, '', '{"recount": 2}', 1773377743646),
	(193, 0, 0, 0, '', '{"recount": 3}', 1773980856886),
	(194, 0, 0, 0, '', '{"recount": 0}', 1773980858746),
	(195, 0, 0, 0, '', '{"recount": 1}', 1774181659473),
	(196, 0, 0, 0, '', '{"recount": 2}', 1775807384112),
	(197, 0, 0, 0, '', '{"recount": 0}', 1775811805672),
	(198, 0, 0, 0, '', '{"recount": 2}', 1775812769438),
	(199, 0, 0, 0, '', '{"recount": 0}', 1775873679634),
	(200, 0, 0, 0, '', '{"recount": 2}', 1775874826161),
	(201, 0, 0, 0, '', '{"recount": 0}', 1775876453107);
/*!40000 ALTER TABLE `event` ENABLE KEYS */;

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

-- Dumping data for table sf_snowflake.recounter: ~2 rows (approximately)
/*!40000 ALTER TABLE `recounter` DISABLE KEYS */;
INSERT INTO `recounter` (`id`, `dcid`, `mid`, `rc`, `ct`, `ut`) VALUES
	(129, 0, 0, 1, 1766717664774, 1775876453110),
	(130, 1, 2, 3, 1766718635976, 1766720269794);
/*!40000 ALTER TABLE `recounter` ENABLE KEYS */;

-- Dumping structure for table sf_snowflake.reg
CREATE TABLE IF NOT EXISTS `reg` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `access_key` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `status` tinyint(2) NOT NULL DEFAULT '0',
  `ct` bigint(20) unsigned NOT NULL DEFAULT '0',
  `ut` bigint(20) unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE KEY `uni_notice_reg_access_key` (`access_key`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=10000001 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC COMMENT='注册表';

-- Dumping data for table sf_snowflake.reg: ~1 rows (approximately)
/*!40000 ALTER TABLE `reg` DISABLE KEYS */;
INSERT INTO `reg` (`id`, `name`, `access_key`, `status`, `ct`, `ut`) VALUES
	(10000000, '测试', '59bbdb9aee884ec69f8badcaa6296774', 1, 1775873230976, 1775873230976);
/*!40000 ALTER TABLE `reg` ENABLE KEYS */;


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

-- Dumping data for table sf_test.auth_group: ~0 rows (approximately)
/*!40000 ALTER TABLE `auth_group` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_group` ENABLE KEYS */;

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

-- Dumping data for table sf_test.auth_group_permissions: ~0 rows (approximately)
/*!40000 ALTER TABLE `auth_group_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_group_permissions` ENABLE KEYS */;

-- Dumping structure for table sf_test.auth_permission
CREATE TABLE IF NOT EXISTS `auth_permission` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `content_type_id` int(11) NOT NULL,
  `codename` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_permission_content_type_id_codename_01ab375a_uniq` (`content_type_id`,`codename`),
  CONSTRAINT `auth_permission_content_type_id_2f476e4b_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=93 DEFAULT CHARSET=latin1;

-- Dumping data for table sf_test.auth_permission: ~92 rows (approximately)
/*!40000 ALTER TABLE `auth_permission` DISABLE KEYS */;
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES
	(1, 'Can add log entry', 1, 'add_logentry'),
	(2, 'Can change log entry', 1, 'change_logentry'),
	(3, 'Can delete log entry', 1, 'delete_logentry'),
	(4, 'Can view log entry', 1, 'view_logentry'),
	(5, 'Can add permission', 2, 'add_permission'),
	(6, 'Can change permission', 2, 'change_permission'),
	(7, 'Can delete permission', 2, 'delete_permission'),
	(8, 'Can view permission', 2, 'view_permission'),
	(9, 'Can add group', 3, 'add_group'),
	(10, 'Can change group', 3, 'change_group'),
	(11, 'Can delete group', 3, 'delete_group'),
	(12, 'Can view group', 3, 'view_group'),
	(13, 'Can add user', 4, 'add_user'),
	(14, 'Can change user', 4, 'change_user'),
	(15, 'Can delete user', 4, 'delete_user'),
	(16, 'Can view user', 4, 'view_user'),
	(17, 'Can add content type', 5, 'add_contenttype'),
	(18, 'Can change content type', 5, 'change_contenttype'),
	(19, 'Can delete content type', 5, 'delete_contenttype'),
	(20, 'Can view content type', 5, 'view_contenttype'),
	(21, 'Can add session', 6, 'add_session'),
	(22, 'Can change session', 6, 'change_session'),
	(23, 'Can delete session', 6, 'delete_session'),
	(24, 'Can view session', 6, 'view_session'),
	(25, 'Can add metadata', 7, 'add_metadata'),
	(26, 'Can change metadata', 7, 'change_metadata'),
	(27, 'Can delete metadata', 7, 'delete_metadata'),
	(28, 'Can view metadata', 7, 'view_metadata'),
	(29, 'Can add distribution', 8, 'add_distribution'),
	(30, 'Can change distribution', 8, 'change_distribution'),
	(31, 'Can delete distribution', 8, 'delete_distribution'),
	(32, 'Can view distribution', 8, 'view_distribution'),
	(33, 'Can add invalidation', 9, 'add_invalidation'),
	(34, 'Can change invalidation', 9, 'change_invalidation'),
	(35, 'Can delete invalidation', 9, 'delete_invalidation'),
	(36, 'Can view invalidation', 9, 'view_invalidation'),
	(37, 'Can add user', 10, 'add_user'),
	(38, 'Can change user', 10, 'change_user'),
	(39, 'Can delete user', 10, 'delete_user'),
	(40, 'Can view user', 10, 'view_user'),
	(41, 'Can add password reset code', 11, 'add_passwordresetcode'),
	(42, 'Can change password reset code', 11, 'change_passwordresetcode'),
	(43, 'Can delete password reset code', 11, 'delete_passwordresetcode'),
	(44, 'Can view password reset code', 11, 'view_passwordresetcode'),
	(45, 'Can add mail account', 12, 'add_mailaccount'),
	(46, 'Can change mail account', 12, 'change_mailaccount'),
	(47, 'Can delete mail account', 12, 'delete_mailaccount'),
	(48, 'Can view mail account', 12, 'view_mailaccount'),
	(49, 'Can add mailbox', 13, 'add_mailbox'),
	(50, 'Can change mailbox', 13, 'change_mailbox'),
	(51, 'Can delete mailbox', 13, 'delete_mailbox'),
	(52, 'Can view mailbox', 13, 'view_mailbox'),
	(53, 'Can add mail message', 14, 'add_mailmessage'),
	(54, 'Can change mail message', 14, 'change_mailmessage'),
	(55, 'Can delete mail message', 14, 'delete_mailmessage'),
	(56, 'Can view mail message', 14, 'view_mailmessage'),
	(57, 'Can add mail attachment', 15, 'add_mailattachment'),
	(58, 'Can change mail attachment', 15, 'change_mailattachment'),
	(59, 'Can delete mail attachment', 15, 'delete_mailattachment'),
	(60, 'Can view mail attachment', 15, 'view_mailattachment'),
	(61, 'Can add notice record', 16, 'add_noticerecord'),
	(62, 'Can change notice record', 16, 'change_noticerecord'),
	(63, 'Can delete notice record', 16, 'delete_noticerecord'),
	(64, 'Can view notice record', 16, 'view_noticerecord'),
	(65, 'Can add reg', 17, 'add_reg'),
	(66, 'Can change reg', 17, 'change_reg'),
	(67, 'Can delete reg', 17, 'delete_reg'),
	(68, 'Can view reg', 17, 'view_reg'),
	(69, 'Can add search rec document', 18, 'add_searchrecdocument'),
	(70, 'Can change search rec document', 18, 'change_searchrecdocument'),
	(71, 'Can delete search rec document', 18, 'delete_searchrecdocument'),
	(72, 'Can view search rec document', 18, 'view_searchrecdocument'),
	(73, 'Can add event', 19, 'add_event'),
	(74, 'Can change event', 19, 'change_event'),
	(75, 'Can delete event', 19, 'delete_event'),
	(76, 'Can view event', 19, 'view_event'),
	(77, 'Can add verify code', 20, 'add_verifycode'),
	(78, 'Can change verify code', 20, 'change_verifycode'),
	(79, 'Can delete verify code', 20, 'delete_verifycode'),
	(80, 'Can view verify code', 20, 'view_verifycode'),
	(81, 'Can add reg', 21, 'add_reg'),
	(82, 'Can change reg', 21, 'change_reg'),
	(83, 'Can delete reg', 21, 'delete_reg'),
	(84, 'Can view reg', 21, 'view_reg'),
	(85, 'Can add search rec doc term', 22, 'add_searchrecdocterm'),
	(86, 'Can change search rec doc term', 22, 'change_searchrecdocterm'),
	(87, 'Can delete search rec doc term', 22, 'delete_searchrecdocterm'),
	(88, 'Can view search rec doc term', 22, 'view_searchrecdocterm'),
	(89, 'Can add search rec event', 23, 'add_searchrecevent'),
	(90, 'Can change search rec event', 23, 'change_searchrecevent'),
	(91, 'Can delete search rec event', 23, 'delete_searchrecevent'),
	(92, 'Can view search rec event', 23, 'view_searchrecevent');
/*!40000 ALTER TABLE `auth_permission` ENABLE KEYS */;

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

-- Dumping data for table sf_test.auth_user: ~0 rows (approximately)
/*!40000 ALTER TABLE `auth_user` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_user` ENABLE KEYS */;

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

-- Dumping data for table sf_test.auth_user_groups: ~0 rows (approximately)
/*!40000 ALTER TABLE `auth_user_groups` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_user_groups` ENABLE KEYS */;

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

-- Dumping data for table sf_test.auth_user_user_permissions: ~0 rows (approximately)
/*!40000 ALTER TABLE `auth_user_user_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_user_user_permissions` ENABLE KEYS */;

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

-- Dumping data for table sf_test.django_admin_log: ~0 rows (approximately)
/*!40000 ALTER TABLE `django_admin_log` DISABLE KEYS */;
/*!40000 ALTER TABLE `django_admin_log` ENABLE KEYS */;

-- Dumping structure for table sf_test.django_content_type
CREATE TABLE IF NOT EXISTS `django_content_type` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `app_label` varchar(100) NOT NULL,
  `model` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `django_content_type_app_label_model_76bd3d3b_uniq` (`app_label`,`model`)
) ENGINE=InnoDB AUTO_INCREMENT=24 DEFAULT CHARSET=latin1;

-- Dumping data for table sf_test.django_content_type: ~23 rows (approximately)
/*!40000 ALTER TABLE `django_content_type` DISABLE KEYS */;
INSERT INTO `django_content_type` (`id`, `app_label`, `model`) VALUES
	(1, 'admin', 'logentry'),
	(8, 'app_cdn', 'distribution'),
	(9, 'app_cdn', 'invalidation'),
	(12, 'app_mailserver', 'mailaccount'),
	(15, 'app_mailserver', 'mailattachment'),
	(13, 'app_mailserver', 'mailbox'),
	(14, 'app_mailserver', 'mailmessage'),
	(16, 'app_notice', 'noticerecord'),
	(17, 'app_notice', 'reg'),
	(7, 'app_oss', 'metadata'),
	(22, 'app_searchrec', 'searchrecdocterm'),
	(18, 'app_searchrec', 'searchrecdocument'),
	(23, 'app_searchrec', 'searchrecevent'),
	(19, 'app_user', 'event'),
	(11, 'app_user', 'passwordresetcode'),
	(10, 'app_user', 'user'),
	(21, 'app_verify', 'reg'),
	(20, 'app_verify', 'verifycode'),
	(3, 'auth', 'group'),
	(2, 'auth', 'permission'),
	(4, 'auth', 'user'),
	(5, 'contenttypes', 'contenttype'),
	(6, 'sessions', 'session');
/*!40000 ALTER TABLE `django_content_type` ENABLE KEYS */;

-- Dumping structure for table sf_test.django_migrations
CREATE TABLE IF NOT EXISTS `django_migrations` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `app` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `applied` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=28 DEFAULT CHARSET=latin1;

-- Dumping data for table sf_test.django_migrations: ~18 rows (approximately)
/*!40000 ALTER TABLE `django_migrations` DISABLE KEYS */;
INSERT INTO `django_migrations` (`id`, `app`, `name`, `applied`) VALUES
	(1, 'contenttypes', '0001_initial', '2026-03-24 08:21:13.841315'),
	(2, 'auth', '0001_initial', '2026-03-24 08:21:14.133873'),
	(3, 'admin', '0001_initial', '2026-03-24 08:21:14.219858'),
	(4, 'admin', '0002_logentry_remove_auto_add', '2026-03-24 08:21:14.236849'),
	(5, 'admin', '0003_logentry_add_action_flag_choices', '2026-03-24 08:21:14.251414'),
	(13, 'contenttypes', '0002_remove_content_type_name', '2026-03-24 08:21:14.402646'),
	(14, 'auth', '0002_alter_permission_name_max_length', '2026-03-24 08:21:14.426434'),
	(15, 'auth', '0003_alter_user_email_max_length', '2026-03-24 08:21:14.448565'),
	(16, 'auth', '0004_alter_user_username_opts', '2026-03-24 08:21:14.460257'),
	(17, 'auth', '0005_alter_user_last_login_null', '2026-03-24 08:21:14.496032'),
	(18, 'auth', '0006_require_contenttypes_0002', '2026-03-24 08:21:14.501854'),
	(19, 'auth', '0007_alter_validators_add_error_messages', '2026-03-24 08:21:14.511943'),
	(20, 'auth', '0008_alter_user_username_max_length', '2026-03-24 08:21:14.535600'),
	(21, 'auth', '0009_alter_user_last_name_max_length', '2026-03-24 08:21:14.556399'),
	(22, 'auth', '0010_alter_group_name_max_length', '2026-03-24 08:21:14.578937'),
	(23, 'auth', '0011_update_proxy_permissions', '2026-03-24 08:21:14.594469'),
	(24, 'auth', '0012_alter_user_first_name_max_length', '2026-03-24 08:21:14.615085'),
	(25, 'sessions', '0001_initial', '2026-03-24 08:21:14.646511');
/*!40000 ALTER TABLE `django_migrations` ENABLE KEYS */;

-- Dumping structure for table sf_test.django_session
CREATE TABLE IF NOT EXISTS `django_session` (
  `session_key` varchar(40) NOT NULL,
  `session_data` longtext NOT NULL,
  `expire_date` datetime(6) NOT NULL,
  PRIMARY KEY (`session_key`),
  KEY `django_session_expire_date_a5c62663` (`expire_date`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- Dumping data for table sf_test.django_session: ~0 rows (approximately)
/*!40000 ALTER TABLE `django_session` DISABLE KEYS */;
/*!40000 ALTER TABLE `django_session` ENABLE KEYS */;


-- Dumping database structure for sf_user
CREATE DATABASE IF NOT EXISTS `sf_user` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci */;
USE `sf_user`;

-- Dumping structure for table sf_user.event
CREATE TABLE IF NOT EXISTS `event` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `biz_type` tinyint(4) NOT NULL DEFAULT '0' COMMENT '0-unknown, 1-register, 2-update_profile, 3-user_auth, 4-password_reset',
  `status` tinyint(2) NOT NULL DEFAULT '0' COMMENT '0-init, 1-pending, 3-completed, 9-failed',
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
  KEY `idx_event_verify_code_id` (`verify_code_id`) USING BTREE,
  KEY `idx_event_biz_status_notice_ct` (`biz_type`,`status`,`notice_target`,`ct`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=15 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Dumping data for table sf_user.event: ~14 rows (approximately)
/*!40000 ALTER TABLE `event` DISABLE KEYS */;
INSERT INTO `event` (`id`, `biz_type`, `status`, `level`, `verify_code_id`, `verify_ref_id`, `notice_target`, `notice_channel`, `payload_json`, `message`, `ct`, `ut`) VALUES
	(1, 3, 3, 3, 1, 1, 'zhang_career@foxmail.com', 0, '{"user_id": 1, "bit": 1}', 'completed', 1774443484566, 1774443501116),
	(2, 1, 3, 3, 5, 2, 'string', 0, '{"username": "test", "password_hash": "pbkdf2_sha256$390000$1J1qAajkaOicvwmGJuIlhL$lRGKHQVU0pVzmA8fLOb5K0iAYhWJhYTNqB+JeAnuU90=", "email": "test@example.com", "phone": "12345678901", "avatar": "", "ext": {}}', 'completed', 1775119301879, 1775119458054),
	(3, 4, 3, 3, 6, 3, 'test@example.com', 0, '{"user_id": 2}', 'completed', 1775124541113, 1775124612357),
	(4, 4, 3, 3, 7, 4, 'test@example.com', 0, '{"user_id": 2}', 'completed', 1775129139521, 1775129189676),
	(5, 1, 1, 3, 8, 5, 'test@example.com', 0, '{"username": "test", "password_hash": "pbkdf2_sha256$390000$U8aqjcwaOoCUfpflyH575b$wiutEqV0yZdyE5AhpWvTf7h0LFSnP5XLi02m1IkOpl0=", "email": "test@example.com", "phone": "12345678901", "avatar": "", "ext": {}}', '', 1775300302062, 1775300302958),
	(6, 1, 1, 3, 9, 6, 'test@example.com', 0, '{"username": "test", "password_hash": "pbkdf2_sha256$390000$LvX20jRLorx0GfewcfwkQm$myt8HiWwYjo4Ot4w7O4LJ4Y00bsqUK1N+WbWXyrl6Dc=", "email": "test@example.com", "phone": "13333333333", "avatar": "", "ext": {}}', '', 1775302108645, 1775302108659),
	(7, 1, 3, 3, 10, 7, 'test@example.com', 0, '{"username": "test", "password_hash": "pbkdf2_sha256$390000$kZxLx6Vxcz7P3egq1O2cEQ$Wl/esSHJvRNJgPcqSSOqgA25jvPRDHWmPBaqUGmWIfo=", "email": "test@example.com", "phone": "13333333333", "avatar": "", "ext": {}}', 'completed', 1775302530038, 1775302553556),
	(8, 1, 1, 3, 11, 8, 'test@example.com', 0, '{"username": "test", "password_hash": "pbkdf2_sha256$390000$7sJFVpMqbfSOPeL2Bvd3Z0$DgENUpLd0uJ+A+Z/BLxMYuae/3k2NnKCeTWWgpKMvZ8=", "email": "test@example.com", "phone": "13333333333", "avatar": "", "ext": {}}', '', 1775303127257, 1775303127270),
	(9, 1, 3, 3, 12, 9, 'test@example.com', 0, '{"username": "test", "password_hash": "pbkdf2_sha256$390000$sGO3fKM0YEVzVhUPd1i7HF$1SolcnfAjpMqqCwCbjc9LR4SUAli9J8iZ0GldjQuKCk=", "email": "test@example.com", "phone": "13333333333", "avatar": "", "ext": {}}', 'completed', 1775303154234, 1775303168522),
	(10, 1, 1, 3, 13, 10, 'test@example.com', 0, '{"username": "test", "password_hash": "pbkdf2_sha256$390000$9EpPBAu8nNfsalfPXHokN2$bEvh9SjJe/VEboEtXEtGzrIrFHk01QHfFEgPMegPwn4=", "email": "test@example.com", "phone": "13333333333", "avatar": "", "ext": {}}', 'waiting for verified', 1775308259352, 1775308272176),
	(11, 1, 3, 3, 14, 11, 'test@example.com', 0, '{"username": "test", "password_hash": "pbkdf2_sha256$390000$s4ar83wtLfmilhkq05hQWv$V+OQb4i7xXW0I1uFMbTpxCVo+4VcYd8JwHkr/MjKCzo=", "email": "test@example.com", "phone": "13333333333", "avatar": "", "ext": {}}', 'completed', 1775361570560, 1775361609510),
	(12, 1, 3, 3, 15, 12, 'test@example.com', 0, '{"username": "test", "password_hash": "pbkdf2_sha256$390000$ykp5MwwiCO4SMaSM0XyTwF$z8dqMwX459hhbfO2mmljDyxIdGH5dwh5acTCT7xFizg=", "email": "test@example.com", "phone": "13333333333", "avatar": "", "ext": {}}', 'completed', 1775361734413, 1775361782381),
	(13, 4, 9, 3, 16, 13, 'test@example.com', 0, '{"user_id": 6}', 'superseded', 1775362761160, 1775364599368),
	(14, 4, 3, 3, 17, 14, 'test@example.com', 0, '{"user_id": 6}', 'completed', 1775364599369, 1775364634499);
/*!40000 ALTER TABLE `event` ENABLE KEYS */;

-- Dumping structure for table sf_user.token
CREATE TABLE IF NOT EXISTS `token` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` bigint(20) unsigned NOT NULL DEFAULT '0',
  `token` varchar(512) COLLATE utf8_unicode_ci NOT NULL DEFAULT '' COMMENT 'access token',
  `refresh` varchar(255) COLLATE utf8_unicode_ci NOT NULL DEFAULT '' COMMENT 'refresh token',
  `status` tinyint(4) NOT NULL DEFAULT '0' COMMENT 'token状态，0-init, 1-in_use, 2-deprecated',
  `expires_at` bigint(20) unsigned NOT NULL DEFAULT '0',
  `ct` bigint(20) unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE KEY `uni_user_token_refresh` (`user_id`,`refresh`) USING BTREE,
  UNIQUE KEY `uni_user_token_token` (`user_id`,`token`),
  KEY `idx_user_token_status` (`user_id`,`status`)
) ENGINE=InnoDB AUTO_INCREMENT=153 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci COMMENT='令牌';

-- Dumping data for table sf_user.token: ~63 rows (approximately)
/*!40000 ALTER TABLE `token` DISABLE KEYS */;
INSERT INTO `token` (`id`, `user_id`, `token`, `refresh`, `status`, `expires_at`, `ct`) VALUES
	(90, 6, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoiYWNjZXNzIiwidXNlcl9pZCI6NiwidXNlcm5hbWUiOiJ0ZXN0IiwiaWF0IjoxNzc1NzExNTA2LCJleHAiOjE3NzU3MTg3MDZ9.DD9bickdZwc5tZZyAFD9yT3TbII4msOfwWwm774_xDE', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoicmVmcmVzaCIsInVzZXJfaWQiOjYsInVzZXJuYW1lIjoidGVzdCIsImlhdCI6MTc3NTcxMTUwNiwiZXhwIjoxNzc2MzE2MzA2fQ.Bx6ArR5Xih-lTnpL9QyhR24xmYDShCFHx1Z5r3VnjlM', 2, 1775718706000, 1775711506011),
	(91, 6, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoiYWNjZXNzIiwidXNlcl9pZCI6NiwidXNlcm5hbWUiOiJ0ZXN0IiwiaWF0IjoxNzc1NzExNjIwLCJleHAiOjE3NzU3MTg4MjB9.8DkIp07bLBrygDeRUnbPl1diOh5AINru_uL8VzNNS78', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoicmVmcmVzaCIsInVzZXJfaWQiOjYsInVzZXJuYW1lIjoidGVzdCIsImlhdCI6MTc3NTcxMTYyMCwiZXhwIjoxNzc2MzE2NDIwfQ.Dl52hj-M--rtt2aCuCB5kfwGOR21aTdSgIZOOJYe4TE', 2, 1775718820000, 1775711620153),
	(92, 6, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoiYWNjZXNzIiwidXNlcl9pZCI6NiwidXNlcm5hbWUiOiJ0ZXN0IiwiaWF0IjoxNzc1NzExOTIwLCJleHAiOjE3NzU3MTkxMjB9.60JL9fvONuzT4Jz5nFkkOBJPpNT6E1NFD-nqoKiC27A', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoicmVmcmVzaCIsInVzZXJfaWQiOjYsInVzZXJuYW1lIjoidGVzdCIsImlhdCI6MTc3NTcxMTkyMCwiZXhwIjoxNzc2MzE2NzIwfQ.MW07iyeU1fJVLv04n4BIYV5CeSdFSHFxs86y7cr37KM', 2, 1775719120000, 1775711920649),
	(93, 6, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoiYWNjZXNzIiwidXNlcl9pZCI6NiwidXNlcm5hbWUiOiJ0ZXN0IiwiaWF0IjoxNzc1NzEyMjIwLCJleHAiOjE3NzU3MTk0MjB9.ly9rtAlgwbBJPK0NOe3i74GxAoICyOtOySwqz5mrw20', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoicmVmcmVzaCIsInVzZXJfaWQiOjYsInVzZXJuYW1lIjoidGVzdCIsImlhdCI6MTc3NTcxMjIyMCwiZXhwIjoxNzc2MzE3MDIwfQ.UESHC8GeTATSUG7hMQ4b43UvAjnJtqw5_44Qd5kvam0', 2, 1775719420000, 1775712220967),
	(94, 6, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoiYWNjZXNzIiwidXNlcl9pZCI6NiwidXNlcm5hbWUiOiJ0ZXN0IiwiaWF0IjoxNzc1NzEyNTIxLCJleHAiOjE3NzU3MTk3MjF9.mLhGbX971qW7KwM46K3Hl5AX6PuXudofk8shOCwd17U', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoicmVmcmVzaCIsInVzZXJfaWQiOjYsInVzZXJuYW1lIjoidGVzdCIsImlhdCI6MTc3NTcxMjUyMSwiZXhwIjoxNzc2MzE3MzIxfQ.Ne2Eb9r40CXjc48iBEj-aZmhDc6rBbC7hSAwfkZWGhA', 2, 1775719721000, 1775712521346),
	(95, 6, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoiYWNjZXNzIiwidXNlcl9pZCI6NiwidXNlcm5hbWUiOiJ0ZXN0IiwiaWF0IjoxNzc1NzEyODIyLCJleHAiOjE3NzU3MjAwMjJ9.p7sv2ysuHKFpvnFXNC8i4hmnD3E8kDyZD6sjlQ2udoQ', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoicmVmcmVzaCIsInVzZXJfaWQiOjYsInVzZXJuYW1lIjoidGVzdCIsImlhdCI6MTc3NTcxMjgyMiwiZXhwIjoxNzc2MzE3NjIyfQ.YrcGJpBGm_0VI2uqjjLIJrZp0K9NswZjfaeK_o1T8pU', 2, 1775720022000, 1775712822302),
	(96, 6, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoiYWNjZXNzIiwidXNlcl9pZCI6NiwidXNlcm5hbWUiOiJ0ZXN0IiwiaWF0IjoxNzc1NzEzMTIyLCJleHAiOjE3NzU3MjAzMjJ9.u6OE6S4FuCMdaS31AFt9WNdXyixIC8O9VK7FRSbEjeY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoicmVmcmVzaCIsInVzZXJfaWQiOjYsInVzZXJuYW1lIjoidGVzdCIsImlhdCI6MTc3NTcxMzEyMiwiZXhwIjoxNzc2MzE3OTIyfQ.DRX18MWdrrixO5IDrVgCzowlW28d0mAMJ4ovSD37ZMg', 2, 1775720322000, 1775713122715),
	(97, 6, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoiYWNjZXNzIiwidXNlcl9pZCI6NiwidXNlcm5hbWUiOiJ0ZXN0IiwiaWF0IjoxNzc1NzEzNDIzLCJleHAiOjE3NzU3MjA2MjN9.DYXeCiPxiWNQ_rcnEcxQVzleJfYoLHb9XQ-wHZwO7ZE', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoicmVmcmVzaCIsInVzZXJfaWQiOjYsInVzZXJuYW1lIjoidGVzdCIsImlhdCI6MTc3NTcxMzQyMywiZXhwIjoxNzc2MzE4MjIzfQ.a1mPn9wGWFOALCA8nw9mI5CsaSgI-SNrjSO0BWdMbGk', 2, 1775720623000, 1775713423213),
	(98, 6, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoiYWNjZXNzIiwidXNlcl9pZCI6NiwidXNlcm5hbWUiOiJ0ZXN0IiwiaWF0IjoxNzc1NzEzNzIzLCJleHAiOjE3NzU3MjA5MjN9.07WNrs3ZuAr8igOfOffBjI_mnbaNpubFB4uYlClui5Y', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoicmVmcmVzaCIsInVzZXJfaWQiOjYsInVzZXJuYW1lIjoidGVzdCIsImlhdCI6MTc3NTcxMzcyMywiZXhwIjoxNzc2MzE4NTIzfQ.7IR9Biv9Fhd7wQeM4Si3WN5hWXNCOyEr7zMTGQq1yc4', 2, 1775720923000, 1775713723595),
	(99, 6, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoiYWNjZXNzIiwidXNlcl9pZCI6NiwidXNlcm5hbWUiOiJ0ZXN0IiwiaWF0IjoxNzc1NzE0MDI0LCJleHAiOjE3NzU3MjEyMjR9._qkwTMMs-vqAqGahdnkE1evHhJy_Px8llYD4E67FDsk', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoicmVmcmVzaCIsInVzZXJfaWQiOjYsInVzZXJuYW1lIjoidGVzdCIsImlhdCI6MTc3NTcxNDAyNCwiZXhwIjoxNzc2MzE4ODI0fQ.roOu-KXxvn9wewj3gTSnN9ikgiME7ZoY7ujss0r7hy8', 2, 1775721224000, 1775714024086),
	(100, 6, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoiYWNjZXNzIiwidXNlcl9pZCI6NiwidXNlcm5hbWUiOiJ0ZXN0IiwiaWF0IjoxNzc1NzE0MzI0LCJleHAiOjE3NzU3MjE1MjR9.uvOJI4CpAMhwYZvbkI1R3Rw4vEVGMfLebDZ4vOMC3j8', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoicmVmcmVzaCIsInVzZXJfaWQiOjYsInVzZXJuYW1lIjoidGVzdCIsImlhdCI6MTc3NTcxNDMyNCwiZXhwIjoxNzc2MzE5MTI0fQ.S_lQ_q-NVec0FtPKzPXBm2ufvzEnUXUkdQGBPaQQofM', 2, 1775721524000, 1775714324470),
	(101, 6, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoiYWNjZXNzIiwidXNlcl9pZCI6NiwidXNlcm5hbWUiOiJ0ZXN0IiwiaWF0IjoxNzc1NzE0NjI0LCJleHAiOjE3NzU3MjE4MjR9.ddTPXk5S2g4sINEtb6v1G0RByCxcjpFDTmq83hb520k', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoicmVmcmVzaCIsInVzZXJfaWQiOjYsInVzZXJuYW1lIjoidGVzdCIsImlhdCI6MTc3NTcxNDYyNCwiZXhwIjoxNzc2MzE5NDI0fQ.VKebxTH5Zb8see0p99gP-1BCU5ja120HoGqgRfAVo0E', 2, 1775721824000, 1775714624895),
	(102, 6, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoiYWNjZXNzIiwidXNlcl9pZCI6NiwidXNlcm5hbWUiOiJ0ZXN0IiwiaWF0IjoxNzc1NzE0OTI1LCJleHAiOjE3NzU3MjIxMjV9.avst_1hsJo7YL54QXczbfcdXtvUt1Y0oeUtAfmOsiIM', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoicmVmcmVzaCIsInVzZXJfaWQiOjYsInVzZXJuYW1lIjoidGVzdCIsImlhdCI6MTc3NTcxNDkyNSwiZXhwIjoxNzc2MzE5NzI1fQ.dksc0pQBM6zopDpgP-VNcNw9AEHH070USURU_kzsMY4', 2, 1775722125000, 1775714925329),
	(103, 6, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoiYWNjZXNzIiwidXNlcl9pZCI6NiwidXNlcm5hbWUiOiJ0ZXN0IiwiaWF0IjoxNzc1NzE1MjI1LCJleHAiOjE3NzU3MjI0MjV9.IodyH8rDtQdR5tsUI-LsqdtxdSIBLiozxD1KPav-HMc', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoicmVmcmVzaCIsInVzZXJfaWQiOjYsInVzZXJuYW1lIjoidGVzdCIsImlhdCI6MTc3NTcxNTIyNSwiZXhwIjoxNzc2MzIwMDI1fQ.47PFMYaUqkuZ-pQGralhu2hdmYgaTXzPOFIcat9Da3k', 2, 1775722425000, 1775715225722),
	(104, 6, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoiYWNjZXNzIiwidXNlcl9pZCI6NiwidXNlcm5hbWUiOiJ0ZXN0IiwiaWF0IjoxNzc1NzE1NTI2LCJleHAiOjE3NzU3MjI3MjZ9.ZzgE7AhlFSHALu-5GheyjDEw_NixGMgnEGQf7qD-r2k', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoicmVmcmVzaCIsInVzZXJfaWQiOjYsInVzZXJuYW1lIjoidGVzdCIsImlhdCI6MTc3NTcxNTUyNiwiZXhwIjoxNzc2MzIwMzI2fQ.V9OAXvujmCRZIRf7Jqupicy_fnBNpAglBUP-1KHZx3Q', 2, 1775722726000, 1775715526063),
	(105, 6, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoiYWNjZXNzIiwidXNlcl9pZCI6NiwidXNlcm5hbWUiOiJ0ZXN0IiwiaWF0IjoxNzc1NzE1ODI2LCJleHAiOjE3NzU3MjMwMjZ9.ORnl4QNlMeXVkHUBReZaEbbd4xvQQoxhpwwwTZwFkoc', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoicmVmcmVzaCIsInVzZXJfaWQiOjYsInVzZXJuYW1lIjoidGVzdCIsImlhdCI6MTc3NTcxNTgyNiwiZXhwIjoxNzc2MzIwNjI2fQ.FMx1m6huURnng1mTNQWb7G77MagnUjx6IVuGz2sDbDY', 2, 1775723026000, 1775715826436),
	(106, 6, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoiYWNjZXNzIiwidXNlcl9pZCI6NiwidXNlcm5hbWUiOiJ0ZXN0IiwiaWF0IjoxNzc1NzE2OTg0LCJleHAiOjE3NzU3MjQxODR9.NqUJst5IAUQ7Ah6Kw0wkoZmrhlc2dfHJhFRW7UVAzSA', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoicmVmcmVzaCIsInVzZXJfaWQiOjYsInVzZXJuYW1lIjoidGVzdCIsImlhdCI6MTc3NTcxNjk4NCwiZXhwIjoxNzc2MzIxNzg0fQ.irPty7UClLJe4Lu31RioZz1zhTyYjY5qrJxTHnw2cV4', 2, 1775724184000, 1775716984670),
	(107, 6, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoiYWNjZXNzIiwidXNlcl9pZCI6NiwidXNlcm5hbWUiOiJ0ZXN0IiwiaWF0IjoxNzc1NzE3Mjg1LCJleHAiOjE3NzU3MjQ0ODV9.grDFqByp0bkUjI0ZR4Tdvn6l9r61XG-r46ZDYKFNEXo', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoicmVmcmVzaCIsInVzZXJfaWQiOjYsInVzZXJuYW1lIjoidGVzdCIsImlhdCI6MTc3NTcxNzI4NSwiZXhwIjoxNzc2MzIyMDg1fQ.mFAsAlFYws4bSIjVf1NLkO3gOUO7zGdzH7rvm9tsBak', 2, 1775724485000, 1775717285342),
	(108, 6, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoiYWNjZXNzIiwidXNlcl9pZCI6NiwidXNlcm5hbWUiOiJ0ZXN0IiwiaWF0IjoxNzc1NzE3NTg1LCJleHAiOjE3NzU3MjQ3ODV9.ycFEu4bseaXFId_fhXok9n253OIDFKWfc2nSpTt_cos', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoicmVmcmVzaCIsInVzZXJfaWQiOjYsInVzZXJuYW1lIjoidGVzdCIsImlhdCI6MTc3NTcxNzU4NSwiZXhwIjoxNzc2MzIyMzg1fQ.lBp5XSl20wDQPZBV02XRDsmx31YAuMlcTC56msvTukw', 2, 1775724785000, 1775717585754),
	(109, 6, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoiYWNjZXNzIiwidXNlcl9pZCI6NiwidXNlcm5hbWUiOiJ0ZXN0IiwiaWF0IjoxNzc1NzE3ODg2LCJleHAiOjE3NzU3MjUwODZ9.YzKFYQKDOkPtCZZnUuGz4HOyX94hBLa7kpOHosWrbTk', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoicmVmcmVzaCIsInVzZXJfaWQiOjYsInVzZXJuYW1lIjoidGVzdCIsImlhdCI6MTc3NTcxNzg4NiwiZXhwIjoxNzc2MzIyNjg2fQ.G-0w6kYkkz4xZ6si1dELYn3fVvh87rCIX_Td03MUcRI', 2, 1775725086000, 1775717886124),
	(110, 6, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoiYWNjZXNzIiwidXNlcl9pZCI6NiwidXNlcm5hbWUiOiJ0ZXN0IiwiaWF0IjoxNzc1NzE4MTg2LCJleHAiOjE3NzU3MjUzODZ9.Q9Muo6_0ssdx28n42yvUMSPpBEHDStC_FpV4mMz41_s', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoicmVmcmVzaCIsInVzZXJfaWQiOjYsInVzZXJuYW1lIjoidGVzdCIsImlhdCI6MTc3NTcxODE4NiwiZXhwIjoxNzc2MzIyOTg2fQ.jKv4WyjiQoJhS0tc4E3uc6TVtkyp1LZOEgUM596PQEI', 2, 1775725386000, 1775718186588),
	(111, 6, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoiYWNjZXNzIiwidXNlcl9pZCI6NiwidXNlcm5hbWUiOiJ0ZXN0IiwiaWF0IjoxNzc1NzE4NDg2LCJleHAiOjE3NzU3MjU2ODZ9.KD1vuNJXDV-uwwhWIEcZiOA-TuMogCvNqNFApqTBykE', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoicmVmcmVzaCIsInVzZXJfaWQiOjYsInVzZXJuYW1lIjoidGVzdCIsImlhdCI6MTc3NTcxODQ4NiwiZXhwIjoxNzc2MzIzMjg2fQ.XG2Q10dU8CjGdurxiy10IRtCbR1FuG889wldEsKA50c', 2, 1775725686000, 1775718486956),
	(112, 6, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoiYWNjZXNzIiwidXNlcl9pZCI6NiwidXNlcm5hbWUiOiJ0ZXN0IiwiaWF0IjoxNzc1NzE4Nzg3LCJleHAiOjE3NzU3MjU5ODd9.VyOmjuvIe3OKauR9QbtKtqYpRGbImM-VDE5FlFNozos', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoicmVmcmVzaCIsInVzZXJfaWQiOjYsInVzZXJuYW1lIjoidGVzdCIsImlhdCI6MTc3NTcxODc4NywiZXhwIjoxNzc2MzIzNTg3fQ.N-BxFiNsGaew9q5Is8LN4uOcJKrpqsXRR2H8_z7qJO8', 2, 1775725987000, 1775718787332),
	(113, 6, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoiYWNjZXNzIiwidXNlcl9pZCI6NiwidXNlcm5hbWUiOiJ0ZXN0IiwiaWF0IjoxNzc1NzE5MDg3LCJleHAiOjE3NzU3MjYyODd9.o4kg8SSzPxOFOfieJ0OP2wzogyMmxDICVlOTo0a8SB8', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoicmVmcmVzaCIsInVzZXJfaWQiOjYsInVzZXJuYW1lIjoidGVzdCIsImlhdCI6MTc3NTcxOTA4NywiZXhwIjoxNzc2MzIzODg3fQ.o6mHpjBUIv153rWvsfbPwwUO-K2bqRrXRyNfGqzUzmI', 2, 1775726287000, 1775719087873),
	(114, 6, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoiYWNjZXNzIiwidXNlcl9pZCI6NiwidXNlcm5hbWUiOiJ0ZXN0IiwiaWF0IjoxNzc1NzE5Mzg4LCJleHAiOjE3NzU3MjY1ODh9.HewqicfoNmKVP8RjtDQGcVji6kvecNogSPmC0xy0m7s', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoicmVmcmVzaCIsInVzZXJfaWQiOjYsInVzZXJuYW1lIjoidGVzdCIsImlhdCI6MTc3NTcxOTM4OCwiZXhwIjoxNzc2MzI0MTg4fQ.j2T8MPyZ81J_8RVBEjYphrK3hNmPQK0VpVKsSmtQf9k', 2, 1775726588000, 1775719388465),
	(115, 6, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoiYWNjZXNzIiwidXNlcl9pZCI6NiwidXNlcm5hbWUiOiJ0ZXN0IiwiaWF0IjoxNzc1NzE5Njg4LCJleHAiOjE3NzU3MjY4ODh9.UnTOq7kXreEw7FCqFw_HwEN_a4HxFp50JcHZOn2q9rA', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoicmVmcmVzaCIsInVzZXJfaWQiOjYsInVzZXJuYW1lIjoidGVzdCIsImlhdCI6MTc3NTcxOTY4OCwiZXhwIjoxNzc2MzI0NDg4fQ.rt7QxEoyOuvLBB4DzbOzuQDzE0tbBajj3qquusYUA1M', 2, 1775726888000, 1775719688885),
	(116, 6, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoiYWNjZXNzIiwidXNlcl9pZCI6NiwidXNlcm5hbWUiOiJ0ZXN0IiwiaWF0IjoxNzc1NzE5OTg5LCJleHAiOjE3NzU3MjcxODl9.P6nxKP4K6DRligW2sn-ykIKFUWCfl7cDc6lkUnoRB0s', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoicmVmcmVzaCIsInVzZXJfaWQiOjYsInVzZXJuYW1lIjoidGVzdCIsImlhdCI6MTc3NTcxOTk4OSwiZXhwIjoxNzc2MzI0Nzg5fQ.pPeu3v9vUIOOS0m49aTOMsZ8UEv4koOaupYJpvsJIvw', 2, 1775727189000, 1775719989355),
	(117, 6, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoiYWNjZXNzIiwidXNlcl9pZCI6NiwidXNlcm5hbWUiOiJ0ZXN0IiwiaWF0IjoxNzc1NzIwMjg5LCJleHAiOjE3NzU3Mjc0ODl9.mLugUmNCbFUiyAmKz1ZsvD0IGUVLJAxdLsdeuyFExdE', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoicmVmcmVzaCIsInVzZXJfaWQiOjYsInVzZXJuYW1lIjoidGVzdCIsImlhdCI6MTc3NTcyMDI4OSwiZXhwIjoxNzc2MzI1MDg5fQ.HKKQak_EOWt543EcBmNxp9WozgMZEUY_HffRPP00eb8', 2, 1775727489000, 1775720289884),
	(118, 6, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoiYWNjZXNzIiwidXNlcl9pZCI6NiwidXNlcm5hbWUiOiJ0ZXN0IiwiaWF0IjoxNzc1NzIwNTkwLCJleHAiOjE3NzU3Mjc3OTB9.HoDfdchQ_nHw8DQishr1JF7xBskVidczbLQx_814T0o', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoicmVmcmVzaCIsInVzZXJfaWQiOjYsInVzZXJuYW1lIjoidGVzdCIsImlhdCI6MTc3NTcyMDU5MCwiZXhwIjoxNzc2MzI1MzkwfQ.xQHoWENF9SukYyc90NgxAb0Cl48QXQozy0VhZoF25CY', 2, 1775727790000, 1775720590262),
	(119, 6, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoiYWNjZXNzIiwidXNlcl9pZCI6NiwidXNlcm5hbWUiOiJ0ZXN0IiwiaWF0IjoxNzc1NzI5MDYzLCJleHAiOjE3NzU3MzYyNjN9.ODLMkVj7xZCHEHzkGFSl61uAvqwdGxKccZXEolqOG1o', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoicmVmcmVzaCIsInVzZXJfaWQiOjYsInVzZXJuYW1lIjoidGVzdCIsImlhdCI6MTc3NTcyOTA2MywiZXhwIjoxNzc2MzMzODYzfQ.6pYXF7V1iQNP2FA_PpiBNheVOwkU5-iN5LrOUPQX3BY', 2, 1775736263000, 1775729063552),
	(120, 6, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoiYWNjZXNzIiwidXNlcl9pZCI6NiwidXNlcm5hbWUiOiJ0ZXN0IiwiaWF0IjoxNzc1ODM2NDg3LCJleHAiOjE3NzU4NDM2ODd9.F77uFl2O75q0MrOpN4v9bU1uZ2GRNZiACw9kvPdgT3Q', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoicmVmcmVzaCIsInVzZXJfaWQiOjYsInVzZXJuYW1lIjoidGVzdCIsImlhdCI6MTc3NTgzNjQ4NywiZXhwIjoxNzc2NDQxMjg3fQ.9Znfu5ofCYzi1a-6lpxIJoSmPa6_lWbTV-7Q2NMmA-E', 2, 1775843687000, 1775836487903),
	(121, 6, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoiYWNjZXNzIiwidXNlcl9pZCI6NiwidXNlcm5hbWUiOiJ0ZXN0IiwiaWF0IjoxNzc1ODM2Nzg4LCJleHAiOjE3NzU4NDM5ODh9.VIXzUOdsNNzF9R2tj2DcKHr7ruzJgK_3YiXIDp-tRts', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoicmVmcmVzaCIsInVzZXJfaWQiOjYsInVzZXJuYW1lIjoidGVzdCIsImlhdCI6MTc3NTgzNjc4OCwiZXhwIjoxNzc2NDQxNTg4fQ.gLzU0edhvWeCXSEh_ZKBQrxSYXFwAFKzwPxmykeXDEE', 2, 1775843988000, 1775836788392),
	(122, 6, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoiYWNjZXNzIiwidXNlcl9pZCI6NiwidXNlcm5hbWUiOiJ0ZXN0IiwiaWF0IjoxNzc1ODM3MDg4LCJleHAiOjE3NzU4NDQyODh9.Z7h9cnG4YEezpS47dJSw9NWqkEES4csPXpwLgMYtZqA', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoicmVmcmVzaCIsInVzZXJfaWQiOjYsInVzZXJuYW1lIjoidGVzdCIsImlhdCI6MTc3NTgzNzA4OCwiZXhwIjoxNzc2NDQxODg4fQ.MnPpFbWRbk5vRrAjXFdCCq7oyujPJB-eoP98KM9mSd0', 2, 1775844288000, 1775837088602),
	(123, 6, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoiYWNjZXNzIiwidXNlcl9pZCI6NiwidXNlcm5hbWUiOiJ0ZXN0IiwiaWF0IjoxNzc1ODM3ODI1LCJleHAiOjE3NzU4NDUwMjV9.vRDmKKA_e24WCg3whEUp2EkXuyPFa9u3AkFGjSqYgUI', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoicmVmcmVzaCIsInVzZXJfaWQiOjYsInVzZXJuYW1lIjoidGVzdCIsImlhdCI6MTc3NTgzNzgyNSwiZXhwIjoxNzc2NDQyNjI1fQ.NIBSxL_DtruvEKN3crtFZcTzMdbdFVJ3cSaYHjrg53w', 2, 1775845025000, 1775837825733),
	(124, 6, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoiYWNjZXNzIiwidXNlcl9pZCI6NiwidXNlcm5hbWUiOiJ0ZXN0IiwiaWF0IjoxNzc1ODM4MTI2LCJleHAiOjE3NzU4NDUzMjZ9.dnTn1IhieVIgj6BJAVj3vY3w_4LMmPuF0wduybAysac', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoicmVmcmVzaCIsInVzZXJfaWQiOjYsInVzZXJuYW1lIjoidGVzdCIsImlhdCI6MTc3NTgzODEyNiwiZXhwIjoxNzc2NDQyOTI2fQ.Z7JJPGkQvWP3xyG2ZnzHzrULwPsWCCLHBh0nwSzYK04', 2, 1775845326000, 1775838126170),
	(125, 6, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoiYWNjZXNzIiwidXNlcl9pZCI6NiwidXNlcm5hbWUiOiJ0ZXN0IiwiaWF0IjoxNzc1ODM4NDI2LCJleHAiOjE3NzU4NDU2MjZ9.FQmI49YFXfwYlzTNlaAhc4e60xfGxdGKroLCAVyEEmU', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoicmVmcmVzaCIsInVzZXJfaWQiOjYsInVzZXJuYW1lIjoidGVzdCIsImlhdCI6MTc3NTgzODQyNiwiZXhwIjoxNzc2NDQzMjI2fQ.Ct0yu2MasicGcbKyvEgT0qq9VPgdOd1Mw4GmYv3VZiE', 2, 1775845626000, 1775838426539),
	(126, 6, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoiYWNjZXNzIiwidXNlcl9pZCI6NiwidXNlcm5hbWUiOiJ0ZXN0IiwiaWF0IjoxNzc1ODM4NzMwLCJleHAiOjE3NzU4NDU5MzB9.3IPsSsSmaKFhlLsjC3KS2H9yQRw7cHKcIiu87gEUedU', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoicmVmcmVzaCIsInVzZXJfaWQiOjYsInVzZXJuYW1lIjoidGVzdCIsImlhdCI6MTc3NTgzODczMCwiZXhwIjoxNzc2NDQzNTMwfQ.PB6_TH3D15--7isaWq4-kSXq8NmPZkUhvA6zeuvOXOQ', 2, 1775845930000, 1775838730051),
	(127, 6, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoiYWNjZXNzIiwidXNlcl9pZCI6NiwidXNlcm5hbWUiOiJ0ZXN0IiwiaWF0IjoxNzc1ODM5MDMwLCJleHAiOjE3NzU4NDYyMzB9.dUbdh0JBK9_Wx6rcxSSh15JY_1bEfnAJEJJXKqivaIU', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoicmVmcmVzaCIsInVzZXJfaWQiOjYsInVzZXJuYW1lIjoidGVzdCIsImlhdCI6MTc3NTgzOTAzMCwiZXhwIjoxNzc2NDQzODMwfQ.uz4VkC_qrBFRw5X4Z9eNEucviprKH7k0tJyI28tPcMM', 2, 1775846230000, 1775839030250),
	(128, 6, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoiYWNjZXNzIiwidXNlcl9pZCI6NiwidXNlcm5hbWUiOiJ0ZXN0IiwiaWF0IjoxNzc1ODM5MzMwLCJleHAiOjE3NzU4NDY1MzB9.YIyiNPZn1JuR67oWOBpHufPWLC5Jj2RrvriYaFPIraY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoicmVmcmVzaCIsInVzZXJfaWQiOjYsInVzZXJuYW1lIjoidGVzdCIsImlhdCI6MTc3NTgzOTMzMCwiZXhwIjoxNzc2NDQ0MTMwfQ.zbAudhx1pc4Dj0XeEe5wrTCgo8WJkqUO9jC2UbL8aQ8', 2, 1775846530000, 1775839330588),
	(129, 6, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoiYWNjZXNzIiwidXNlcl9pZCI6NiwidXNlcm5hbWUiOiJ0ZXN0IiwiaWF0IjoxNzc1ODM5NjMwLCJleHAiOjE3NzU4NDY4MzB9.wTskYtAWlwCOFEMzrHIWU_QXXHUQrU0XBy6uwBLU3Oo', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoicmVmcmVzaCIsInVzZXJfaWQiOjYsInVzZXJuYW1lIjoidGVzdCIsImlhdCI6MTc3NTgzOTYzMCwiZXhwIjoxNzc2NDQ0NDMwfQ.0_YT8RIBiXwtNMdEXtY-Cg1hrhqaNfVj5EcUse-B1ho', 2, 1775846830000, 1775839630953),
	(130, 6, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoiYWNjZXNzIiwidXNlcl9pZCI6NiwidXNlcm5hbWUiOiJ0ZXN0IiwiaWF0IjoxNzc1ODM5OTMxLCJleHAiOjE3NzU4NDcxMzF9.OqRqsyAjwV7PB8Tq6NASodW7wcXa5tao1h8mlGF245s', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoicmVmcmVzaCIsInVzZXJfaWQiOjYsInVzZXJuYW1lIjoidGVzdCIsImlhdCI6MTc3NTgzOTkzMSwiZXhwIjoxNzc2NDQ0NzMxfQ.GjrAHS2ntRg_YtTXrl5R4ZymUnC26snJw-mX84ROTdo', 2, 1775847131000, 1775839931514),
	(131, 6, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoiYWNjZXNzIiwidXNlcl9pZCI6NiwidXNlcm5hbWUiOiJ0ZXN0IiwiaWF0IjoxNzc1ODQwMjMxLCJleHAiOjE3NzU4NDc0MzF9.NstTZIxpO8J92XKN7HPsVW2oB6VQA59ZSqa4gFQsilA', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoicmVmcmVzaCIsInVzZXJfaWQiOjYsInVzZXJuYW1lIjoidGVzdCIsImlhdCI6MTc3NTg0MDIzMSwiZXhwIjoxNzc2NDQ1MDMxfQ.HRv85mrpyP8YUUr8kESn7mHWWv2yhSqK0PVFYxdT9jQ', 2, 1775847431000, 1775840231906),
	(132, 6, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoiYWNjZXNzIiwidXNlcl9pZCI6NiwidXNlcm5hbWUiOiJ0ZXN0IiwiaWF0IjoxNzc1ODQwNTM1LCJleHAiOjE3NzU4NDc3MzV9.ZVIsP250wyuB_s86VxYAFDCsuQrlRCn8sHL33ZHK5eg', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoicmVmcmVzaCIsInVzZXJfaWQiOjYsInVzZXJuYW1lIjoidGVzdCIsImlhdCI6MTc3NTg0MDUzNSwiZXhwIjoxNzc2NDQ1MzM1fQ.WpLorRgbW2CnbJ716ENxDg6J_d2-RYowyO6qO2UuNlM', 2, 1775847735000, 1775840535520),
	(133, 6, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoiYWNjZXNzIiwidXNlcl9pZCI6NiwidXNlcm5hbWUiOiJ0ZXN0IiwiaWF0IjoxNzc1ODQwODM1LCJleHAiOjE3NzU4NDgwMzV9.CGZek8aMtVDT4AQ8ddnkOBrQrT0bE9FLv-pzt4z60Aw', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoicmVmcmVzaCIsInVzZXJfaWQiOjYsInVzZXJuYW1lIjoidGVzdCIsImlhdCI6MTc3NTg0MDgzNSwiZXhwIjoxNzc2NDQ1NjM1fQ.FDycPU7deGzINy2sBAyJTW_kHA2BrGzSu5f9tM3_mhI', 2, 1775848035000, 1775840835762),
	(134, 6, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoiYWNjZXNzIiwidXNlcl9pZCI6NiwidXNlcm5hbWUiOiJ0ZXN0IiwiaWF0IjoxNzc1ODQxMTM2LCJleHAiOjE3NzU4NDgzMzZ9.P9nHJinkn7qDxjNrpdDWLeTaxRsO2OwXJo-nbidZUno', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoicmVmcmVzaCIsInVzZXJfaWQiOjYsInVzZXJuYW1lIjoidGVzdCIsImlhdCI6MTc3NTg0MTEzNiwiZXhwIjoxNzc2NDQ1OTM2fQ.pUzevbUIf-ZBhSXYqc0dkvT0hmaT1uw-a9gVQpzlpYg', 2, 1775848336000, 1775841136094),
	(135, 6, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoiYWNjZXNzIiwidXNlcl9pZCI6NiwidXNlcm5hbWUiOiJ0ZXN0IiwiaWF0IjoxNzc1ODQxNDM2LCJleHAiOjE3NzU4NDg2MzZ9.UQbtQA88O1aMQxix8BgyZJGZiJayLtSTe4MWp9QOxKo', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoicmVmcmVzaCIsInVzZXJfaWQiOjYsInVzZXJuYW1lIjoidGVzdCIsImlhdCI6MTc3NTg0MTQzNiwiZXhwIjoxNzc2NDQ2MjM2fQ.ILtOtITnfCsojLj4nn9gYuk08zOtfzaYTlxONN0PS_o', 2, 1775848636000, 1775841436289),
	(136, 6, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoiYWNjZXNzIiwidXNlcl9pZCI6NiwidXNlcm5hbWUiOiJ0ZXN0IiwiaWF0IjoxNzc1ODQxNzM2LCJleHAiOjE3NzU4NDg5MzZ9.36ApusoBb3wltDfgvvDX-hWWeApspMUBCXctx5uVMRA', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoicmVmcmVzaCIsInVzZXJfaWQiOjYsInVzZXJuYW1lIjoidGVzdCIsImlhdCI6MTc3NTg0MTczNiwiZXhwIjoxNzc2NDQ2NTM2fQ.GRY9cl7TMFtk1S0ZV5sw88C7EnNbIOaMRD3rfd0PLq4', 2, 1775848936000, 1775841736492),
	(137, 6, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoiYWNjZXNzIiwidXNlcl9pZCI6NiwidXNlcm5hbWUiOiJ0ZXN0IiwiaWF0IjoxNzc1ODQyMDM2LCJleHAiOjE3NzU4NDkyMzZ9.AjFCRly9IsCSL_Q1IzoyMXlSfpZJCm_nC9sU07GIFrg', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoicmVmcmVzaCIsInVzZXJfaWQiOjYsInVzZXJuYW1lIjoidGVzdCIsImlhdCI6MTc3NTg0MjAzNiwiZXhwIjoxNzc2NDQ2ODM2fQ.OnVm2-k8iwILMItYAcQUIcUkzzIUsTJ17u1bU8yjpew', 2, 1775849236000, 1775842036841),
	(138, 6, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoiYWNjZXNzIiwidXNlcl9pZCI6NiwidXNlcm5hbWUiOiJ0ZXN0IiwiaWF0IjoxNzc1ODQyMzQwLCJleHAiOjE3NzU4NDk1NDB9.KOyofjejef-D0rVzP_1SZfwvaDEEr_em94fa_vOTRUM', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoicmVmcmVzaCIsInVzZXJfaWQiOjYsInVzZXJuYW1lIjoidGVzdCIsImlhdCI6MTc3NTg0MjM0MCwiZXhwIjoxNzc2NDQ3MTQwfQ.VsTn-dACoeXv-Oiih_YcF5LqGY2olGQGnuz0ASWUGBg', 2, 1775849540000, 1775842340406),
	(139, 6, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoiYWNjZXNzIiwidXNlcl9pZCI6NiwidXNlcm5hbWUiOiJ0ZXN0IiwiaWF0IjoxNzc1ODQyNjQwLCJleHAiOjE3NzU4NDk4NDB9.XHF_3AOubkgG39IH6SFo8q8IOtk7BdFL2jV0PkjARTc', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoicmVmcmVzaCIsInVzZXJfaWQiOjYsInVzZXJuYW1lIjoidGVzdCIsImlhdCI6MTc3NTg0MjY0MCwiZXhwIjoxNzc2NDQ3NDQwfQ.HBBTuTZnJzYobAeSmzPRHV44CshWTQY-tdyRlHaMJTY', 2, 1775849840000, 1775842640573),
	(140, 6, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoiYWNjZXNzIiwidXNlcl9pZCI6NiwidXNlcm5hbWUiOiJ0ZXN0IiwiaWF0IjoxNzc1ODQyOTQwLCJleHAiOjE3NzU4NTAxNDB9.qhT3xUlA0eJ82yD7OcwuHXZixSG6OwseCHfngGYagbA', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoicmVmcmVzaCIsInVzZXJfaWQiOjYsInVzZXJuYW1lIjoidGVzdCIsImlhdCI6MTc3NTg0Mjk0MCwiZXhwIjoxNzc2NDQ3NzQwfQ.UZJMHtC_eEmWnE_0nRMZZ1p9j8iFgjHQMNo_aUXMn-w', 2, 1775850140000, 1775842940889),
	(141, 6, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoiYWNjZXNzIiwidXNlcl9pZCI6NiwidXNlcm5hbWUiOiJ0ZXN0IiwiaWF0IjoxNzc1ODQzMjQxLCJleHAiOjE3NzU4NTA0NDF9.JVqEryLQ4jDPYhyqHDbyPa1hSKSKsI8kKlKiXK5FtsE', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoicmVmcmVzaCIsInVzZXJfaWQiOjYsInVzZXJuYW1lIjoidGVzdCIsImlhdCI6MTc3NTg0MzI0MSwiZXhwIjoxNzc2NDQ4MDQxfQ.iuDOCLsW8trWNWlq2NDKxhwQVy_iaaj-k6-aNckqwUs', 2, 1775850441000, 1775843241156),
	(142, 6, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoiYWNjZXNzIiwidXNlcl9pZCI6NiwidXNlcm5hbWUiOiJ0ZXN0IiwiaWF0IjoxNzc1ODQzNTQxLCJleHAiOjE3NzU4NTA3NDF9.leXUXS5UOBZV0VWr_yBUHoLMn1ut6Myr9btXKMr4Nv0', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoicmVmcmVzaCIsInVzZXJfaWQiOjYsInVzZXJuYW1lIjoidGVzdCIsImlhdCI6MTc3NTg0MzU0MSwiZXhwIjoxNzc2NDQ4MzQxfQ.JbbUYOa0ADyBckACIPsCHexJKmPZboBh3UQkeU9ru98', 2, 1775850741000, 1775843541329),
	(143, 6, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoiYWNjZXNzIiwidXNlcl9pZCI6NiwidXNlcm5hbWUiOiJ0ZXN0IiwiaWF0IjoxNzc1ODQzODQzLCJleHAiOjE3NzU4NTEwNDN9.bGyIgzON1XVxZFphgQ4UYt5dy1RuAI0cv-DspOvZk3Y', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoicmVmcmVzaCIsInVzZXJfaWQiOjYsInVzZXJuYW1lIjoidGVzdCIsImlhdCI6MTc3NTg0Mzg0MywiZXhwIjoxNzc2NDQ4NjQzfQ.e9NhzyEyxhIYLbWZTmGbfbL026KjGzU81dCO4eev2Bc', 2, 1775851043000, 1775843843758),
	(144, 6, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoiYWNjZXNzIiwidXNlcl9pZCI6NiwidXNlcm5hbWUiOiJ0ZXN0IiwiaWF0IjoxNzc1ODQ5Njk1LCJleHAiOjE3NzU4NTY4OTV9.aZ6c1bXBiqJEpN6diBrfHNeS_6kvJ0ujqB4egf4fKaw', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoicmVmcmVzaCIsInVzZXJfaWQiOjYsInVzZXJuYW1lIjoidGVzdCIsImlhdCI6MTc3NTg0OTY5NSwiZXhwIjoxNzc2NDU0NDk1fQ.VPTMfrtsiOoxDAr7EW95h4N0e3_hANGgN_P1QlBTvEI', 2, 1775856895000, 1775849695612),
	(145, 6, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoiYWNjZXNzIiwidXNlcl9pZCI6NiwidXNlcm5hbWUiOiJ0ZXN0IiwiaWF0IjoxNzc1ODU0NzI0LCJleHAiOjE3NzU4NjE5MjR9.B9uB1xqDnTfTnun2rt_vV1SZxhLzoVRtkhptp4_3Vn0', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoicmVmcmVzaCIsInVzZXJfaWQiOjYsInVzZXJuYW1lIjoidGVzdCIsImlhdCI6MTc3NTg1NDcyNCwiZXhwIjoxNzc2NDU5NTI0fQ.y-aIGIdOasDSTc80H0y2mFcPaoNsMvziqH5SuPNgC7E', 2, 1775861924000, 1775854724994),
	(146, 6, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoiYWNjZXNzIiwidXNlcl9pZCI6NiwidXNlcm5hbWUiOiJ0ZXN0IiwiaWF0IjoxNzc1ODU4MzU4LCJleHAiOjE3NzU4NjU1NTh9.i_l480Pc3evqq-gB6tA0Trzi6iC0An36X8E5u7tdVNM', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoicmVmcmVzaCIsInVzZXJfaWQiOjYsInVzZXJuYW1lIjoidGVzdCIsImlhdCI6MTc3NTg1ODM1OCwiZXhwIjoxNzc2NDYzMTU4fQ.S4KEwMOUrBJTgQZg4iCwhfJUYEzSEC9roGUZY2eZcS0', 2, 1775865558000, 1775858358733),
	(147, 6, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoiYWNjZXNzIiwidXNlcl9pZCI6NiwidXNlcm5hbWUiOiJ0ZXN0IiwiaWF0IjoxNzc1ODYyMDc4LCJleHAiOjE3NzU4NjkyNzh9.5_tpGV6ScteU4Gl-jt2cTXJ_1y4L9RmUqFJkmOxiNeU', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoicmVmcmVzaCIsInVzZXJfaWQiOjYsInVzZXJuYW1lIjoidGVzdCIsImlhdCI6MTc3NTg2MjA3OCwiZXhwIjoxNzc2NDY2ODc4fQ.DPn-n7AjoAKhPt89d96nEHLG1L7BUJ91piWewWXDpPk', 2, 1775869278000, 1775862078457),
	(148, 6, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoiYWNjZXNzIiwidXNlcl9pZCI6NiwidXNlcm5hbWUiOiJ0ZXN0IiwiaWF0IjoxNzc1ODY1NjMzLCJleHAiOjE3NzU4NzI4MzN9.V4HA-DTCQqaxHoYfZmCPbJC0xMyRqnad1o9PHQQUYVQ', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoicmVmcmVzaCIsInVzZXJfaWQiOjYsInVzZXJuYW1lIjoidGVzdCIsImlhdCI6MTc3NTg2NTYzMywiZXhwIjoxNzc2NDcwNDMzfQ.FK1gHg5cQsWsS6OOxxbMym4Mh25M3w49mlNiLuUiZaQ', 2, 1775872833000, 1775865633342),
	(149, 6, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoiYWNjZXNzIiwidXNlcl9pZCI6NiwidXNlcm5hbWUiOiJ0ZXN0IiwiaWF0IjoxNzc1ODY1OTMzLCJleHAiOjE3NzU4NzMxMzN9.pGxT3b4j-AreulchicipKETqqtKuMqvFbucfHTbLV4I', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoicmVmcmVzaCIsInVzZXJfaWQiOjYsInVzZXJuYW1lIjoidGVzdCIsImlhdCI6MTc3NTg2NTkzMywiZXhwIjoxNzc2NDcwNzMzfQ.gGRyDnmhStE-_snPeWEUtsd6MOFp_IB41eBzrPGqLdY', 2, 1775873133000, 1775865933652),
	(150, 6, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoiYWNjZXNzIiwidXNlcl9pZCI6NiwidXNlcm5hbWUiOiJ0ZXN0IiwiaWF0IjoxNzc1ODcwMjYwLCJleHAiOjE3NzU4Nzc0NjB9.WjevdqfSu4fRexjO8x0gsZHN6_wU7H9Z_7_gZ9y_y-s', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoicmVmcmVzaCIsInVzZXJfaWQiOjYsInVzZXJuYW1lIjoidGVzdCIsImlhdCI6MTc3NTg3MDI2MCwiZXhwIjoxNzc2NDc1MDYwfQ.ciu9uh01EoGW4BkA5mYXN7-v_EQqL4KP2ptzb1xzhp4', 2, 1775877460000, 1775870260664),
	(151, 6, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoiYWNjZXNzIiwidXNlcl9pZCI6NiwidXNlcm5hbWUiOiJ0ZXN0IiwiaWF0IjoxNzc1ODc1ODcxLCJleHAiOjE3NzU4ODMwNzF9.fRwXDKV9iYA4p0-4d7ol_dIAaojRVRtyAPnYy1sFcZU', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoicmVmcmVzaCIsInVzZXJfaWQiOjYsInVzZXJuYW1lIjoidGVzdCIsImlhdCI6MTc3NTg3NTg3MSwiZXhwIjoxNzc2NDgwNjcxfQ.ObOYJKI7xgWI_e3IVsSg6qqHwLqQhJLHn1VlL_fgiM4', 2, 1775883071000, 1775875871220),
	(152, 6, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoiYWNjZXNzIiwidXNlcl9pZCI6NiwidXNlcm5hbWUiOiJ0ZXN0IiwiaWF0IjoxNzc1ODgwMzM0LCJleHAiOjE3NzU4ODc1MzR9.43nxhPuQ0YRhkSLlQIBP9y3887EblFmZQ92jkKRRF-A', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoicmVmcmVzaCIsInVzZXJfaWQiOjYsInVzZXJuYW1lIjoidGVzdCIsImlhdCI6MTc3NTg4MDMzNCwiZXhwIjoxNzc2NDg1MTM0fQ.c_2y95UHKuLaUFgXv94wKQYGBXDRqHZA9w5vofdaRac', 1, 1775887534000, 1775880334185);
/*!40000 ALTER TABLE `token` ENABLE KEYS */;

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
  `ctrl_status` tinyint(4) NOT NULL DEFAULT '0' COMMENT '处置状态，0-none, 1-login_forbidden',
  `ctrl_reason` varchar(512) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT '处置原因',
  `ext` text COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '扩展',
  `ct` bigint(20) unsigned NOT NULL DEFAULT '0',
  `ut` bigint(20) unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE KEY `uni_user_email` (`email`) USING BTREE,
  UNIQUE KEY `uni_user_phone` (`phone`) USING BTREE,
  UNIQUE KEY `uni_user_name` (`name`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- Dumping data for table sf_user.user: ~2 rows (approximately)
/*!40000 ALTER TABLE `user` DISABLE KEYS */;
INSERT INTO `user` (`id`, `name`, `pw_hash`, `email`, `phone`, `avatar`, `status`, `auth_status`, `ctrl_status`, `ctrl_reason`, `ext`, `ct`, `ut`) VALUES
	(1, 'zhang', 'pbkdf2_sha256$390000$ZQNpT1kLO3fu0MfSFNDhVk$H27I3BROxjb4/vCkj0L5olCrjmx11XGNaieIQWirD+8=', 'zhang_career@foxmail.com', '18611100339', '/api/oss/user/avatar/20260326/e1c10f744d8a45d0b4f90c769d1a3707.jpg', 1, 1, 0, '', '{}', 1774443484563, 1774520533497),
	(6, 'test', 'pbkdf2_sha256$390000$mAAIr5H365bwDHRFRgUp2V$U1iZ6pDBDCdZTzIweOM+YzJtUDJZNgh29rj3A+NTGfU=', 'test@example.com', '13333333333', '', 1, 0, 0, '', '{}', 1775361782379, 1775364634497);
/*!40000 ALTER TABLE `user` ENABLE KEYS */;


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

-- Dumping data for table sf_verify.reg: ~0 rows (approximately)
/*!40000 ALTER TABLE `reg` DISABLE KEYS */;
INSERT INTO `reg` (`id`, `name`, `access_key`, `status`, `ct`, `ut`) VALUES
	(1, '用户中心', 'f5b68d4560a04529a8a6347c4a5a209c', 1, 1774427127769, 1774427127769);
/*!40000 ALTER TABLE `reg` ENABLE KEYS */;

-- Dumping structure for table sf_verify.verify_code
CREATE TABLE IF NOT EXISTS `verify_code` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `reg_id` bigint(20) unsigned NOT NULL DEFAULT '0' COMMENT '注册ID',
  `ref_id` bigint(20) unsigned NOT NULL DEFAULT '0',
  `level` tinyint(4) NOT NULL DEFAULT '0' COMMENT '安全等级：0-pass, 1-low, 2-medium, 3-high',
  `code` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `expires_at` bigint(20) unsigned NOT NULL DEFAULT '0',
  `used_at` bigint(20) unsigned NOT NULL DEFAULT '0',
  `ct` bigint(20) unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`) USING BTREE,
  KEY `idx_verify_exp` (`expires_at`) USING BTREE,
  KEY `idx_verify_reg_ref` (`reg_id`,`ref_id`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=18 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='校验码';

-- Dumping data for table sf_verify.verify_code: ~16 rows (approximately)
/*!40000 ALTER TABLE `verify_code` DISABLE KEYS */;
INSERT INTO `verify_code` (`id`, `reg_id`, `ref_id`, `level`, `code`, `expires_at`, `used_at`, `ct`) VALUES
	(1, 1, 1, 3, '712940', 1774444084574, 1774443501111, 1774443484574),
	(3, 1, 0, 1, '712827', 1775020911249, 1775020343427, 1775020311249),
	(4, 1, 12345, 1, '598769', 1775023029389, 1775022471172, 1775022429389),
	(5, 1, 2, 3, '864783', 1775119902660, 1775119458031, 1775119302660),
	(6, 1, 3, 3, '466228', 1775125141258, 1775124612083, 1775124541258),
	(7, 1, 4, 3, '977368', 1775129739533, 1775129189406, 1775129139533),
	(8, 1, 5, 3, '121636', 1775300902950, 0, 1775300302950),
	(9, 1, 6, 3, '111531', 1775302708653, 0, 1775302108653),
	(10, 1, 7, 3, '299632', 1775303130046, 1775302553549, 1775302530046),
	(11, 1, 8, 3, '762764', 1775303727265, 0, 1775303127265),
	(12, 1, 9, 3, '548688', 1775303754240, 1775303168516, 1775303154241),
	(13, 1, 10, 3, '417042', 1775308559412, 0, 1775308259412),
	(14, 1, 11, 3, '960880', 1775361870633, 1775361609504, 1775361570633),
	(15, 1, 12, 3, '240168', 1775362034419, 1775361782375, 1775361734419),
	(16, 1, 13, 3, '089807', 1775363061165, 0, 1775362761165),
	(17, 1, 14, 3, '589287', 1775364899437, 1775364634314, 1775364599437);
/*!40000 ALTER TABLE `verify_code` ENABLE KEYS */;

-- Dumping structure for table sf_verify.verify_log
CREATE TABLE IF NOT EXISTS `verify_log` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `reg_id` bigint(20) unsigned NOT NULL DEFAULT '0',
  `ref_id` bigint(20) NOT NULL DEFAULT '0',
  `code_id` bigint(20) unsigned DEFAULT '0',
  `level` smallint(6) NOT NULL DEFAULT '0',
  `action` smallint(6) NOT NULL DEFAULT '0',
  `ok` smallint(6) NOT NULL DEFAULT '1',
  `message` varchar(512) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `ct` bigint(20) unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  KEY `idx_verify_log_code` (`code_id`) USING BTREE,
  KEY `idx_verify_log_reg_ref` (`reg_id`,`ref_id`) USING BTREE
) ENGINE=MyISAM AUTO_INCREMENT=30 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='校验历史';

-- Dumping data for table sf_verify.verify_log: 29 rows
/*!40000 ALTER TABLE `verify_log` DISABLE KEYS */;
INSERT INTO `verify_log` (`id`, `reg_id`, `ref_id`, `code_id`, `level`, `action`, `ok`, `message`, `ct`) VALUES
	(1, 1, 0, 2, 0, 1, 1, '', 1775019587568),
	(2, 1, 0, 3, 1, 1, 1, '', 1775020311250),
	(3, 1, 0, 3, 1, 2, 0, 'invalid or expired verify code', 1775020322595),
	(4, 1, 0, 3, 1, 2, 1, '', 1775020343428),
	(5, 1, 0, 3, 1, 2, 0, 'invalid or expired verify code', 1775020381738),
	(6, 1, 12345, 4, 1, 1, 1, '', 1775022429391),
	(7, 1, 12345, 4, 1, 2, 1, '', 1775022471173),
	(8, 1, 2, 5, 3, 1, 1, '', 1775119302664),
	(9, 1, 2, 5, 3, 2, 1, '', 1775119458034),
	(10, 1, 3, 6, 3, 1, 1, '', 1775124541259),
	(11, 1, 3, 6, 3, 2, 1, '', 1775124612085),
	(12, 1, 4, 7, 3, 1, 1, '', 1775129139535),
	(13, 1, 4, 7, 3, 2, 1, '', 1775129189408),
	(14, 1, 5, 8, 3, 1, 1, '', 1775300302952),
	(15, 1, 6, 9, 3, 1, 1, '', 1775302108655),
	(16, 1, 7, 10, 3, 1, 1, '', 1775302530047),
	(17, 1, 7, 10, 3, 2, 1, '', 1775302553550),
	(18, 1, 8, 11, 3, 1, 1, '', 1775303127266),
	(19, 1, 9, 12, 3, 1, 1, '', 1775303154241),
	(20, 1, 9, 12, 3, 2, 1, '', 1775303168517),
	(21, 1, 10, 13, 3, 1, 1, '', 1775308259414),
	(22, 1, 10, 13, 3, 2, 0, 'wrong verify code', 1775308272173),
	(23, 1, 11, 14, 3, 1, 1, '', 1775361570634),
	(24, 1, 11, 14, 3, 2, 1, '', 1775361609506),
	(25, 1, 12, 15, 3, 1, 1, '', 1775361734420),
	(26, 1, 12, 15, 3, 2, 1, '', 1775361782376),
	(27, 1, 13, 16, 3, 1, 1, '', 1775362761166),
	(28, 1, 14, 17, 3, 1, 1, '', 1775364599438),
	(29, 1, 14, 17, 3, 2, 1, '', 1775364634314);
/*!40000 ALTER TABLE `verify_log` ENABLE KEYS */;

/*!40101 SET SQL_MODE=IFNULL(@OLD_SQL_MODE, '') */;
/*!40014 SET FOREIGN_KEY_CHECKS=IFNULL(@OLD_FOREIGN_KEY_CHECKS, 1) */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40111 SET SQL_NOTES=IFNULL(@OLD_SQL_NOTES, 1) */;
