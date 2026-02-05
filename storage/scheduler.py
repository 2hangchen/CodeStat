"""定时任务：自动备份和清理"""
import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Optional
from storage.backup import backup_database
from storage.models import delete_sessions
from config import get_database_config
from utils.time_utils import get_time_range_days

logger = logging.getLogger(__name__)


class Scheduler:
    """定时任务调度器"""
    
    def __init__(self):
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
    
    def start(self):
        """启动定时任务"""
        if self._running:
            logger.warning("Scheduler is already running")
            return
        
        self._running = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        logger.info("Scheduler started")
    
    def stop(self):
        """停止定时任务"""
        if not self._running:
            return
        
        self._running = False
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Scheduler stopped")
    
    def _run(self):
        """定时任务主循环"""
        # 计算到下一个凌晨的时间
        now = datetime.now()
        next_backup_time = (now + timedelta(days=1)).replace(hour=2, minute=0, second=0, microsecond=0)
        wait_seconds = (next_backup_time - now).total_seconds()
        
        logger.info(f"Next backup scheduled at {next_backup_time}, waiting {wait_seconds:.0f} seconds")
        
        while self._running and not self._stop_event.is_set():
            # 等待到下一个备份时间或停止信号
            if self._stop_event.wait(timeout=min(wait_seconds, 3600)):  # 最多等待1小时检查一次
                break
            
            now = datetime.now()
            if now >= next_backup_time:
                try:
                    # 执行备份
                    logger.info("Starting scheduled backup...")
                    backup_path = backup_database()
                    if backup_path:
                        logger.info(f"Scheduled backup completed: {backup_path}")
                    else:
                        logger.error("Scheduled backup failed")
                    
                    # 执行清理
                    config = get_database_config()
                    clean_cycle = config.get("clean_cycle", 30)
                    logger.info(f"Starting scheduled cleanup (removing data older than {clean_cycle} days)...")
                    _, before_time = get_time_range_days(clean_cycle)
                    deleted = delete_sessions(before_time=before_time)
                    logger.info(f"Scheduled cleanup completed: {deleted} records deleted")
                    
                except Exception as e:
                    logger.error(f"Scheduled task error: {e}", exc_info=True)
                
                # 计算下一个备份时间（明天凌晨2点）
                next_backup_time = (now + timedelta(days=1)).replace(hour=2, minute=0, second=0, microsecond=0)
                wait_seconds = (next_backup_time - now).total_seconds()
                logger.info(f"Next backup scheduled at {next_backup_time}")


# 全局调度器实例
_scheduler: Optional[Scheduler] = None


def get_scheduler() -> Scheduler:
    """获取全局调度器实例"""
    global _scheduler
    if _scheduler is None:
        _scheduler = Scheduler()
    return _scheduler


def start_scheduler():
    """启动定时任务"""
    scheduler = get_scheduler()
    scheduler.start()


def stop_scheduler():
    """停止定时任务"""
    global _scheduler
    if _scheduler:
        _scheduler.stop()

