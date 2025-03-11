# plugins/filter/filter.py
from plugins.base_plugin import BasePlugin
from plugins.filter.rules import FilterRules
from models.tweet import Tweet

class FilterPlugin(BasePlugin):
    """پلاگین فیلتر توییت‌ها"""
    
    def __init__(self, app):
        super().__init__(app)
        
    def initialize(self):
        """راه‌اندازی پلاگین"""
        self.logger.info("Initializing Tweet Filter Plugin")
        
        # اشتراک در رویدادها
        self.event_manager.subscribe('new_tweet', self._on_new_tweet)
        self.event_manager.subscribe('filter_tweet', self._on_filter_tweet)
        
        self.logger.info("Tweet Filter Plugin initialized")
    
    def shutdown(self):
        """توقف پلاگین"""
        self.logger.info("Shutting down Tweet Filter Plugin")
    
    def _on_new_tweet(self, data):
        """رویداد توییت جدید"""
        tweet_id = data.get('tweet_id')
        if tweet_id:
            self.logger.debug(f"Filter received new_tweet event for tweet {tweet_id}")
            self.filter_tweet(tweet_id)
    
    def _on_filter_tweet(self, data):
        """رویداد درخواست فیلتر توییت"""
        tweet_id = data.get('tweet_id')
        if tweet_id:
            self.logger.debug(f"Filter received filter_tweet event for tweet {tweet_id}")
            self.filter_tweet(tweet_id)
    
    def filter_tweet(self, tweet_id):
        """فیلتر یک توییت با ID"""
        tweet = Tweet.get_by_id(self.db, tweet_id)
        if not tweet:
            self.logger.warning(f"Tweet {tweet_id} not found for filtering")
            return False
        
        if tweet.processing_status != 'collected':
            self.logger.debug(f"Tweet {tweet_id} already processed. Status: {tweet.processing_status}")
            return False
        
        try:
            self.logger.debug(f"Filtering tweet {tweet_id}")
            
            # اعمال قواعد فیلتر
            content = tweet.content
            
            # بررسی اسپم
            if FilterRules.contains_spam_patterns(content):
                self.logger.debug(f"Tweet {tweet_id} rejected: Spam")
                tweet.update_processing_status('filtered_spam')
                tweet.filter_result = 'rejected'
                tweet.save()
                return False
            
            # بررسی محتوای توهین‌آمیز
            if FilterRules.contains_offensive_language(content, tweet.language):
                self.logger.debug(f"Tweet {tweet_id} rejected: Offensive language")
                tweet.update_processing_status('filtered_offensive')
                tweet.filter_result = 'rejected'
                tweet.save()
                return False
            
            # بررسی تبلیغات سیاسی
            if FilterRules.is_propaganda(content):
                self.logger.debug(f"Tweet {tweet_id} rejected: Propaganda")
                tweet.update_processing_status('filtered_propaganda')
                tweet.filter_result = 'rejected'
                tweet.save()
                return False
            
            # بررسی کیفیت محتوا
            if FilterRules.is_low_quality(content):
                self.logger.debug(f"Tweet {tweet_id} rejected: Low quality")
                tweet.update_processing_status('filtered_low_quality')
                tweet.filter_result = 'rejected'
                tweet.save()
                return False
            
            # قبول توییت
            self.logger.debug(f"Tweet {tweet_id} accepted")
            tweet.update_processing_status('filtered_accepted')
            tweet.filter_result = 'accepted'
            tweet.save()
            
            # انتشار رویداد توییت قبول شده
            self.event_manager.emit('tweet_accepted', tweet_id=tweet_id)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error filtering tweet {tweet_id}: {str(e)}")
            tweet.update_processing_status('filter_error')
            tweet.save()
            return False