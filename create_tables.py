# migrations/create_tables.py (continued)
def create_tables(db):
    """ایجاد جداول دیتابیس"""
    
    # جدول کلمات کلیدی
    db.execute_script("""
    CREATE TABLE IF NOT EXISTS keywords (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        text TEXT NOT NULL UNIQUE,
        is_active BOOLEAN DEFAULT 1,
        priority INTEGER DEFAULT 5,
        max_tweets_per_day INTEGER DEFAULT 1000,
        last_search_at TIMESTAMP,
        category TEXT,
        filter_rules JSON,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    # جدول کاربران توییتر
    db.execute_script("""
    CREATE TABLE IF NOT EXISTS twitter_users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        twitter_id TEXT NOT NULL UNIQUE,
        username TEXT NOT NULL,
        display_name TEXT,
        bio TEXT,
        followers_count INTEGER DEFAULT 0,
        following_count INTEGER DEFAULT 0,
        account_created_at TIMESTAMP,
        is_verified BOOLEAN DEFAULT 0,
        importance_score REAL DEFAULT 0,
        profile_data JSON,
        last_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE INDEX IF NOT EXISTS idx_twitter_users_username ON twitter_users(username);
    """)
    
    # جدول توییت‌ها
    db.execute_script("""
    CREATE TABLE IF NOT EXISTS tweets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        twitter_id TEXT NOT NULL UNIQUE,
        user_id INTEGER NOT NULL,
        content TEXT NOT NULL,
        created_at TIMESTAMP NOT NULL,
        collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        retweet_count INTEGER DEFAULT 0,
        like_count INTEGER DEFAULT 0,
        reply_count INTEGER DEFAULT 0,
        quote_count INTEGER DEFAULT 0,
        view_count INTEGER DEFAULT 0,
        is_retweet BOOLEAN DEFAULT 0,
        is_reply BOOLEAN DEFAULT 0,
        is_quote BOOLEAN DEFAULT 0,
        in_reply_to_id TEXT,
        language TEXT,
        is_sensitive BOOLEAN DEFAULT 0,
        importance_score REAL DEFAULT 0,
        importance_level TEXT DEFAULT 'normal',
        processing_status TEXT DEFAULT 'collected',
        filter_result TEXT DEFAULT 'pending',
        sentiment_score REAL,
        content_category TEXT,
        tweet_data JSON,
        FOREIGN KEY (user_id) REFERENCES twitter_users(id)
    );
    
    CREATE INDEX IF NOT EXISTS idx_tweets_twitter_id ON tweets(twitter_id);
    CREATE INDEX IF NOT EXISTS idx_tweets_created_at ON tweets(created_at);
    CREATE INDEX IF NOT EXISTS idx_tweets_processing_status ON tweets(processing_status);
    CREATE INDEX IF NOT EXISTS idx_tweets_importance_score ON tweets(importance_score);
    """)
    
    # جدول ارتباط توییت و کلمات کلیدی
    db.execute_script("""
    CREATE TABLE IF NOT EXISTS tweet_keywords (
        tweet_id INTEGER NOT NULL,
        keyword_id INTEGER NOT NULL,
        relevance_score REAL DEFAULT 1.0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (tweet_id, keyword_id),
        FOREIGN KEY (tweet_id) REFERENCES tweets(id) ON DELETE CASCADE,
        FOREIGN KEY (keyword_id) REFERENCES keywords(id) ON DELETE CASCADE
    );
    
    CREATE INDEX IF NOT EXISTS idx_tweet_keywords_keyword_id ON tweet_keywords(keyword_id);
    """)
    
    # جدول موجودیت‌های توییت (هشتگ‌ها، منشن‌ها، لینک‌ها)
    db.execute_script("""
    CREATE TABLE IF NOT EXISTS tweet_entities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tweet_id INTEGER NOT NULL,
        entity_type TEXT NOT NULL,
        text TEXT NOT NULL,
        mentioned_user_id INTEGER,
        start_index INTEGER,
        end_index INTEGER,
        FOREIGN KEY (tweet_id) REFERENCES tweets(id) ON DELETE CASCADE,
        FOREIGN KEY (mentioned_user_id) REFERENCES twitter_users(id)
    );
    
    CREATE INDEX IF NOT EXISTS idx_tweet_entities_type ON tweet_entities(entity_type, text);
    CREATE INDEX IF NOT EXISTS idx_tweet_entities_tweet_id ON tweet_entities(tweet_id);
    """)
    
    # جدول مدیریت API
    db.execute_script("""
    CREATE TABLE IF NOT EXISTS api_usage (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        service_type TEXT NOT NULL,
        endpoint TEXT NOT NULL,
        request_count INTEGER DEFAULT 1,
        tokens_used INTEGER DEFAULT 0,
        estimated_cost REAL DEFAULT 0,
        request_date DATE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE INDEX IF NOT EXISTS idx_api_usage_service_date ON api_usage(service_type, request_date);
    """)
    
    # جدول هشدارها
    db.execute_script("""
    CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        alert_type TEXT NOT NULL,
        severity TEXT DEFAULT 'medium',
        message TEXT NOT NULL,
        related_tweet_id INTEGER,
        is_read BOOLEAN DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (related_tweet_id) REFERENCES tweets(id)
    );
    
    CREATE INDEX IF NOT EXISTS idx_alerts_is_read ON alerts(is_read);
    """)