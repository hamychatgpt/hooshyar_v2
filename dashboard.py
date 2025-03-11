# plugins/dashboard/dashboard.py
from datetime import datetime, timedelta
import os
from fastapi import FastAPI, Request, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
from pydantic import BaseModel
import threading
import asyncio

from plugins.base_plugin import BasePlugin
from models.keyword import Keyword
from models.tweet import Tweet
from models.user import TwitterUser

class DashboardPlugin(BasePlugin):
    """پلاگین داشبورد مدیریت"""
    
    def __init__(self, app):
        super().__init__(app)
        self.fastapi_app = None
        self.server_thread = None
        self.templates_dir = os.path.join(os.path.dirname(__file__), "templates")
        self.static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "static")
        
    def initialize(self):
        """راه‌اندازی پلاگین"""
        self.logger.info("Initializing Dashboard Plugin")
        
        # ایجاد برنامه FastAPI
        self.fastapi_app = FastAPI(title="Twitter Monitor Dashboard")
        
        # تنظیم مسیر فایل‌های استاتیک
        self.fastapi_app.mount("/static", StaticFiles(directory=self.static_dir), name="static")
        
        # تنظیم موتور قالب
        self.templates = Jinja2Templates(directory=self.templates_dir)
        
        # ثبت مسیرها
        self._register_routes()
        
        # راه‌اندازی سرور در یک ترد جداگانه
        host = self.config.get('DASHBOARD', 'HOST', '0.0.0.0')
        port = self.config.getint('DASHBOARD', 'PORT', 8000)
        
        self.server_thread = threading.Thread(
            target=self._run_server,
            args=(host, port),
            daemon=True
        )
        self.server_thread.start()
        
        self.logger.info(f"Dashboard Plugin initialized on http://{host}:{port}")
    
    def shutdown(self):
        """توقف پلاگین"""
        self.logger.info("Shutting down Dashboard Plugin")
    
    def _register_routes(self):
        """ثبت مسیرهای FastAPI"""
        
        @self.fastapi_app.get("/", response_class=HTMLResponse)
        async def read_root(request: Request):
            """صفحه اصلی"""
            tweet_count = len(Tweet.get_recent(self.db, limit=1000))
            
            # آمار کلی
            stats = {
                'total_tweets': tweet_count,
                'active_keywords': len(Keyword.get_all(self.db, active_only=True)),
                'recent_tweets': Tweet.get_recent(self.db, limit=10)
            }
            
            # نمودار توییت‌ها در 7 روز گذشته
            chart_data = await self._get_tweet_volume_data(days=7)
            
            return self.templates.TemplateResponse(
                "dashboard.html",
                {"request": request, "stats": stats, "chart_data": chart_data}
            )
        
        @self.fastapi_app.get("/keywords", response_class=HTMLResponse)
        async def keywords_page(request: Request):
            """صفحه مدیریت کلمات کلیدی"""
            keywords = Keyword.get_all(self.db)
            return self.templates.TemplateResponse(
                "keywords.html",
                {"request": request, "keywords": keywords}
            )
        
        @self.fastapi_app.post("/keywords/add")
        async def add_keyword(
            request: Request,
            text: str = Form(...),
            priority: int = Form(5),
            max_tweets_per_day: int = Form(1000)
        ):
            """افزودن کلمه کلیدی جدید"""
            # بررسی وجود کلمه کلیدی
            existing = Keyword.get_by_text(self.db, text)
            if existing:
                return {"status": "error", "message": "Keyword already exists"}
            
            # ایجاد کلمه کلیدی جدید
            keyword = Keyword(
                db=self.db,
                text=text,
                priority=priority,
                max_tweets_per_day=max_tweets_per_day
            ).save()
            
            return RedirectResponse(url="/keywords", status_code=303)
        
        @self.fastapi_app.get("/keywords/{keyword_id}/toggle")
        async def toggle_keyword(request: Request, keyword_id: int):
            """تغییر وضعیت فعال/غیرفعال کلمه کلیدی"""
            keyword = Keyword.get_by_id(self.db, keyword_id)
            if not keyword:
                raise HTTPException(status_code=404, detail="Keyword not found")
            
            keyword.is_active = not keyword.is_active
            keyword.save()
            
            return RedirectResponse(url="/keywords", status_code=303)
        
        @self.fastapi_app.get("/keywords/{keyword_id}/delete")
        async def delete_keyword(request: Request, keyword_id: int):
            """حذف کلمه کلیدی"""
            keyword = Keyword.get_by_id(self.db, keyword_id)
            if not keyword:
                raise HTTPException(status_code=404, detail="Keyword not found")
            
            # حذف کلمه کلیدی
            self.db.execute(
                "DELETE FROM keywords WHERE id = ?",
                {"id": keyword_id}
            )
            self.db.commit()
            
            return RedirectResponse(url="/keywords", status_code=303)
        
        @self.fastapi_app.get("/tweets", response_class=HTMLResponse)
        async def tweets_page(request: Request, limit: int = 50, offset: int = 0, status: str = None):
            """صفحه مشاهده توییت‌ها"""
            # ساخت کوئری
            query = "SELECT * FROM tweets"
            params = {}
            
            if status:
                query += " WHERE processing_status = :status"
                params["status"] = status
            
            query += " ORDER BY created_at DESC LIMIT :limit OFFSET :offset"
            params["limit"] = limit
            params["offset"] = offset
            
            # اجرای کوئری
            results = self.db.execute(query, params).fetchall()
            tweets = [Tweet.from_dict(dict(row), self.db) for row in results]
            
            # دریافت تعداد کل
            count_query = "SELECT COUNT(*) as count FROM tweets"
            if status:
                count_query += " WHERE processing_status = :status"
            
            count_result = self.db.execute(count_query, params).fetchone()
            total_count = dict(count_result)["count"]
            
            # محاسبه صفحه‌بندی
            pagination = {
                "current_offset": offset,
                "limit": limit,
                "total_count": total_count,
                "has_prev": offset > 0,
                "has_next": offset + limit < total_count,
                "prev_offset": max(0, offset - limit),
                "next_offset": offset + limit
            }
            
            return self.templates.TemplateResponse(
                "tweets.html",
                {
                    "request": request,
                    "tweets": tweets,
                    "pagination": pagination,
                    "status": status
                }
            )
        
        @self.fastapi_app.get("/api/stats")
        async def get_stats():
            """API برای آمار کلی"""
            tweet_count = len(Tweet.get_recent(self.db, limit=1000))
            accepted_count = 0
            rejected_count = 0
            
            # محاسبه تعداد توییت‌های پذیرفته/رد شده
            filter_stats = self.db.execute("""
                SELECT filter_result, COUNT(*) as count
                FROM tweets
                GROUP BY filter_result
            """).fetchall()
            
            for row in filter_stats:
                stats_row = dict(row)
                if stats_row["filter_result"] == "accepted":
                    accepted_count = stats_row["count"]
                elif stats_row["filter_result"] == "rejected":
                    rejected_count = stats_row["count"]
            
            return {
                "total_tweets": tweet_count,
                "active_keywords": len(Keyword.get_all(self.db, active_only=True)),
                "accepted_tweets": accepted_count,
                "rejected_tweets": rejected_count
            }
        
        @self.fastapi_app.get("/api/chart/volume")
        async def get_tweet_volume():
            """API برای داده‌های نمودار حجم توییت"""
            return await self._get_tweet_volume_data()
        
        @self.fastapi_app.post("/api/collect")
        async def trigger_collection():
            """API برای شروع جمع‌آوری دستی"""
            self.event_manager.emit('collect_tweets')
            return {"status": "success", "message": "Collection started"}
    
    def _run_server(self, host, port):
        """اجرای سرور FastAPI"""
        uvicorn.run(self.fastapi_app, host=host, port=port)
    
    async def _get_tweet_volume_data(self, days=7):
        """دریافت داده‌های حجم توییت برای نمودار"""
        # محاسبه تاریخ شروع
        start_date = datetime.now() - timedelta(days=days)
        
        # اجرای کوئری
        query = """
            SELECT DATE(created_at) as date, COUNT(*) as count
            FROM tweets
            WHERE created_at >= :start_date
            GROUP BY DATE(created_at)
            ORDER BY date ASC
        """
        
        results = self.db.execute(query, {"start_date": start_date.isoformat()}).fetchall()
        
        # ساخت داده‌های نمودار
        chart_data = [{"date": dict(row)["date"], "count": dict(row)["count"]} for row in results]
        
        # تکمیل تاریخ‌های خالی
        dates = set(item["date"] for item in chart_data)
        current_date = start_date.date()
        end_date = datetime.now().date()
        
        while current_date <= end_date:
            date_str = current_date.isoformat()
            if date_str not in dates:
                chart_data.append({"date": date_str, "count": 0})
            current_date += timedelta(days=1)
        
        # مرتب‌سازی بر اساس تاریخ
        chart_data.sort(key=lambda x: x["date"])
        
        return chart_data