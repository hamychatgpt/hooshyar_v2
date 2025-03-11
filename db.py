# core/db.py
import sqlite3
import os
import json
from datetime import datetime

class Database:
    """کلاس مدیریت دیتابیس SQLite"""
    
    def __init__(self, db_path):
        # اطمینان از وجود دایرکتوری دیتابیس
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        self.db_path = db_path
        self.conn = None
        self.cursor = None
    
    def connect(self):
        """اتصال به دیتابیس"""
        self.conn = sqlite3.connect(self.db_path)
        
        # تنظیم برای مدیریت تاریخ و JSON
        self.conn.row_factory = sqlite3.Row
        
        # ثبت تابع تبدیل برای JSON
        sqlite3.register_adapter(dict, json.dumps)
        sqlite3.register_adapter(list, json.dumps)
        sqlite3.register_converter("JSON", json.loads)
        
        # بهینه‌سازی SQLite
        self.execute_pragma("PRAGMA journal_mode = WAL")
        self.execute_pragma("PRAGMA synchronous = NORMAL")
        self.execute_pragma("PRAGMA cache_size = -50000")
        self.execute_pragma("PRAGMA temp_store = MEMORY")
        
        self.cursor = self.conn.cursor()
        return self.conn
    
    def execute_pragma(self, pragma_statement):
        """اجرای یک دستور PRAGMA"""
        self.conn.execute(pragma_statement)
    
    def close(self):
        """بستن اتصال دیتابیس"""
        if self.conn:
            self.conn.close()
    
    def execute(self, query, params=None):
        """اجرای یک کوئری"""
        if params is None:
            params = {}
        self.cursor.execute(query, params)
        return self.cursor
    
    def execute_many(self, query, params_list):
        """اجرای یک کوئری با چندین مجموعه پارامتر"""
        self.cursor.executemany(query, params_list)
        return self.cursor
    
    def fetch_one(self):
        """دریافت یک ردیف نتیجه"""
        return self.cursor.fetchone()
    
    def fetch_all(self):
        """دریافت همه ردیف‌های نتیجه"""
        return self.cursor.fetchall()
    
    def commit(self):
        """ثبت تغییرات"""
        self.conn.commit()
    
    def rollback(self):
        """برگرداندن تغییرات"""
        self.conn.rollback()
    
    def execute_script(self, script):
        """اجرای یک اسکریپت SQL"""
        self.conn.executescript(script)
        self.commit()
    
    def table_exists(self, table_name):
        """بررسی وجود یک جدول"""
        self.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,)
        )
        return self.fetch_one() is not None