CREATE TABLE `event` (
	`id` BIGINT(20) UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'primary key id',
	`event_type` VARCHAR(50) NOT NULL DEFAULT '' COMMENT 'event type',
	`event_time` BIGINT(20) UNSIGNED NOT NULL DEFAULT '0' COMMENT 'event occurrence time',
	`message` TEXT NOT NULL COMMENT 'event message',
	`detail` TEXT NOT NULL COMMENT 'detailed information (JSON format)',
	`dcid` INT(10) UNSIGNED NOT NULL DEFAULT '0' COMMENT 'datacenter id',
	`mid` INT(10) UNSIGNED NOT NULL DEFAULT '0' COMMENT 'machine id',
	`ct` BIGINT(20) UNSIGNED NOT NULL DEFAULT '0' COMMENT 'creation time, UNIX timestamp in ms',
	PRIMARY KEY (`id`) USING BTREE
)
COMMENT='event log'
COLLATE='utf8mb4_unicode_ci'
ENGINE=InnoDB;

-- Restart counter table
CREATE TABLE `recounter` (
	`id` BIGINT(20) UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'primary key id',
	`dcid` INT(10) UNSIGNED NOT NULL DEFAULT '0' COMMENT 'datacenter id (0-3)',
	`mid` INT(10) UNSIGNED NOT NULL DEFAULT '0' COMMENT 'machine id (0-7)',
	`rc` INT(10) UNSIGNED NOT NULL DEFAULT '0' COMMENT 're-counter (0-3)',
	`ct` BIGINT(20) UNSIGNED NOT NULL DEFAULT '0' COMMENT 'create time, UNIX timestamp in ms',
	`ut` BIGINT(20) NULL DEFAULT '0' COMMENT 'update time, UNIX timestamp in ms',
	PRIMARY KEY (`id`) USING BTREE,
	UNIQUE INDEX `uni_dc_mac_biz` (`dcid`, `mid`, `bid`) USING BTREE
)
COMMENT='re-counter for restart/clockback'
COLLATE='utf8mb4_unicode_ci'
ENGINE=InnoDB;


-- Create indexes (if table already exists, execute separately)
-- Note: MySQL 5.7 does not support IF NOT EXISTS, need to manually check or use stored procedures
-- If index already exists, execution will error, can be ignored
-- 
-- CREATE INDEX idx_event_type ON events(event_type);
-- CREATE INDEX idx_event_time ON events(event_time);
-- CREATE INDEX idx_datacenter_machine ON events(datacenter_id, machine_id);
-- CREATE INDEX idx_created_at ON events(created_at);

-- Query examples
-- Query last 100 events
-- SELECT * FROM events ORDER BY event_time DESC LIMIT 100;

-- Query events of specified type
-- SELECT * FROM events WHERE event_type = 'CLOCK_BACKWARD' ORDER BY event_time DESC LIMIT 100;

-- Query count of clock backward events in last 24 hours
-- SELECT COUNT(*) FROM events 
-- WHERE event_type = 'CLOCK_BACKWARD' 
-- AND event_time >= DATE_SUB(NOW(), INTERVAL 24 HOUR);

-- Query count of clock backward events in last 7 days
-- SELECT COUNT(*) FROM events 
-- WHERE event_type = 'CLOCK_BACKWARD' 
-- AND event_time >= DATE_SUB(NOW(), INTERVAL 7 DAY);

-- Statistics of event count by date
-- SELECT DATE(event_time) as date, event_type, COUNT(*) as count
-- FROM events
-- WHERE event_time >= DATE_SUB(NOW(), INTERVAL 30 DAY)
-- GROUP BY DATE(event_time), event_type
-- ORDER BY date DESC;

-- Query restart counter for specific instance
-- SELECT * FROM restart_counters 
-- WHERE datacenter_id = 1 AND machine_id = 2 AND business_id = 0;

-- Query all restart counters
-- SELECT * FROM restart_counters ORDER BY last_updated DESC;

-- Query restart counter update events
-- SELECT * FROM event 
-- WHERE event_type = 'RESTART_COUNTER_UPDATE' 
-- ORDER BY event_time DESC LIMIT 100;
