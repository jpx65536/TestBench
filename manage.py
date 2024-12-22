#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
import socket

def get_local_ip():
    try:
        # 获取本机的局域网 IP 地址
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'TestBench.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    print(f"Local server address: http://{get_local_ip()}:8000/")
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
