# plugins/filter/rules.py
import re
from collections import Counter

class FilterRules:
    """قواعد فیلترینگ توییت‌ها"""
    
    @staticmethod
    def contains_spam_patterns(text):
        """بررسی الگوهای اسپم"""
        # الگوهای رایج اسپم
        spam_patterns = [
            r'(?i)(buy now|click here|free offer|limited time|discount code|special deal)',
            r'(?i)(earn money online|work from home|make \$\d+ daily)',
            r'(?i)(viagra|cialis|medication online|buy pills)',
            r'(?i)(casino|betting|gambling|slot machine|poker)',
            r'(?i)(subscribe to my|follow me at|check out my profile)',
            r'https?://\S+\s+https?://\S+\s+https?://\S+'  # چندین لینک در یک توییت
        ]
        
        for pattern in spam_patterns:
            if re.search(pattern, text):
                return True
        
        return False
    
    @staticmethod
    def contains_offensive_language(text, language='fa'):
        """بررسی محتوای توهین‌آمیز"""
        # لیست کلمات توهین‌آمیز (به صورت ساده)
        if language == 'fa':
            offensive_words = [
                # اینجا کلمات فارسی نامناسب قرار می‌گیرند
                # این لیست باید به صورت واقعی تکمیل شود
                'کلمه_نامناسب1', 'کلمه_نامناسب2'
            ]
        else:
            offensive_words = [
                # کلمات انگلیسی نامناسب
                'offensive_word1', 'offensive_word2'
            ]
        
        # تبدیل به الگو برای جستجوی دقیق‌تر
        pattern = r'\b(' + '|'.join(offensive_words) + r')\b'
        
        if re.search(pattern, text, re.IGNORECASE):
            return True
        
        return False
    
    @staticmethod
    def is_propaganda(text):
        """تشخیص تبلیغات سیاسی"""
        # نیازمند الگوریتم‌های پیشرفته‌تر NLP
        # این یک تشخیص ساده است
        propaganda_indicators = [
            'حمایت_کنید_از',
            'رای_دهید_به',
            'انتخاب_کنید',
            'فقط_یک_انتخاب',
            'بهترین_گزینه'
        ]
        
        for indicator in propaganda_indicators:
            if indicator in text:
                return True
        
        return False
    
    @staticmethod
    def is_low_quality(text):
        """تشخیص محتوای کم‌کیفیت"""
        # توییت‌های خیلی کوتاه
        if len(text) < 10:
            return True
        
        # تکرار زیاد یک کاراکتر
        char_counts = Counter(text)
        most_common_char, count = char_counts.most_common(1)[0]
        if count > len(text) * 0.5 and len(text) > 15:
            return True
        
        # تکرار کلمات
        words = re.findall(r'\b\w+\b', text)
        if words:
            word_counts = Counter(words)
            most_common_word, count = word_counts.most_common(1)[0]
            if count > 3 and count > len(words) * 0.4:
                return True
        
        return False
    
    @staticmethod
    def contains_required_keywords(text, keywords):
        """بررسی وجود کلمات کلیدی الزامی"""
        if not keywords:
            return True
            
        for keyword in keywords:
            if keyword.lower() in text.lower():
                return True
                
        return False
    
    @staticmethod
    def is_excluded_by_keywords(text, exclude_keywords):
        """بررسی عدم وجود کلمات کلیدی مستثنی"""
        if not exclude_keywords:
            return False
            
        for keyword in exclude_keywords:
            if keyword.lower() in text.lower():
                return True
                
        return False