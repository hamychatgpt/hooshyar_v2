# models/base.py
class BaseModel:
    """کلاس پایه برای همه مدل‌ها"""
    
    def __init__(self, db):
        self.db = db
    
    @staticmethod
    def dict_factory(cursor, row):
        """تبدیل ردیف به دیکشنری"""
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d
    
    def to_dict(self):
        """تبدیل مدل به دیکشنری"""
        raise NotImplementedError("Subclasses must implement to_dict method")
    
    @classmethod
    def from_dict(cls, data, db=None):
        """ایجاد مدل از دیکشنری"""
        raise NotImplementedError("Subclasses must implement from_dict method")

# models/keyword.py
from datetime import datetime
from models.base import BaseModel

class Keyword(BaseModel):
    """مدل کلمه کلیدی"""
    
    TABLE_NAME = 'keywords'
    
    def __init__(self, db, id=None, text=None, is_active=True, priority=5,
                 max_tweets_per_day=1000, last_search_at=None, category=None,
                 filter_rules=None, created_at=None):
        super().__init__(db)
        self.id = id
        self.text = text
        self.is_active = is_active
        self.priority = priority
        self.max_tweets_per_day = max_tweets_per_day
        self.last_search_at = last_search_at
        self.category = category
        self.filter_rules = filter_rules or {}
        self.created_at = created_at or datetime.now()
    
    def save(self):
        """ذخیره کلمه کلیدی در دیتابیس"""
        if self.id:
            # به‌روزرسانی
            query = f"""
                UPDATE {self.TABLE_NAME}
                SET text = :text, is_active = :is_active, priority = :priority,
                    max_tweets_per_day = :max_tweets_per_day, last_search_at = :last_search_at,
                    category = :category, filter_rules = :filter_rules
                WHERE id = :id
            """
        else:
            # ایجاد جدید
            query = f"""
                INSERT INTO {self.TABLE_NAME}
                (text, is_active, priority, max_tweets_per_day, last_search_at,
                 category, filter_rules, created_at)
                VALUES
                (:text, :is_active, :priority, :max_tweets_per_day, :last_search_at,
                 :category, :filter_rules, :created_at)
            """
        
        params = {
            'id': self.id,
            'text': self.text,
            'is_active': 1 if self.is_active else 0,
            'priority': self.priority,
            'max_tweets_per_day': self.max_tweets_per_day,
            'last_search_at': self.last_search_at.isoformat() if self.last_search_at else None,
            'category': self.category,
            'filter_rules': self.filter_rules,
            'created_at': self.created_at.isoformat()
        }
        
        self.db.execute(query, params)
        
        if not self.id:
            # دریافت ID ایجاد شده
            self.id = self.db.cursor.lastrowid
        
        self.db.commit()
        return self
    
    def update_last_search(self):
        """به‌روزرسانی زمان آخرین جستجو"""
        self.last_search_at = datetime.now()
        query = f"""
            UPDATE {self.TABLE_NAME}
            SET last_search_at = :last_search_at
            WHERE id = :id
        """
        self.db.execute(query, {
            'id': self.id,
            'last_search_at': self.last_search_at.isoformat()
        })
        self.db.commit()
        return self
    
    @classmethod
    def get_by_id(cls, db, id):
        """دریافت کلمه کلیدی با ID"""
        query = f"SELECT * FROM {cls.TABLE_NAME} WHERE id = :id"
        result = db.execute(query, {'id': id}).fetchone()
        if result:
            return cls.from_dict(dict(result), db)
        return None
    
    @classmethod
    def get_by_text(cls, db, text):
        """دریافت کلمه کلیدی با متن"""
        query = f"SELECT * FROM {cls.TABLE_NAME} WHERE text = :text"
        result = db.execute(query, {'text': text}).fetchone()
        if result:
            return cls.from_dict(dict(result), db)
        return None
    
    @classmethod
    def get_all(cls, db, active_only=False):
        """دریافت همه کلمات کلیدی"""
        query = f"SELECT * FROM {cls.TABLE_NAME}"
        if active_only:
            query += " WHERE is_active = 1"
        query += " ORDER BY priority DESC, created_at DESC"
        
        results = db.execute(query).fetchall()
        return [cls.from_dict(dict(row), db) for row in results]
    
    @classmethod
    def from_dict(cls, data, db):
        """ایجاد مدل از دیکشنری"""
        return cls(
            db=db,
            id=data.get('id'),
            text=data.get('text'),
            is_active=bool(data.get('is_active')),
            priority=data.get('priority', 5),
            max_tweets_per_day=data.get('max_tweets_per_day', 1000),
            last_search_at=datetime.fromisoformat(data['last_search_at']) if data.get('last_search_at') else None,
            category=data.get('category'),
            filter_rules=data.get('filter_rules', {}),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None
        )
    
    def to_dict(self):
        """تبدیل مدل به دیکشنری"""
        return {
            'id': self.id,
            'text': self.text,
            'is_active': self.is_active,
            'priority': self.priority,
            'max_tweets_per_day': self.max_tweets_per_day,
            'last_search_at': self.last_search_at.isoformat() if self.last_search_at else None,
            'category': self.category,
            'filter_rules': self.filter_rules,
            'created_at': self.created_at.isoformat()
        }