"""面向业务的DAO函数"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from storage.db import get_db
from utils.time_utils import get_current_time

logger = logging.getLogger(__name__)


def save_before_edit(session_id: str, file_path: str, code_before: str) -> bool:
    """
    保存编辑前的代码到临时表
    
    Args:
        session_id: 会话ID
        file_path: 文件路径
        code_before: 编辑前的代码内容
    
    Returns:
        是否成功
    """
    db = get_db()
    try:
        cursor = db.execute("""
            INSERT OR REPLACE INTO temp_before_edit 
            (session_id, file_path, code_before, create_time)
            VALUES (?, ?, ?, ?)
        """, (session_id, file_path, code_before, get_current_time()))
        db.commit()
        logger.debug(f"Saved before_edit for session={session_id}, file={file_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to save before_edit: {e}")
        db.rollback()
        return False


def get_before_edit(session_id: str, file_path: str) -> Optional[str]:
    """
    获取编辑前的代码
    
    Args:
        session_id: 会话ID
        file_path: 文件路径
    
    Returns:
        编辑前的代码内容，如果不存在则返回None
    """
    db = get_db()
    try:
        cursor = db.execute("""
            SELECT code_before FROM temp_before_edit
            WHERE session_id = ? AND file_path = ?
        """, (session_id, file_path))
        row = cursor.fetchone()
        if row:
            return row[0]
        return None
    except Exception as e:
        logger.error(f"Failed to get before_edit: {e}")
        return None


def delete_before_edit(session_id: str, file_path: str) -> bool:
    """
    删除编辑前的代码记录
    
    Args:
        session_id: 会话ID
        file_path: 文件路径
    
    Returns:
        是否成功
    """
    db = get_db()
    try:
        db.execute("""
            DELETE FROM temp_before_edit
            WHERE session_id = ? AND file_path = ?
        """, (session_id, file_path))
        db.commit()
        logger.debug(f"Deleted before_edit for session={session_id}, file={file_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to delete before_edit: {e}")
        db.rollback()
        return False


def save_session_summary(
    session_id: str,
    file_path: str,
    add_lines_count: int,
    modify_lines_count: int,
    total_lines_after: int,
    session_info: Optional[str] = None
) -> bool:
    """
    保存会话汇总信息
    
    Args:
        session_id: 会话ID
        file_path: 文件路径
        add_lines_count: 新增行数
        modify_lines_count: 修改行数
        total_lines_after: 编辑后文件总行数
        session_info: 会话补充信息（可选）
    
    Returns:
        是否成功
    """
    db = get_db()
    try:
        db.execute("""
            INSERT OR REPLACE INTO session_summary
            (session_id, file_path, add_lines_count, modify_lines_count, 
             total_lines_after, session_info, create_time)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            session_id, file_path, add_lines_count, modify_lines_count,
            total_lines_after, session_info, get_current_time()
        ))
        db.commit()
        logger.debug(f"Saved session_summary for session={session_id}, file={file_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to save session_summary: {e}")
        db.rollback()
        return False


def save_code_diff_lines(
    session_id: str,
    file_path: str,
    diff_lines: List[Dict[str, Any]]
) -> bool:
    """
    批量保存差异行明细
    
    Args:
        session_id: 会话ID
        file_path: 文件路径
        diff_lines: 差异行列表，每个元素包含 diff_type, line_content, line_number
    
    Returns:
        是否成功
    """
    if not diff_lines:
        return True
    
    db = get_db()
    try:
        cursor = db.connect().cursor()
        cursor.executemany("""
            INSERT INTO code_diff_lines
            (session_id, file_path, diff_type, line_content, line_number, create_time)
            VALUES (?, ?, ?, ?, ?, ?)
        """, [
            (
                session_id,
                file_path,
                diff_line["diff_type"],
                diff_line["line_content"],
                diff_line["line_number"],
                get_current_time()
            )
            for diff_line in diff_lines
        ])
        db.commit()
        logger.debug(f"Saved {len(diff_lines)} diff_lines for session={session_id}, file={file_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to save code_diff_lines: {e}")
        db.rollback()
        return False


def get_session_summaries(
    session_id: Optional[str] = None,
    file_path: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None
) -> List[Dict[str, Any]]:
    """
    查询会话汇总信息
    
    Args:
        session_id: 会话ID（可选，用于过滤）
        file_path: 文件路径（可选，用于过滤）
        start_time: 开始时间（可选）
        end_time: 结束时间（可选）
    
    Returns:
        会话汇总列表
    """
    db = get_db()
    try:
        conditions = []
        params = []
        
        if session_id:
            conditions.append("session_id = ?")
            params.append(session_id)
        
        if file_path:
            conditions.append("file_path = ?")
            params.append(file_path)
        
        if start_time:
            conditions.append("create_time >= ?")
            params.append(start_time)
        
        if end_time:
            conditions.append("create_time <= ?")
            params.append(end_time)
        
        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
        
        cursor = db.execute(f"""
            SELECT session_id, file_path, add_lines_count, modify_lines_count,
                   total_lines_after, session_info, create_time
            FROM session_summary
            {where_clause}
            ORDER BY create_time DESC
        """, tuple(params))
        
        rows = cursor.fetchall()
        return [
            {
                "session_id": row[0],
                "file_path": row[1],
                "add_lines_count": row[2],
                "modify_lines_count": row[3],
                "total_lines_after": row[4],
                "session_info": row[5],
                "create_time": row[6]
            }
            for row in rows
        ]
    except Exception as e:
        logger.error(f"Failed to get session_summaries: {e}")
        return []


def get_code_diff_lines(
    session_id: Optional[str] = None,
    file_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    查询差异行明细
    
    Args:
        session_id: 会话ID（可选）
        file_path: 文件路径（可选）
    
    Returns:
        差异行列表
    """
    db = get_db()
    try:
        conditions = []
        params = []
        
        if session_id:
            conditions.append("session_id = ?")
            params.append(session_id)
        
        if file_path:
            conditions.append("file_path = ?")
            params.append(file_path)
        
        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
        
        cursor = db.execute(f"""
            SELECT id, session_id, file_path, diff_type, line_content, line_number, create_time
            FROM code_diff_lines
            {where_clause}
            ORDER BY line_number ASC
        """, tuple(params))
        
        rows = cursor.fetchall()
        return [
            {
                "id": row[0],
                "session_id": row[1],
                "file_path": row[2],
                "diff_type": row[3],
                "line_content": row[4],
                "line_number": row[5],
                "create_time": row[6]
            }
            for row in rows
        ]
    except Exception as e:
        logger.error(f"Failed to get code_diff_lines: {e}")
        return []


def delete_sessions(
    session_ids: Optional[List[str]] = None,
    before_time: Optional[datetime] = None
) -> int:
    """
    删除会话数据（级联删除差异行）
    
    Args:
        session_ids: 会话ID列表（可选）
        before_time: 删除指定时间之前的数据（可选）
    
    Returns:
        删除的记录数
    """
    db = get_db()
    try:
        if session_ids:
            placeholders = ",".join("?" * len(session_ids))
            cursor = db.execute(f"""
                DELETE FROM session_summary
                WHERE session_id IN ({placeholders})
            """, tuple(session_ids))
        elif before_time:
            cursor = db.execute("""
                DELETE FROM session_summary
                WHERE create_time < ?
            """, (before_time,))
        else:
            return 0
        
        deleted_count = cursor.rowcount
        db.commit()
        logger.info(f"Deleted {deleted_count} session records")
        return deleted_count
    except Exception as e:
        logger.error(f"Failed to delete sessions: {e}")
        db.rollback()
        return 0

