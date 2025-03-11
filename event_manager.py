# core/event_manager.py
class EventManager:
    """مدیریت رویدادهای سیستم"""
    
    def __init__(self, logger):
        self.logger = logger
        self.subscribers = {}
        
    def subscribe(self, event_type, callback):
        """اشتراک در یک رویداد"""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)
        self.logger.debug(f"Subscribed to event: {event_type}")
        
    def unsubscribe(self, event_type, callback):
        """لغو اشتراک از یک رویداد"""
        if event_type in self.subscribers and callback in self.subscribers[event_type]:
            self.subscribers[event_type].remove(callback)
            self.logger.debug(f"Unsubscribed from event: {event_type}")
            
    def emit(self, event_type, **data):
        """انتشار یک رویداد"""
        self.logger.debug(f"Emitting event: {event_type}")
        if event_type in self.subscribers:
            for callback in self.subscribers[event_type]:
                try:
                    callback(data)
                except Exception as e:
                    self.logger.error(f"Error in event handler for {event_type}: {str(e)}")

# core/plugin_manager.py
class PluginManager:
    """مدیریت پلاگین‌های سیستم"""
    
    def __init__(self, app):
        self.app = app
        self.logger = app.logger
        self.plugins = {}
        
    def register_plugin(self, plugin_name, plugin_class):
        """ثبت یک پلاگین جدید"""
        if plugin_name in self.plugins:
            self.logger.warning(f"Plugin {plugin_name} is already registered")
            return False
            
        try:
            # ایجاد نمونه پلاگین
            plugin_instance = plugin_class(self.app)
            self.plugins[plugin_name] = plugin_instance
            self.logger.info(f"Plugin {plugin_name} registered successfully")
            return True
        except Exception as e:
            self.logger.error(f"Error registering plugin {plugin_name}: {str(e)}")
            return False
    
    def initialize_plugins(self):
        """راه‌اندازی همه پلاگین‌های ثبت شده"""
        for name, plugin in self.plugins.items():
            try:
                plugin.initialize()
                self.logger.info(f"Plugin {name} initialized")
            except Exception as e:
                self.logger.error(f"Error initializing plugin {name}: {str(e)}")
    
    def get_plugin(self, plugin_name):
        """دریافت یک پلاگین با نام آن"""
        return self.plugins.get(plugin_name)
    
    def shutdown_plugins(self):
        """توقف همه پلاگین‌ها"""
        for name, plugin in self.plugins.items():
            try:
                plugin.shutdown()
                self.logger.info(f"Plugin {name} shutdown successfully")
            except Exception as e:
                self.logger.error(f"Error shutting down plugin {name}: {str(e)}")
    
    def execute_hooks(self, hook_name, *args, **kwargs):
        """اجرای هوک‌ها در تمام پلاگین‌ها"""
        results = {}
        for name, plugin in self.plugins.items():
            hook_method = getattr(plugin, hook_name, None)
            if hook_method and callable(hook_method):
                try:
                    result = hook_method(*args, **kwargs)
                    results[name] = result
                except Exception as e:
                    self.logger.error(f"Error executing hook {hook_name} in plugin {name}: {str(e)}")
        return results