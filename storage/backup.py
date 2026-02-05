"""备份记录读写、导出/导入JSON实现"""
import json
import logging
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from storage.db import get_db
from storage.models import (
    get_session_summaries,
    get_code_diff_lines,
    save_session_summary,
    save_code_diff_lines
)
from utils.time_utils import get_current_time, format_datetime

logger = logging.getLogger(__name__)


def backup_database(backup_path: Optional[str] = None) -> Optional[str]:
    """
    备份数据库到JSON文件
    
    Args:
        backup_path: 备份文件路径（可选，如果为None则从配置读取）
    
    Returns:
        备份文件路径，如果失败则返回None
    """
    from config import get_database_config
    
    db = get_db()
    config = get_database_config()
    
    if backup_path is None:
        backup_dir = Path(config["backup_path"])
        backup_dir.mkdir(parents=True, exist_ok=True)
        timestamp = format_datetime(get_current_time(), "%Y%m%d_%H%M%S")
        backup_path = str(backup_dir / f"backup_{timestamp}.json")
    
    backup_file = Path(backup_path)
    backup_file.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # 导出所有数据
        summaries = get_session_summaries()
        all_diff_lines = get_code_diff_lines()
        
        # 组织数据
        backup_data = {
            "backup_time": format_datetime(get_current_time()),
            "version": "1.0.0",
            "summaries": summaries,
            "diff_lines": all_diff_lines
        }
        
        # 写入JSON文件
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2)
        
        # 记录备份信息
        backup_size = backup_file.stat().st_size // 1024  # KB
        record_backup(str(backup_file), backup_size)
        
        logger.info(f"Database backed up to {backup_file} ({backup_size} KB)")
        return str(backup_file)
        
    except Exception as e:
        logger.error(f"Failed to backup database: {e}")
        return None


def restore_database(backup_path: str) -> bool:
    """
    从JSON文件恢复数据库
    
    Args:
        backup_path: 备份文件路径
    
    Returns:
        是否成功
    """
    backup_file = Path(backup_path)
    
    if not backup_file.exists():
        logger.error(f"Backup file not found: {backup_path}")
        return False
    
    try:
        # 读取备份数据
        with open(backup_file, 'r', encoding='utf-8') as f:
            backup_data = json.load(f)
        
        # 清空现有数据（可选，根据需求决定）
        # 这里我们选择追加模式，不删除现有数据
        
        # 恢复会话汇总
        summaries = backup_data.get("summaries", [])
        for summary in summaries:
            save_session_summary(
                session_id=summary["session_id"],
                file_path=summary["file_path"],
                add_lines_count=summary["add_lines_count"],
                modify_lines_count=summary["modify_lines_count"],
                total_lines_after=summary["total_lines_after"],
                session_info=summary.get("session_info")
            )
        
        # 恢复差异行
        diff_lines = backup_data.get("diff_lines", [])
        # 按session_id和file_path分组
        grouped = {}
        for diff_line in diff_lines:
            key = (diff_line["session_id"], diff_line["file_path"])
            if key not in grouped:
                grouped[key] = []
            grouped[key].append({
                "diff_type": diff_line["diff_type"],
                "line_content": diff_line["line_content"],
                "line_number": diff_line["line_number"]
            })
        
        for (session_id, file_path), lines in grouped.items():
            save_code_diff_lines(session_id, file_path, lines)
        
        logger.info(f"Database restored from {backup_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to restore database: {e}")
        return False


def record_backup(backup_path: str, backup_size: int):
    """
    记录备份操作到数据库
    
    Args:
        backup_path: 备份文件路径
        backup_size: 备份文件大小（KB）
    """
    db = get_db()
    try:
        db.execute("""
            INSERT INTO backup_record (backup_path, backup_time, backup_size)
            VALUES (?, ?, ?)
        """, (backup_path, get_current_time(), backup_size))
        db.commit()
    except Exception as e:
        logger.error(f"Failed to record backup: {e}")


def get_backup_records(limit: int = 10) -> List[Dict[str, Any]]:
    """
    获取备份记录列表
    
    Args:
        limit: 返回记录数限制
    
    Returns:
        备份记录列表
    """
    db = get_db()
    try:
        cursor = db.execute("""
            SELECT id, backup_path, backup_time, backup_size
            FROM backup_record
            ORDER BY backup_time DESC
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        return [
            {
                "id": row[0],
                "backup_path": row[1],
                "backup_time": row[2],
                "backup_size": row[3]
            }
            for row in rows
        ]
    except Exception as e:
        logger.error(f"Failed to get backup records: {e}")
        return []

