# models/user.py
from datetime import datetime
from models.base import BaseModel

class TwitterUser(BaseModel):
    """مدل کاربر توییتر"""
    
    TABLE_NAME = 'twitter_users'
    
    def __init__(self, db, id=None, twitter_id=None, username=None, display_name=None,
                 bio=None, followers_count=0, following_count=0, account_created_at=None,
                 is_verified=False, importance_score=0, profile_data=None,
                 last_updated_at=None):
        super().__init__(db)
        self.id = id
        self.twitter_id = twitter_id
        self.username = username
        self.display_name = display_name
        self.bio = bio
        self.followers_count = followers_count
        self.following_count = following_count
        self.account_created_at = account_created_at
        self.is_verified = is_verified
        self.importance_score = importance_score
        self.profile_data = profile_data or {}
        self.last_updated_at = last_updated_at or datetime.now()
    
    def save(self):
        """ذخیره کاربر در دیتابیس"""
        if self.id:
            # به‌روزرسانی
            query = f"""
                UPDATE {self.TABLE_NAME}
                SET twitter_id = :twitter_id, username = :username, display_name = :display_name,
                    bio = :bio, followers_count = :followers_count, following_count = :following_count,
                    account_created_at = :account_created_at, is_verified = :is_verified,
                    importance_score = :importance_score, profile_data = :profile_data,
                    last_updated_at = :last_updated_at
                WHERE id = :id
            """
        else:
            # ایجاد جدید
            query = f"""
                INSERT INTO {self.TABLE_NAME}
                (twitter_id, username, display_name, bio, followers_count, following_count,
                 account_created_at, is_verified, importance_score, profile_data, last_updated_at)
                VALUES
                (:twitter_id, :username, :display_name, :bio, :followers_count, :following_count,
                 :account_created_at, :is_verified, :importance_score, :profile_data, :last_updated_at)
            """
        
        params = {
            'id': self.id,
            'twitter_id': self.twitter_id,
            'username': self.username,
            'display_name': self.display_name,
            'bio': self.bio,
            'followers_count': self.followers_count,
            'following_count': self.following_count,
            'account_created_at': self.account_created_at.isoformat() if self.account_created_at else None,
            'is_verified': 1 if self.is_verified else 0,
            'importance_score': self.importance_score,
            'profile_data': self.profile_data,
            'last_updated_at': self.last_updated_at.isoformat()
        }
        
        self.db.execute(query, params)
        
        if not self.id:
            # دریافت ID ایجاد شده
            self.id = self.db.cursor.lastrowid
        
        self.db.commit()
        return self
    
    @classmethod
    def get_by_id(cls, db, id):
        """دریافت کاربر با ID"""
        query = f"SELECT * FROM {cls.TABLE_NAME} WHERE id = :id"
        result = db.execute(query, {'id': id}).fetchone()
        if result:
            return cls.from_dict(dict(result), db)
        return None
    
    @classmethod
    def get_by_twitter_id(cls, db, twitter_id):
        """دریافت کاربر با ID توییتر"""
        query = f"SELECT * FROM {cls.TABLE_NAME} WHERE twitter_id = :twitter_id"
        result = db.execute(query, {'twitter_id': twitter_id}).fetchone()
        if result:
            return cls.from_dict(dict(result), db)
        return None
    
    @classmethod
    def get_by_username(cls, db, username):
        """دریافت کاربر با نام کاربری"""
        query = f"SELECT * FROM {cls.TABLE_NAME} WHERE username = :username"
        result = db.execute(query, {'username': username}).fetchone()
        if result:
            return cls.from_dict(dict(result), db)
        return None
    
    @classmethod
    def from_dict(cls, data, db):
        """ایجاد مدل از دیکشنری"""
        return cls(
            db=db,
            id=data.get('id'),
            twitter_id=data.get('twitter_id'),
            username=data.get('username'),
            display_name=data.get('display_name'),
            bio=data.get('bio'),
            followers_count=data.get('followers_count', 0),
            following_count=data.get('following_count', 0),
            account_created_at=datetime.fromisoformat(data['account_created_at']) if data.get('account_created_at') else None,
            is_verified=bool(data.get('is_verified')),
            importance_score=data.get('importance_score', 0),
            profile_data=data.get('profile_data', {}),
            last_updated_at=datetime.fromisoformat(data['last_updated_at']) if data.get('last_updated_at') else None
        )
    
    def to_dict(self):
        """تبدیل مدل به دیکشنری"""
        return {
            'id': self.id,
            'twitter_id': self.twitter_id,
            'username': self.username,
            'display_name': self.display_name,
            'bio': self.bio,
            'followers_count': self.followers_count,
            'following_count': self.following_count,
            'account_created_at': self.account_created_at.isoformat() if self.account_created_at else None,
            'is_verified': self.is_verified,
            'importance_score': self.importance_score,
            'profile_data': self.profile_data,
            'last_updated_at': self.last_updated_at.isoformat()
        }