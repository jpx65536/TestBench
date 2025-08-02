#!/bin/bash

# 获取本机 IP 地址
IP_ADDRESS=$(hostname -I | awk '{print $1}')

# 打印本机地址
echo "Local server address: http://$IP_ADDRESS:8000/"

# 查看是否有残留manage进程
EXISTING_PIDS=$(pgrep -f "manage\.py runserver")

if [ -n "$EXISTING_PIDS" ]; then
    echo "发现已有 Django runserver 进程，强制终止（-9）：$EXISTING_PIDS"
    echo "$EXISTING_PIDS" | xargs -r kill -9
else
    echo "未检测到已有 Django runserver 进程。"
fi

# 启动 Django 开发服务器，监听 0.0.0.0，允许外部访问
nohup python3 manage.py runserver 0.0.0.0:8000 &>/dev/null &