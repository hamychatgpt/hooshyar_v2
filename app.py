# core/app.py
import os
import signal
import atexit
from datetime import datetime

from core.config import Config
from core.logger import Logger
from core.db import Database
from core.plugin_manager import PluginManager
from core.event_manager import EventManager

class TwitterMonitorApp:
    """کلاس اصلی اپلیکیشن"""
    
    def __init__(self, config_path='config.ini'):
        # بارگذاری تنظیمات
        self.config = Config(config_path)
        
        # راه‌اندازی سیستم لاگینگ
        log_level = self.config.get('DEFAULT', 'LOG_LEVEL', 'INFO')
        self.logger = Logger('twitter_monitor', log_level).logger
        
        self.logger.info("Starting Twitter Monitor App")
        
        # راه‌اندازی اتصال به دیتابیس
        db_path = self.config.get('DEFAULT', 'DB_PATH', 'data/twitter_monitor.db')
        self.db = Database(db_path)
        self.db.connect()
        
        # راه‌اندازی مدیر رویداد
        self.event_manager = EventManager(self.logger)
        
        # راه‌اندازی مدیر پلاگین
        self.plugin_manager = PluginManager(self)
        
        # ثبت مدیریت خاتمه اپلیکیشن
        atexit.register(self.shutdown)
        signal.signal(signal.SIGINT, self._handle_interrupt)
        signal.signal(signal.SIGTERM, self._handle_interrupt)
        
        self.start_time = datetime.now()
        self.logger.info("Twitter Monitor App initialized")
    
    def run(self):
        """اجرای اپلیکیشن"""
        self.logger.info("Running app...")
        
        # راه‌اندازی پلاگین‌ها
        self.plugin_manager.initialize_plugins()
        
        # اطلاع‌رسانی راه‌اندازی موفق
        self.event_manager.emit('app_started')
        
        # در اینجا می‌توان حلقه اصلی اپلیکیشن را اجرا کرد
        # برای مثال، یک وب‌سرور یا سیستم زمان‌بندی
        
        return True
    
    def shutdown(self):
        """توقف اپلیکیشن"""
        self.logger.info("Shutting down app...")
        
        # اطلاع‌رسانی توقف
        self.event_manager.emit('app_stopping')
        
        # توقف پلاگین‌ها
        self.plugin_manager.shutdown_plugins()
        
        # بستن اتصال دیتابیس
        self.db.close()
        
        uptime = datetime.now() - self.start_time
        self.logger.info(f"App shutdown complete. Uptime: {uptime}")
    
    def _handle_interrupt(self, signum, frame):
        """مدیریت سیگنال‌های پایان برنامه"""
        self.logger.info(f"Received signal {signum}. Initiating shutdown...")
        self.shutdown()
        exit(0)