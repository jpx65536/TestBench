-- 业务库与账号
CREATE DATABASE IF NOT EXISTS appdb;

CREATE USER IF NOT EXISTS 'appuser'@'%' IDENTIFIED WITH mysql_native_password BY 'app_pass';
GRANT ALL PRIVILEGES ON appdb.* TO 'appuser'@'%';

-- 复制账号（9.x 可用的新权限名 REPLICATION REPLICA；旧名 REPLICATION SLAVE 也兼容）
CREATE USER IF NOT EXISTS 'repl'@'%' IDENTIFIED WITH mysql_native_password BY 'repl_pass';
GRANT REPLICATION SLAVE ON *.* TO 'repl'@'%';

-- ProxySQL 监控账号
CREATE USER IF NOT EXISTS 'monitor'@'%' IDENTIFIED WITH mysql_native_password BY 'monitor';
GRANT SELECT, PROCESS, REPLICATION CLIENT ON *.* TO 'monitor'@'%';

FLUSH PRIVILEGES;

