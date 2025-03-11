# plugins/collector/twitter_api.py
import time
import json
import httpx
from datetime import datetime, timedelta

class TwitterAPI:
    """کلاس ارتباط با Twitter API"""
    
    def __init__(self, api_key, logger, timeout=30, max_retries=3):
        self.api_key = api_key
        self.logger = logger
        self.timeout = timeout
        self.max_retries = max_retries
        self.base_url = "https://api.twitterapi.io/v1"
        self.rate_limits = {
            'search': {'limit': 60, 'remaining': 60, 'reset': 0},
            'user_info': {'limit': 60, 'remaining': 60, 'reset': 0},
        }
    
    async def _make_request(self, endpoint, params=None, method='GET'):
        """انجام یک درخواست به API توییتر"""
        url = f"{self.base_url}/{endpoint}"
        headers = {
            "X-API-Key": self.api_key,
            "Accept": "application/json"
        }
        
        # بررسی محدودیت نرخ
        endpoint_key = endpoint.split('/')[0] if '/' in endpoint else endpoint
        if endpoint_key in self.rate_limits:
            limit_data = self.rate_limits[endpoint_key]
            
            # اگر محدودیت به صفر رسیده و زمان ریست هنوز نرسیده
            if limit_data['remaining'] <= 0 and limit_data['reset'] > time.time():
                wait_time = limit_data['reset'] - time.time() + 1  # یک ثانیه اضافه برای اطمینان
                self.logger.warning(f"Rate limit hit for {endpoint_key}. Waiting {wait_time:.1f} seconds.")
                time.sleep(wait_time)
        
        retries = 0
        while retries <= self.max_retries:
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    if method == 'GET':
                        response = await client.get(url, headers=headers, params=params)
                    elif method == 'POST':
                        response = await client.post(url, headers=headers, json=params)
                    
                    # به‌روزرسانی محدودیت نرخ
                    if 'X-Rate-Limit-Limit' in response.headers:
                        self.rate_limits.setdefault(endpoint_key, {})
                        self.rate_limits[endpoint_key]['limit'] = int(response.headers['X-Rate-Limit-Limit'])
                        self.rate_limits[endpoint_key]['remaining'] = int(response.headers['X-Rate-Limit-Remaining'])
                        self.rate_limits[endpoint_key]['reset'] = int(response.headers['X-Rate-Limit-Reset'])
                    
                    # بررسی خطاهای HTTP
                    response.raise_for_status()
                    
                    return response.json()
                    
            except httpx.TimeoutException:
                retries += 1
                if retries <= self.max_retries:
                    self.logger.warning(f"Request to {endpoint} timed out. Retrying ({retries}/{self.max_retries})...")
                    time.sleep(2 ** retries)  # تاخیر نمایی
                else:
                    self.logger.error(f"Request to {endpoint} failed after {self.max_retries} retries due to timeout.")
                    raise
                    
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:  # Too Many Requests
                    retries += 1
                    retry_after = int(e.response.headers.get('Retry-After', 60))
                    self.logger.warning(f"Rate limit exceeded. Waiting {retry_after} seconds...")
                    time.sleep(retry_after)
                elif e.response.status_code >= 500:  # Server Error
                    retries += 1
                    if retries <= self.max_retries:
                        wait_time = 2 ** retries
                        self.logger.warning(f"Server error: {e}. Retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                    else:
                        self.logger.error(f"Request to {endpoint} failed after {self.max_retries} retries due to server error.")
                        raise
                else:
                    self.logger.error(f"HTTP error: {e}")
                    raise
                    
            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
                raise
    
    async def search_tweets(self, query, max_results=100, language=None, until=None, since=None):
        """جستجوی توییت‌ها"""
        endpoint = "tweet/advanced_search"
        
        # ساخت کوئری پیشرفته
        advanced_query = query
        
        if language:
            advanced_query += f" lang:{language}"
            
        if until:
            if isinstance(until, datetime):
                until = until.strftime('%Y-%m-%d_%H:%M:%S_UTC')
            advanced_query += f" until:{until}"
            
        if since:
            if isinstance(since, datetime):
                since = since.strftime('%Y-%m-%d_%H:%M:%S_UTC')
            advanced_query += f" since:{since}"
        
        params = {
            "query": advanced_query,
            "queryType": "Latest"
        }
        
        self.logger.info(f"Searching tweets with query: {advanced_query}")
        return await self._make_request(endpoint, params)
    
    async def get_user_info(self, username):
        """دریافت اطلاعات کاربر"""
        endpoint = "twitter/user/info"
        params = {"userName": username}
        
        self.logger.info(f"Fetching user info for: {username}")
        return await self._make_request(endpoint, params)
    
    async def get_tweet_by_id(self, tweet_id):
        """دریافت یک توییت با ID"""
        endpoint = "twitter/tweets"
        params = {"tweet_ids": tweet_id}
        
        self.logger.info(f"Fetching tweet with ID: {tweet_id}")
        return await self._make_request(endpoint, params)
    
    async def get_user_tweets(self, user_id=None, username=None, include_replies=False, max_results=20):
        """دریافت توییت‌های یک کاربر"""
        endpoint = "twitter/user/last_tweets"
        
        params = {
            "includeReplies": include_replies
        }
        
        if user_id:
            params["userId"] = user_id
        elif username:
            params["userName"] = username
        else:
            raise ValueError("Either user_id or username must be provided")
        
        self.logger.info(f"Fetching tweets for user: {username or user_id}")
        return await self._make_request(endpoint, params)