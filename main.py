# main.py
import os
import asyncio
from core.app import TwitterMonitorApp
from migrations.create_tables import create_tables

# پلاگین‌ها
from plugins.collector.collector import CollectorPlugin
from plugins.filter.filter import FilterPlugin
from plugins.dashboard.dashboard import DashboardPlugin

def main():
    """نقطه ورود اصلی برنامه"""
    print("Starting Twitter Monitor Application...")
    
    # اطمینان از وجود دایرکتوری‌های لازم
    os.makedirs("data", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    # راه‌اندازی اپلیکیشن
    app = TwitterMonitorApp()
    
    # ایجاد جداول دیتابیس
    create_tables(app.db)
    
    # ثبت پلاگین‌ها
    app.plugin_manager.register_plugin("collector", CollectorPlugin)
    app.plugin_manager.register_plugin("filter", FilterPlugin)
    app.plugin_manager.register_plugin("dashboard", DashboardPlugin)
    
    # اجرای اپلیکیشن
    app.run()
    
    # حفظ برنامه در حال اجرا
    try:
        # این حلقه به اپلیکیشن اجازه می‌دهد که ادامه دهد
        while True:
            asyncio.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        app.shutdown()

if __name__ == "__main__":
    main()