# plugins/base_plugin.py
class BasePlugin:
    """کلاس پایه برای همه پلاگین‌ها"""
    
    def __init__(self, app):
        self.app = app
        self.db = app.db
        self.logger = app.logger
        self.config = app.config
        self.event_manager = app.event_manager
        
    def initialize(self):
        """راه‌اندازی پلاگین - باید در کلاس فرزند پیاده‌سازی شود"""
        raise NotImplementedError("Plugins must implement initialize method")
        
    def shutdown(self):
        """توقف پلاگین - باید در کلاس فرزند پیاده‌سازی شود"""
        pass