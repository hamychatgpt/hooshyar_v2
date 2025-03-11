# models/tweet.py
from datetime import datetime
from models.base import BaseModel

class Tweet(BaseModel):
    """مدل توییت"""
    
    TABLE_NAME = 'tweets'
    
    def __init__(self, db, id=None, twitter_id=None, user_id=None, content=None,
                 created_at=None, collected_at=None, retweet_count=0, like_count=0,
                 reply_count=0, quote_count=0, view_count=0, is_retweet=False,
                 is_reply=False, is_quote=False, in_reply_to_id=None, language=None,
                 is_sensitive=False, importance_score=0, importance_level='normal',
                 processing_status='collected', filter_result='pending',
                 sentiment_score=None, content_category=None, tweet_data=None):
        super().__init__(db)
        self.id = id
        self.twitter_id = twitter_id
        self.user_id = user_id
        self.content = content
        self.created_at = created_at
        self.collected_at = collected_at or datetime.now()
        self.retweet_count = retweet_count
        self.like_count = like_count
        self.reply_count = reply_count
        self.quote_count = quote_count
        self.view_count = view_count
        self.is_retweet = is_retweet
        self.is_reply = is_reply
        self.is_quote = is_quote
        self.in_reply_to_id = in_reply_to_id
        self.language = language
        self.is_sensitive = is_sensitive
        self.importance_score = importance_score
        self.importance_level = importance_level
        self.processing_status = processing_status
        self.filter_result = filter_result
        self.sentiment_score = sentiment_score
        self.content_category = content_category
        self.tweet_data = tweet_data or {}
    
    def save(self):
        """ذخیره توییت در دیتابیس"""
        if self.id:
            # به‌روزرسانی
            query = f"""
                UPDATE {self.TABLE_NAME}
                SET twitter_id = :twitter_id, user_id = :user_id, content = :content,
                    created_at = :created_at, collected_at = :collected_at,
                    retweet_count = :retweet_count, like_count = :like_count,
                    reply_count = :reply_count, quote_count = :quote_count,
                    view_count = :view_count, is_retweet = :is_retweet,
                    is_reply = :is_reply, is_quote = :is_quote,
                    in_reply_to_id = :in_reply_to_id, language = :language,
                    is_sensitive = :is_sensitive, importance_score = :importance_score,
                    importance_level = :importance_level, processing_status = :processing_status,
                    filter_result = :filter_result, sentiment_score = :sentiment_score,
                    content_category = :content_category, tweet_data = :tweet_data
                WHERE id = :id
            """
        else:
            # ایجاد جدید
            query = f"""
                INSERT INTO {self.TABLE_NAME}
                (twitter_id, user_id, content, created_at, collected_at,
                 retweet_count, like_count, reply_count, quote_count, view_count,
                 is_retweet, is_reply, is_quote, in_reply_to_id, language,
                 is_sensitive, importance_score, importance_level, processing_status,
                 filter_result, sentiment_score, content_category, tweet_data)
                VALUES
                (:twitter_id, :user_id, :content, :created_at, :collected_at,
                 :retweet_count, :like_count, :reply_count, :quote_count, :view_count,
                 :is_retweet, :is_reply, :is_quote, :in_reply_to_id, :language,
                 :is_sensitive, :importance_score, :importance_level, :processing_status,
                 :filter_result, :sentiment_score, :content_category, :tweet_data)
            """
        
        params = {
            'id': self.id,
            'twitter_id': self.twitter_id,
            'user_id': self.user_id,
            'content': self.content,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'collected_at': self.collected_at.isoformat(),
            'retweet_count': self.retweet_count,
            'like_count': self.like_count,
            'reply_count': self.reply_count,
            'quote_count': self.quote_count,
            'view_count': self.view_count,
            'is_retweet': 1 if self.is_retweet else 0,
            'is_reply': 1 if self.is_reply else 0,
            'is_quote': 1 if self.is_quote else 0,
            'in_reply_to_id': self.in_reply_to_id,
            'language': self.language,
            'is_sensitive': 1 if self.is_sensitive else 0,
            'importance_score': self.importance_score,
            'importance_level': self.importance_level,
            'processing_status': self.processing_status,
            'filter_result': self.filter_result,
            'sentiment_score': self.sentiment_score,
            'content_category': self.content_category,
            'tweet_data': self.tweet_data
        }
        
        self.db.execute(query, params)
        
        if not self.id:
            # دریافت ID ایجاد شده
            self.id = self.db.cursor.lastrowid
        
        self.db.commit()
        return self
    
    def update_stats(self, retweet_count=None, like_count=None, reply_count=None, 
                    quote_count=None, view_count=None):
        """به‌روزرسانی آمار توییت"""
        update_fields = []
        params = {'id': self.id}
        
        if retweet_count is not None:
            update_fields.append("retweet_count = :retweet_count")
            params['retweet_count'] = retweet_count
            self.retweet_count = retweet_count
            
        if like_count is not None:
            update_fields.append("like_count = :like_count")
            params['like_count'] = like_count
            self.like_count = like_count
            
        if reply_count is not None:
            update_fields.append("reply_count = :reply_count")
            params['reply_count'] = reply_count
            self.reply_count = reply_count
            
        if quote_count is not None:
            update_fields.append("quote_count = :quote_count")
            params['quote_count'] = quote_count
            self.quote_count = quote_count
            
        if view_count is not None:
            update_fields.append("view_count = :view_count")
            params['view_count'] = view_count
            self.view_count = view_count
        
        if update_fields:
            query = f"""
                UPDATE {self.TABLE_NAME}
                SET {', '.join(update_fields)}
                WHERE id = :id
            """
            self.db.execute(query, params)
            self.db.commit()
        
        return self
    
    def update_importance(self, importance_score=None, importance_level=None):
        """به‌روزرسانی اهمیت توییت"""
        update_fields = []
        params = {'id': self.id}
        
        if importance_score is not None:
            update_fields.append("importance_score = :importance_score")
            params['importance_score'] = importance_score
            self.importance_score = importance_score
            
        if importance_level is not None:
            update_fields.append("importance_level = :importance_level")
            params['importance_level'] = importance_level
            self.importance_level = importance_level
        
        if update_fields:
            query = f"""
                UPDATE {self.TABLE_NAME}
                SET {', '.join(update_fields)}
                WHERE id = :id
            """
            self.db.execute(query, params)
            self.db.commit()
        
        return self
    
    def update_processing_status(self, status):
        """به‌روزرسانی وضعیت پردازش"""
        query = f"""
            UPDATE {self.TABLE_NAME}
            SET processing_status = :status
            WHERE id = :id
        """
        self.db.execute(query, {
            'id': self.id,
            'status': status
        })
        self.processing_status = status
        self.db.commit()
        return self
    
    @classmethod
    def get_by_id(cls, db, id):
        """دریافت توییت با ID"""
        query = f"SELECT * FROM {cls.TABLE_NAME} WHERE id = :id"
        result = db.execute(query, {'id': id}).fetchone()
        if result:
            return cls.from_dict(dict(result), db)
        return None
    
    @classmethod
    def get_by_twitter_id(cls, db, twitter_id):
        """دریافت توییت با ID توییتر"""
        query = f"SELECT * FROM {cls.TABLE_NAME} WHERE twitter_id = :twitter_id"
        result = db.execute(query, {'twitter_id': twitter_id}).fetchone()
        if result:
            return cls.from_dict(dict(result), db)
        return None
    
    @classmethod
    def get_recent(cls, db, limit=10, offset=0):
        """دریافت توییت‌های اخیر"""
        query = f"""
            SELECT * FROM {cls.TABLE_NAME}
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
        """
        results = db.execute(query, {'limit': limit, 'offset': offset}).fetchall()
        return [cls.from_dict(dict(row), db) for row in results]
    
    @classmethod
    def from_dict(cls, data, db):
        """ایجاد مدل از دیکشنری"""
        return cls(
            db=db,
            id=data.get('id'),
            twitter_id=data.get('twitter_id'),
            user_id=data.get('user_id'),
            content=data.get('content'),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None,
            collected_at=datetime.fromisoformat(data['collected_at']) if data.get('collected_at') else None,
            retweet_count=data.get('retweet_count', 0),
            like_count=data.get('like_count', 0),
            reply_count=data.get('reply_count', 0),
            quote_count=data.get('quote_count', 0),
            view_count=data.get('view_count', 0),
            is_retweet=bool(data.get('is_retweet')),
            is_reply=bool(data.get('is_reply')),
            is_quote=bool(data.get('is_quote')),
            in_reply_to_id=data.get('in_reply_to_id'),
            language=data.get('language'),
            is_sensitive=bool(data.get('is_sensitive')),
            importance_score=data.get('importance_score', 0),
            importance_level=data.get('importance_level', 'normal'),
            processing_status=data.get('processing_status', 'collected'),
            filter_result=data.get('filter_result', 'pending'),
            sentiment_score=data.get('sentiment_score'),
            content_category=data.get('content_category'),
            tweet_data=data.get('tweet_data', {})
        )
    
    def to_dict(self):
        """تبدیل مدل به دیکشنری"""
        return {
            'id': self.id,
            'twitter_id': self.twitter_id,
            'user_id': self.user_id,
            'content': self.content,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'collected_at': self.collected_at.isoformat(),
            'retweet_count': self.retweet_count,
            'like_count': self.like_count,
            'reply_count': self.reply_count,
            'quote_count': self.quote_count,
            'view_count': self.view_count,
            'is_retweet': self.is_retweet,
            'is_reply': self.is_reply,
            'is_quote': self.is_quote,
            'in_reply_to_id': self.in_reply_to_id,
            'language': self.language,
            'is_sensitive': self.is_sensitive,
            'importance_score': self.importance_score,
            'importance_level': self.importance_level,
            'processing_status': self.processing_status,
            'filter_result': self.filter_result,
            'sentiment_score': self.sentiment_score,
            'content_category': self.content_category,
            'tweet_data': self.tweet_data
        }
        
    def link_to_keyword(self, keyword_id, relevance_score=1.0):
        """ایجاد ارتباط با یک کلمه کلیدی"""
        query = """
            INSERT OR IGNORE INTO tweet_keywords
            (tweet_id, keyword_id, relevance_score, created_at)
            VALUES
            (:tweet_id, :keyword_id, :relevance_score, :created_at)
        """
        self.db.execute(query, {
            'tweet_id': self.id,
            'keyword_id': keyword_id,
            'relevance_score': relevance_score,
            'created_at': datetime.now().isoformat()
        })
        self.db.commit()
        return self