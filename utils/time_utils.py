"""时间、日期、格式化工具"""
from datetime import datetime, timedelta
from typing import Optional, Tuple


def get_current_time() -> datetime:
    """获取当前时间"""
    return datetime.now()


def format_datetime(dt: datetime, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """格式化datetime为字符串"""
    return dt.strftime(fmt)


def parse_datetime(dt_str: str, fmt: str = "%Y-%m-%d %H:%M:%S") -> Optional[datetime]:
    """解析字符串为datetime"""
    try:
        return datetime.strptime(dt_str, fmt)
    except ValueError:
        return None


def get_time_range_days(days: int) -> Tuple[datetime, datetime]:
    """获取指定天数前到现在的时间范围"""
    end_time = get_current_time()
    start_time = end_time - timedelta(days=days)
    return start_time, end_time


def is_expired(create_time: datetime, days: int) -> bool:
    """判断创建时间是否已过期（超过指定天数）"""
    if create_time is None:
        return True
    expire_time = get_current_time() - timedelta(days=days)
    return create_time < expire_time

