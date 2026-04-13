from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import asyncio
import logging

from app.database import async_session
from app.services.signal_service import SignalService
from app.services.stock_service import StockService
from sqlalchemy import select
from app.models import WatchlistStock, Signal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TaskManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.scheduler = None
        return cls._instance

    def __init__(self):
        if self.scheduler is None:
            self.scheduler = AsyncIOScheduler()
            self._setup_jobs()

    def _setup_jobs(self):
        # self.scheduler.add_job(
        #     self.analyze_all_signals,
        #     IntervalTrigger(minutes=10),
        #     id="analyze_signals",
        #     name="Analyze all watchlist stocks for signals",
        #     replace_existing=True,
        # )

        # self.scheduler.add_job(
        #     self.update_price_cache,
        #     IntervalTrigger(minutes=5),
        #     id="update_prices",
        #     name="Update stock price cache",
        #     replace_existing=True,
        # )

        # self.scheduler.add_job(
        #     self.cleanup_old_signals,
        #     CronTrigger(hour=2, minute=0),
        #     id="cleanup_signals",
        #     name="Clean up old inactive signals",
        #     replace_existing=True,
        # )

        logger.info("Scheduled jobs configured:")
        for job in self.scheduler.get_jobs():
            logger.info(f"  - {job.name}: {job.trigger}")

    async def analyze_all_signals(self):
        logger.info(f"[{datetime.now()}] Starting signal analysis task...")

        try:
            async with async_session() as session:
                result = await session.execute(
                    select(WatchlistStock.ts_code).distinct()
                )
                ts_codes = [r[0] for r in result.all()]

                if not ts_codes:
                    logger.info("No stocks in watchlists to analyze")
                    return

                logger.info(f"Analyzing {len(ts_codes)} stocks...")

                signal_service = SignalService(session)
                analyzed_count = 0
                buy_signals = 0
                sell_signals = 0

                for ts_code in ts_codes:
                    try:
                        analysis = await signal_service.analyze_stock(ts_code)

                        if "error" not in analysis:
                            await signal_service.save_signal(analysis)
                            analyzed_count += 1

                            if analysis["signal_type"] == "BUY":
                                buy_signals += 1
                                logger.info(f"BUY signal generated for {ts_code}")
                            elif analysis["signal_type"] == "SELL":
                                sell_signals += 1
                                logger.info(f"SELL signal generated for {ts_code}")

                            await asyncio.sleep(0.5)
                    except Exception as e:
                        logger.error(f"Error analyzing {ts_code}: {e}")

                logger.info(
                    f"Signal analysis completed: {analyzed_count} analyzed, "
                    f"{buy_signals} BUY, {sell_signals} SELL"
                )
        except Exception as e:
            logger.error(f"Signal analysis task failed: {e}")

    async def update_price_cache(self):
        logger.info(f"[{datetime.now()}] Starting price cache update...")

        try:
            async with async_session() as session:
                result = await session.execute(
                    select(WatchlistStock.ts_code).distinct()
                )
                ts_codes = [r[0] for r in result.all()]

                if not ts_codes:
                    return

                stock_service = StockService()
                signal_service = SignalService(session)
                updated_count = 0

                for ts_code in ts_codes:
                    try:
                        detail = stock_service.get_stock_detail(ts_code)
                        if detail:
                            from datetime import date

                            price_data = {
                                "trade_date": date.today(),
                                "open": detail.get("open"),
                                "high": detail.get("high"),
                                "low": detail.get("low"),
                                "close": detail.get("current_price"),
                                "volume": detail.get("volume"),
                                "amount": detail.get("amount"),
                                "change_pct": detail.get("change_pct"),
                                "turnover_rate": detail.get("turnover_rate"),
                            }
                            await signal_service.update_price_cache(ts_code, price_data)
                            updated_count += 1
                    except Exception as e:
                        logger.error(f"Error updating price for {ts_code}: {e}")

                logger.info(f"Price cache updated: {updated_count} stocks")
        except Exception as e:
            logger.error(f"Price cache update failed: {e}")

    async def cleanup_old_signals(self):
        logger.info(f"[{datetime.now()}] Starting signal cleanup...")

        try:
            async with async_session() as session:
                from datetime import date, timedelta
                from sqlalchemy import delete

                cutoff_date = date.today() - timedelta(days=30)

                result = await session.execute(
                    delete(Signal).where(
                        Signal.is_active == False, Signal.signal_date < cutoff_date
                    )
                )

                await session.commit()
                logger.info(f"Cleaned up {result.rowcount} old signals")
        except Exception as e:
            logger.error(f"Signal cleanup failed: {e}")

    def start(self):
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Task scheduler started")

    def shutdown(self):
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Task scheduler stopped")

    def get_status(self):
        return {
            "running": self.scheduler.running,
            "jobs": [
                {
                    "id": job.id,
                    "name": job.name,
                    "next_run": job.next_run_time.isoformat()
                    if job.next_run_time
                    else None,
                    "trigger": str(job.trigger),
                }
                for job in self.scheduler.get_jobs()
            ],
        }


task_manager = TaskManager()
