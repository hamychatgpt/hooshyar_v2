# core/logger.py
import logging
import os
from logging.handlers import RotatingFileHandler

class Logger:
    """کلاس مدیریت لاگینگ"""
    
    def __init__(self, name, log_level='INFO', log_file='logs/app.log'):
        self.logger = logging.getLogger(name)
        
        # تنظیم سطح لاگینگ
        level = getattr(logging, log_level.upper(), logging.INFO)
        self.logger.setLevel(level)
        
        # ایجاد فرمت لاگ
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # اطمینان از وجود دایرکتوری لاگ
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        # افزودن handler فایل
        file_handler = RotatingFileHandler(
            log_file, maxBytes=10*1024*1024, backupCount=5
        )
        file_handler.setFormatter(formatter)
        
        # افزودن handler کنسول
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        
        # افزودن handlers به logger
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def debug(self, message):
        self.logger.debug(message)
    
    def info(self, message):
        self.logger.info(message)
    
    def warning(self, message):
        self.logger.warning(message)
    
    def error(self, message):
        self.logger.error(message)
    
    def critical(self, message):
        self.logger.critical(message)