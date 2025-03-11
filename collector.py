# plugins/collector/collector.py
import asyncio
import json
from datetime import datetime, timedelta
from plugins.base_plugin import BasePlugin
from plugins.collector.twitter_api import TwitterAPI
from models.keyword import Keyword
from models.tweet import Tweet
from models.user import TwitterUser

class CollectorPlugin(BasePlugin):
    """پلاگین جمع‌آوری توییت"""
    
    def __init__(self, app):
        super().__init__(app)
        self.twitter_api = None
        self.is_collecting = False
        self.collection_task = None
    
    def initialize(self):
        """راه‌اندازی پلاگین"""
        self.logger.info("Initializing Tweet Collector Plugin")
        
        # دریافت کلید API از تنظیمات
        api_key = self.config.get('TWITTER', 'API_KEY')
        timeout = self.config.getint('TWITTER', 'API_TIMEOUT', 30)
        
        # ایجاد نمونه TwitterAPI
        self.twitter_api = TwitterAPI(api_key, self.logger, timeout)
        
        # اشتراک در رویدادها
        self.event_manager.subscribe('app_started', self._on_app_started)
        self.event_manager.subscribe('app_stopping', self._on_app_stopping)
        self.event_manager.subscribe('collect_tweets', self._on_collect_tweets)
        
        # راه‌اندازی تسک جمع‌آوری اتوماتیک
        self._start_collection_task()
        
        self.logger.info("Tweet Collector Plugin initialized")
    
    def shutdown(self):
        """توقف پلاگین"""
        self.logger.info("Shutting down Tweet Collector Plugin")
        self._stop_collection_task()
    
    def _on_app_started(self, data):
        """رویداد راه‌اندازی اپلیکیشن"""
        self.logger.debug("Collector received app_started event")
    
    def _on_app_stopping(self, data):
        """رویداد توقف اپلیکیشن"""
        self.logger.debug("Collector received app_stopping event")
        self._stop_collection_task()
    
    def _on_collect_tweets(self, data):
        """رویداد درخواست جمع‌آوری توییت"""
        self.logger.info("Received collect_tweets event")
        
        # جمع‌آوری بر اساس پارامترهای ارسالی
        keyword = data.get('keyword')
        max_tweets = data.get('max_tweets', 100)
        
        if keyword:
            # جمع‌آوری برای یک کلمه کلیدی خاص
            asyncio.create_task(self.collect_tweets_for_keyword(keyword, max_tweets))
        else:
            # جمع‌آوری برای همه کلمات کلیدی فعال
            asyncio.create_task(self.collect_tweets_for_all_keywords(max_tweets))
    
    def _start_collection_task(self):
        """شروع تسک جمع‌آوری اتوماتیک"""
        if self.collection_task is None or self.collection_task.done():
            self.collection_task = asyncio.create_task(self._automatic_collection())
            self.logger.info("Automatic collection task started")
    
    def _stop_collection_task(self):
        """توقف تسک جمع‌آوری اتوماتیک"""
        if self.collection_task and not self.collection_task.done():
            self.collection_task.cancel()
            self.logger.info("Automatic collection task stopped")
    
    async def _automatic_collection(self):
        """تسک جمع‌آوری اتوماتیک"""
        try:
            while True:
                if not self.is_collecting:
                    self.logger.info("Running automatic tweet collection")
                    await self.collect_tweets_for_all_keywords()
                
                # انتظار برای دور بعدی جمع‌آوری (هر ساعت)
                await asyncio.sleep(3600)  # 1 ساعت
        except asyncio.CancelledError:
            self.logger.info("Automatic collection task cancelled")
        except Exception as e:
            self.logger.error(f"Error in automatic collection task: {str(e)}")
    
    async def collect_tweets_for_all_keywords(self, max_tweets_per_keyword=None):
        """جمع‌آوری توییت برای همه کلمات کلیدی فعال"""
        if self.is_collecting:
            self.logger.warning("Tweet collection already in progress. Skipping...")
            return
        
        self.is_collecting = True
        collection_results = {}
        
        try:
            # دریافت کلمات کلیدی فعال
            keywords = Keyword.get_all(self.db, active_only=True)
            
            if not keywords:
                self.logger.warning("No active keywords found for collection")
                return collection_results
            
            self.logger.info(f"Starting collection for {len(keywords)} active keywords")
            
            # جمع‌آوری برای هر کلمه کلیدی
            for keyword in keywords:
                # تعیین حداکثر توییت برای جمع‌آوری
                if max_tweets_per_keyword is None:
                    keyword_max_tweets = keyword.max_tweets_per_day
                else:
                    keyword_max_tweets = min(keyword.max_tweets_per_day, max_tweets_per_keyword)
                
                try:
                    # جمع‌آوری توییت‌ها
                    count = await self.collect_tweets_for_keyword(keyword, keyword_max_tweets)
                    collection_results[keyword.text] = count
                    
                    # بروزرسانی زمان آخرین جستجو
                    keyword.update_last_search()
                    
                    # تاخیر کوتاه بین درخواست‌ها
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    self.logger.error(f"Error collecting tweets for keyword '{keyword.text}': {str(e)}")
                    collection_results[keyword.text] = 0
            
            self.logger.info("Tweet collection completed")
            
            # انتشار رویداد کامل شدن جمع‌آوری
            self.event_manager.emit('tweets_collected', results=collection_results)
            
            return collection_results
            
        except Exception as e:
            self.logger.error(f"Error in collect_tweets_for_all_keywords: {str(e)}")
            raise
        finally:
            self.is_collecting = False
    
    async def collect_tweets_for_keyword(self, keyword, max_tweets=100):
        """جمع‌آوری توییت برای یک کلمه کلیدی"""
        if isinstance(keyword, str):
            # تبدیل متن به آبجکت Keyword
            keyword_obj = Keyword.get_by_text(self.db, keyword)
            if not keyword_obj:
                self.logger.warning(f"Keyword '{keyword}' not found in database")
                keyword_text = keyword
                keyword_id = None
            else:
                keyword_text = keyword_obj.text
                keyword_id = keyword_obj.id
        else:
            # استفاده از آبجکت Keyword موجود
            keyword_text = keyword.text
            keyword_id = keyword.id
        
        self.logger.info(f"Collecting tweets for keyword: '{keyword_text}', max: {max_tweets}")
        
        try:
            # اجرای جستجو در توییتر
            search_result = await self.twitter_api.search_tweets(
                query=keyword_text,
                max_results=max_tweets
            )
            
            # بررسی نتایج
            if not search_result or 'tweets' not in search_result:
                self.logger.warning(f"No tweets found for keyword: '{keyword_text}'")
                return 0
            
            tweets = search_result.get('tweets', [])
            self.logger.info(f"Found {len(tweets)} tweets for keyword: '{keyword_text}'")
            
            # ذخیره توییت‌ها
            saved_count = 0
            for tweet_data in tweets:
                try:
                    # استخراج اطلاعات توییت
                    tweet_id = tweet_data.get('id')
                    content = tweet_data.get('text', '')
                    
                    # بررسی وجود توییت در دیتابیس
                    existing_tweet = Tweet.get_by_twitter_id(self.db, tweet_id)
                    if existing_tweet:
                        # به‌روزرسانی آمار توییت موجود
                        existing_tweet.update_stats(
                            retweet_count=tweet_data.get('retweetCount', 0),
                            like_count=tweet_data.get('likeCount', 0),
                            reply_count=tweet_data.get('replyCount', 0),
                            quote_count=tweet_data.get('quoteCount', 0),
                            view_count=tweet_data.get('viewCount', 0)
                        )
                        
                        # ایجاد ارتباط با کلمه کلیدی (اگر موجود نباشد)
                        if keyword_id:
                            existing_tweet.link_to_keyword(keyword_id)
                        
                        continue
                    
                    # استخراج اطلاعات کاربر
                    author_data = tweet_data.get('author', {})
                    author_id = author_data.get('id')
                    
                    # بررسی وجود کاربر در دیتابیس
                    user = TwitterUser.get_by_twitter_id(self.db, author_id)
                    if not user:
                        # ایجاد کاربر جدید
                        user = TwitterUser(
                            db=self.db,
                            twitter_id=author_id,
                            username=author_data.get('userName'),
                            display_name=author_data.get('name'),
                            followers_count=author_data.get('followers', 0),
                            following_count=author_data.get('following', 0),
                            is_verified=author_data.get('isBlueVerified', False),
                            profile_data=author_data
                        ).save()
                    
                    # ایجاد توییت جدید
                    created_at = datetime.strptime(
                        tweet_data.get('createdAt', '').split('+')[0],
                        '%a %b %d %H:%M:%S %Y'
                    ) if 'createdAt' in tweet_data else datetime.now()
                    
                    tweet = Tweet(
                        db=self.db,
                        twitter_id=tweet_id,
                        user_id=user.id,
                        content=content,
                        created_at=created_at,
                        retweet_count=tweet_data.get('retweetCount', 0),
                        like_count=tweet_data.get('likeCount', 0),
                        reply_count=tweet_data.get('replyCount', 0),
                        quote_count=tweet_data.get('quoteCount', 0),
                        view_count=tweet_data.get('viewCount', 0),
                        is_retweet='retweetedStatus' in tweet_data,
                        is_reply='inReplyToId' in tweet_data and tweet_data['inReplyToId'],
                        is_quote='quotedStatus' in tweet_data,
                        in_reply_to_id=tweet_data.get('inReplyToId'),
                        language=tweet_data.get('lang'),
                        is_sensitive=tweet_data.get('possiblySensitive', False),
                        tweet_data=tweet_data
                    ).save()
                    
                    # ایجاد ارتباط با کلمه کلیدی
                    if keyword_id:
                        tweet.link_to_keyword(keyword_id)
                    
                    saved_count += 1
                    
                    # انتشار رویداد توییت جدید
                    self.event_manager.emit('new_tweet', tweet_id=tweet.id)
                    
                except Exception as e:
                    self.logger.error(f"Error processing tweet {tweet_data.get('id', 'unknown')}: {str(e)}")
            
            self.logger.info(f"Saved {saved_count} new tweets for keyword: '{keyword_text}'")
            return saved_count
            
        except Exception as e:
            self.logger.error(f"Error collecting tweets for keyword '{keyword_text}': {str(e)}")
            raise