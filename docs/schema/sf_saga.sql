-- sf_saga schema for app_saga (linear HTTP saga orchestration).
-- Apply manually; Django models use Meta.managed = False.
-- Flows are identified by flow.id together with caller access_key.
-- Participant registry table name is ``reg`` (Django model SagaParticipant).

CREATE TABLE IF NOT EXISTS reg (
  id BIGINT NOT NULL AUTO_INCREMENT,
  access_key VARCHAR(128) NOT NULL,
  name VARCHAR(255) NOT NULL DEFAULT '',
  status SMALLINT NOT NULL,
  ct BIGINT UNSIGNED NOT NULL DEFAULT 0,
  ut BIGINT UNSIGNED NOT NULL DEFAULT 0,
  PRIMARY KEY (id),
  UNIQUE KEY reg_access_key_uq (access_key),
  KEY reg_status_idx (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS flow (
  id BIGINT NOT NULL AUTO_INCREMENT,
  rid BIGINT NOT NULL,
  name VARCHAR(255) NOT NULL DEFAULT '',
  status SMALLINT NOT NULL,
  ct BIGINT UNSIGNED NOT NULL DEFAULT 0,
  ut BIGINT UNSIGNED NOT NULL DEFAULT 0,
  PRIMARY KEY (id),
  KEY flow_reg_idx (rid),
  CONSTRAINT flow_reg_fk FOREIGN KEY (rid) REFERENCES reg (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS flow_step (
  id BIGINT NOT NULL AUTO_INCREMENT,
  fid BIGINT NOT NULL,
  step_index INT UNSIGNED NOT NULL,
  name VARCHAR(255) NOT NULL DEFAULT '',
  action_url VARCHAR(2048) NOT NULL,
  compensate_url VARCHAR(2048) NOT NULL,
  timeout_sec INT UNSIGNED NOT NULL DEFAULT 30,
  max_retries INT UNSIGNED NOT NULL DEFAULT 10,
  ct BIGINT UNSIGNED NOT NULL DEFAULT 0,
  ut BIGINT UNSIGNED NOT NULL DEFAULT 0,
  PRIMARY KEY (id),
  UNIQUE KEY flow_step_fid_step_uq (fid, step_index),
  KEY flow_step_fid_idx (fid),
  CONSTRAINT flow_step_flow_fk FOREIGN KEY (fid) REFERENCES flow (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `instance` (
  id BIGINT NOT NULL AUTO_INCREMENT,
  fid BIGINT NOT NULL,
  rid BIGINT NOT NULL,
  status SMALLINT NOT NULL,
  idem_key BIGINT NOT NULL,
  context LONGTEXT NOT NULL,
  step_payloads LONGTEXT NOT NULL,
  current_step_index INT NOT NULL DEFAULT 0,
  next_retry_at BIGINT NOT NULL,
  retry_count INT UNSIGNED NOT NULL DEFAULT 0,
  last_error LONGTEXT NOT NULL,
  ct BIGINT UNSIGNED NOT NULL DEFAULT 0,
  ut BIGINT UNSIGNED NOT NULL DEFAULT 0,
  PRIMARY KEY (id),
  UNIQUE KEY instance_idem_uq (idem_key),
  KEY instance_fid_idx (fid),
  KEY instance_status_retry_idx (status, next_retry_at),
  CONSTRAINT instance_flow_fk FOREIGN KEY (fid) REFERENCES flow (id) ON DELETE CASCADE,
  CONSTRAINT instance_reg_fk FOREIGN KEY (rid) REFERENCES reg (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS step_run (
  id BIGINT NOT NULL AUTO_INCREMENT,
  ins_id BIGINT NOT NULL,
  fsid BIGINT NOT NULL,
  step_index INT UNSIGNED NOT NULL,
  action_status SMALLINT NOT NULL,
  compensate_status SMALLINT NOT NULL,
  last_http_status_action SMALLINT UNSIGNED NULL,
  last_http_status_compensate SMALLINT UNSIGNED NULL,
  last_error_action LONGTEXT NOT NULL,
  last_error_compensate LONGTEXT NOT NULL,
  ct BIGINT UNSIGNED NOT NULL DEFAULT 0,
  ut BIGINT UNSIGNED NOT NULL DEFAULT 0,
  PRIMARY KEY (id),
  UNIQUE KEY step_run_ins_step_uq (ins_id, step_index),
  KEY step_run_ins_idx (ins_id),
  CONSTRAINT step_run_instance_fk FOREIGN KEY (ins_id) REFERENCES `instance` (id) ON DELETE CASCADE,
  CONSTRAINT step_run_flow_step_fk FOREIGN KEY (fsid) REFERENCES flow_step (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------------
-- Existing database: rename saga_* tables -> flow, flow_step, instance, step_run
-- (Adjust constraint names if yours differ; use SHOW CREATE TABLE first.)
-- ---------------------------------------------------------------------------
-- ALTER TABLE saga_step_run DROP FOREIGN KEY saga_step_run_instance_fk;
-- ALTER TABLE saga_step_run DROP FOREIGN KEY saga_step_run_flow_step_fk;
-- ALTER TABLE saga_flow_step DROP FOREIGN KEY saga_flow_step_flow_fk;
-- ALTER TABLE saga_instance DROP FOREIGN KEY saga_instance_flow_fk;
-- ALTER TABLE saga_instance DROP FOREIGN KEY saga_instance_reg_fk;
-- RENAME TABLE saga_flow TO flow;
-- RENAME TABLE saga_flow_step TO flow_step;
-- RENAME TABLE saga_instance TO `instance`;
-- RENAME TABLE saga_step_run TO step_run;
-- ALTER TABLE flow_step ADD CONSTRAINT flow_step_flow_fk FOREIGN KEY (fid) REFERENCES flow (id) ON DELETE CASCADE;
-- ALTER TABLE `instance` ADD CONSTRAINT instance_flow_fk FOREIGN KEY (fid) REFERENCES flow (id) ON DELETE CASCADE;
-- ALTER TABLE `instance` ADD CONSTRAINT instance_reg_fk FOREIGN KEY (rid) REFERENCES reg (id) ON DELETE CASCADE;
-- ALTER TABLE step_run ADD CONSTRAINT step_run_instance_fk FOREIGN KEY (ins_id) REFERENCES `instance` (id) ON DELETE CASCADE;
-- ALTER TABLE step_run ADD CONSTRAINT step_run_flow_step_fk FOREIGN KEY (fsid) REFERENCES flow_step (id) ON DELETE CASCADE;
-- Optional: rename indexes to match new names (MySQL 8+ RENAME INDEX or drop/add).

-- ---------------------------------------------------------------------------
-- Legacy migration notes (older schema steps; table names may already differ)
-- ---------------------------------------------------------------------------
-- ALTER TABLE saga_flow DROP INDEX saga_flow_participant_flow_uq;
-- ALTER TABLE saga_flow DROP COLUMN flow_key;
-- (See project history for flow_id/fid, participant_id/pid/rid, ins_id, fsid, reg rename.)
