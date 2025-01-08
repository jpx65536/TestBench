import os
from datetime import datetime
from logging.handlers import RotatingFileHandler

class CustomRotatingFileHandler(RotatingFileHandler):
    def __init__(self, base_name, log_dir, *args, **kwargs):
        self.base_name = base_name
        self.log_dir = log_dir
        super().__init__(self._get_log_filename(), *args, **kwargs)

    def _get_log_filename(self):
        """动态生成日志文件名，精确到分钟"""
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M')  # 当前时间戳（精确到分钟）
        return os.path.join(self.log_dir, f"{self.base_name}_{timestamp}.log")

    def doRollover(self):
        """在日志轮转时更新文件名"""
        self.stream.close()
        self.baseFilename = self._get_log_filename()
        self.stream = self._open()