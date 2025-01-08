# 使用官方 Python 镜像
FROM python:latest

# 设置工作目录
WORKDIR /app

# 复制项目中的依赖文件（requirements.txt 和 start.sh）
COPY requirements.txt /app/
COPY start.sh /app/

# 安装 Python 依赖包
RUN pip install --no-cache-dir -r requirements.txt --find-links=/root/.cache/pip

# 复制整个 Django 项目到容器中
COPY . /app/

# 给 start.sh 脚本添加执行权限
RUN chmod +x /app/start.sh

# 暴露 Django 默认运行的端口
EXPOSE 8000

# 运行 start.sh 脚本启动服务
CMD ["sh", "/app/start.sh"]
