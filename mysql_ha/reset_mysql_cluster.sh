#!/usr/bin/env bash
set -euo pipefail

# ----------------------------
# 配置（按需修改）
ROOT_PASS="${MYSQL_ROOT_PASSWORD:-root_pass}"   # 默认和你 compose 一致
MONITOR_PASS="${MONITOR_PASS:-monitor}"        # 要给 monitor 用的密码（proxy 配置里要一致）
# 如果你的 compose 服务名不是下面这些，请改这里
MYSQL_SERVICES=("master" "replica1" "replica2")
PROXYSQL_SERVICE="proxysql"
BOOTSTRAP_SERVICE="bootstrap"
# 匹配卷名时使用的关键字（安全删除只删除匹配这些关键字的卷）
VOLUME_PATTERNS="master_data|replica1_data|replica2_data|proxysql_data|mysql-ha_master_data|mysql-ha_replica1_data|mysql-ha_replica2_data|mysql-ha_proxysql_data"
# ----------------------------

echo "=== Step 1: 停止并删除 compose 定义的容器/网络/匿名卷 ==="
docker compose down -v --remove-orphans

echo "=== Step 2: 强制移除残留同名容器（若有） ==="
for svc in "${MYSQL_SERVICES[@]}" "$PROXYSQL_SERVICE" "$BOOTSTRAP_SERVICE"; do
  if docker ps -a --format '{{.Names}}' | grep -q "^${svc}$"; then
    echo "  - removing container ${svc}"
    docker rm -f "${svc}" >/dev/null 2>&1 || true
  fi
done

echo "=== Step 3: 删除与本项目相关的命名卷（按模式匹配，谨慎） ==="
mapfile -t to_delete < <(docker volume ls --format '{{.Name}}' | grep -E "${VOLUME_PATTERNS}" || true)
if [ ${#to_delete[@]} -gt 0 ]; then
  for v in "${to_delete[@]}"; do
    echo "  - docker volume rm ${v}"
    docker volume rm "${v}" >/dev/null || true
  done
else
  echo "  - 未发现匹配的命名卷，跳过"
fi

echo "=== Step 4: 启动 MySQL 节点（不启动 proxysql/bootstrap） ==="
# 先把 mysql 节点单独起，避免 proxysql 太早探测
docker compose up -d "${MYSQL_SERVICES[@]}"

# 等待每个 MySQL 服务 ready
wait_for_ready() {
  local svc="$1"
  echo "Waiting ${svc} to be ready..."

  # 暂时放宽严格模式，避免 ping 失败立即中断
  set +e +o pipefail

  local try=0 rc=0
  while :; do
    ((try++))

    # 直接在容器内用 mysqladmin ping
    docker exec "$svc" \
      mysqladmin -uroot -p"${ROOT_PASS}" --connect-timeout=2 --wait=2 ping >/dev/null 2>&1

    if [ $? -eq 0 ]; then
      echo "  -> ${svc} mysqld is alive"
      rc=0; break
    fi

    if [ $try -gt 120 ]; then
      echo "ERROR: ${svc} not ready after $try attempts"
      docker logs "$svc" --tail 100 || true
      rc=1; break
    fi
    sleep 2
  done

  # 恢复严格模式
  set -euo pipefail
  return $rc
}


for s in "${MYSQL_SERVICES[@]}"; do
  wait_for_ready "$s"
done

echo "=== Step 5: 检查并同步 monitor 账号（确保 ProxySQL 可用监控） ==="

# 函数：从节点查询 monitor 的 plugin/authentication_string 信息
get_monitor_info() {
  local node="$1"
  docker exec -i "$node" mysql -uroot -p"${ROOT_PASS}" -N -s -e \
    "SELECT CONCAT(host,CHAR(9),plugin,CHAR(9),IFNULL(authentication_string,'')) FROM mysql.user WHERE user='monitor';" 2>/dev/null || true
}

# 收集所有节点的 monitor 信息
declare -A info_map
missing=false
for s in "${MYSQL_SERVICES[@]}"; do
  echo "Checking monitor on ${s}..."
  out=$(get_monitor_info "$s")
  if [ -z "$out" ]; then
    echo "  -> monitor 不存在于 ${s}"
    missing=true
  else
    echo "  -> monitor 行(s):"
    echo "$out" | sed 's/^/     /'
    info_map["$s"]="$out"
  fi
done

# 如果有缺失或不同步（authentication_string 不一致），则统一重建/修改为 MONITOR_PASS
need_fix=false
if $missing; then
  need_fix=true
else
  # 比较各节点的 authentication_string（取第一列的哈希）
  base_hash=""
  for s in "${MYSQL_SERVICES[@]}"; do
    row="${info_map[$s]}"
    # 可能有多行 host，不同 host 行要比对所有 authentication_string
    while IFS= read -r line; do
      # line 格式 host \t plugin \t auth
      auth=$(echo "$line" | awk -F $'\t' '{print $3}')
      if [ -z "$base_hash" ]; then base_hash="$auth"; fi
      if [ "$auth" != "$base_hash" ]; then
        need_fix=true
        break 2
      fi
    done <<<"$row"
  done
fi

if $need_fix; then
  echo "需要修复 monitor 账号（创建或修改密码），将统一设置密码为: ${MONITOR_PASS}"
  for s in "${MYSQL_SERVICES[@]}"; do
    echo "  -> 在 ${s} 上创建/修改 monitor ..."
    docker exec -i "$s" mysql -uroot -p"${ROOT_PASS}" -e "
      CREATE USER IF NOT EXISTS 'monitor'@'%' IDENTIFIED WITH mysql_native_password BY '${MONITOR_PASS}';
      ALTER USER 'monitor'@'%' IDENTIFIED WITH mysql_native_password BY '${MONITOR_PASS}';
      GRANT SELECT, PROCESS, REPLICATION CLIENT ON *.* TO 'monitor'@'%';
      FLUSH PRIVILEGES;
    " || true
  done
else
  echo "monitor 在各节点中一致，无需修改"
fi

echo "=== Step 6: 启动 ProxySQL 与 bootstrap 服务 ==="
docker compose up -d "${PROXYSQL_SERVICE}" "${BOOTSTRAP_SERVICE}"

echo "等待 bootstrap 运行结束（bootstrap 会配置半同步、replication、并保存 proxysql 配置）..."
# 等 bootstrap 完成（bootstrap 脚本里会输出 done 字样），最多等待 5 分钟
boot_try=0
while true; do
  ((boot_try++))
  status=$(docker ps -a --filter name="^${BOOTSTRAP_SERVICE}$" --format '{{.Status}}' || true)
  if echo "$status" | grep -q "Exited (0)"; then
    echo "bootstrap 已成功退出（初始化完成）"
    break
  fi
  if echo "$status" | grep -q "Up"; then
    # 输出最近日志跟踪
    docker logs --tail 50 "${BOOTSTRAP_SERVICE}" || true
  fi
  if [ $boot_try -gt 150 ]; then
    echo "ERROR: bootstrap 未在超时时间内完成，请查看 logs： docker logs ${BOOTSTRAP_SERVICE}"
    exit 1
  fi
  sleep 2
done

echo "=== Step 7: 最后检查 ProxySQL 后端状态 ==="
docker exec -it "${PROXYSQL_SERVICE}" mysql -uadmin -padmin -h127.0.0.1 -P6032 -e "SELECT hostgroup_id,hostname,port,status FROM runtime_mysql_servers;" || true
echo "=== 全流程完成 ✅ ==="

