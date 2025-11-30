#!/usr/bin/env bash
set -euo pipefail

MASTER_HOST="master"
REPLS=("replica1" "replica2")
ROOT_PWD="root_pass"
REPL_USER="repl"
REPL_PWD="repl_pass"

ADMIN_USER="admin"
ADMIN_PWD="admin"
PROXY_HOST="proxysql"
PROXY_ADMIN_PORT=6032

mysql_cli() { mysql -h "$1" -uroot -p"$ROOT_PWD" -e "$2" ; }
mysql_wait() {
  local host=$1; local tries=60
  until mysqladmin ping -h "$host" -proot_pass >/dev/null 2>&1; do
    tries=$((tries-1)); [ $tries -le 0 ] && { echo "wait $host timeout"; exit 1; }
    sleep 2
  done
}

echo "[bootstrap] waiting for MySQL nodes..."
mysql_wait "$MASTER_HOST"
for r in "${REPLS[@]}"; do mysql_wait "$r"; done

echo "[bootstrap] enable semi-sync on MASTER (idempotent)"
# 安装插件（已装会报错，忽略即可）
set +e
mysql_cli "$MASTER_HOST" "INSTALL PLUGIN rpl_semi_sync_source SONAME 'semisync_source.so';"
set -e
mysql_cli "$MASTER_HOST" "
SET PERSIST rpl_semi_sync_source_enabled=ON;
SET PERSIST rpl_semi_sync_source_timeout=1000;
SET PERSIST rpl_semi_sync_source_wait_for_replica_count=1;
"

echo "[bootstrap] configure replicas (semi-sync + replication + read-only)"
for r in "${REPLS[@]}"; do
  echo "  -> $r"
  set +e
  mysql_cli "$r" "INSTALL PLUGIN rpl_semi_sync_replica SONAME 'semisync_replica.so';"
  set -e
  mysql_cli "$r" "
    SET PERSIST rpl_semi_sync_replica_enabled=ON;
    STOP REPLICA;
    CHANGE REPLICATION SOURCE TO
      SOURCE_HOST='${MASTER_HOST}', SOURCE_PORT=3306,
      SOURCE_USER='${REPL_USER}', SOURCE_PASSWORD='${REPL_PWD}',
      SOURCE_AUTO_POSITION=1;
    START REPLICA;
    SET PERSIST read_only=ON;
    SET PERSIST super_read_only=ON;
    STOP REPLICA IO_THREAD; START REPLICA IO_THREAD;
  "
done

echo "[bootstrap] wait for ProxySQL admin and load/save runtime"
# 等 ProxySQL Admin 可用
tries=60
until mysql -h "$PROXY_HOST" -u"$ADMIN_USER" -p"$ADMIN_PWD" -P"$PROXY_ADMIN_PORT" -e "SELECT 1;" >/dev/null 2>&1; do
  tries=$((tries-1)); [ $tries -le 0 ] && { echo "wait proxysql timeout"; exit 1; }
  sleep 2
done

mysql -h "$PROXY_HOST" -u"$ADMIN_USER" -p"$ADMIN_PWD" -P"$PROXY_ADMIN_PORT" -e "LOAD MYSQL VARIABLES TO RUNTIME; SAVE MYSQL VARIABLES TO DISK;"
mysql -h "$PROXY_HOST" -u"$ADMIN_USER" -p"$ADMIN_PWD" -P"$PROXY_ADMIN_PORT" -e "LOAD MYSQL SERVERS TO RUNTIME;  SAVE MYSQL SERVERS TO DISK;"
mysql -h "$PROXY_HOST" -u"$ADMIN_USER" -p"$ADMIN_PWD" -P"$PROXY_ADMIN_PORT" -e "LOAD MYSQL USERS TO RUNTIME;    SAVE MYSQL USERS TO DISK;"
mysql -h "$PROXY_HOST" -u"$ADMIN_USER" -p"$ADMIN_PWD" -P"$PROXY_ADMIN_PORT" -e "LOAD MYSQL QUERY RULES TO RUNTIME; SAVE MYSQL QUERY RULES TO DISK;"

echo "[bootstrap] done ✅"

