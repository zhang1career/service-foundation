-- app_tcc: `tx` 全局限等键 `idem_key` 仍为 BIGINT（Snowflake）。
-- `tx_branch.idem_key` 改为定长/变长字符串，存 `{X-Request-Id 或 str(tx 的 snowflake idem)}-{branch_index}`，
-- 与协调器发向参与者的 JSON `idempotency_key` 与 HTTP 头 `X-Request-Id` 一致。
-- 已有 BIGINT 行在 MySQL 8 中 MODIFY 为 VARCHAR 时会做隐式数字到字符串的转换；部署前请在预发核对。

ALTER TABLE `tx_branch`
  MODIFY COLUMN `idem_key` VARCHAR(256) NOT NULL;
