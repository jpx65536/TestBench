#!/bin/bash

# 获取本机 IP 地址
IP_ADDRESS=$(hostname -I | awk '{print $1}')

# 打印本机地址
echo "Local server address: http://$IP_ADDRESS:8000/"

# 启动 Django 开发服务器，监听 0.0.0.0，允许外部访问
python3 manage.py runserver 0.0.0.0:8000