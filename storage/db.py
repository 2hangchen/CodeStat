"""数据库连接管理、建表/迁移初始化逻辑"""
import sqlite3
import logging
from pathlib import Path
from typing import Optional
from config import get_database_config

logger = logging.getLogger(__name__)


class Database:
    """数据库连接管理类"""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        初始化数据库连接
        
        Args:
            db_path: 数据库文件路径，如果为None则从配置读取
        """
        if db_path is None:
            config = get_database_config()
            db_path = config["path"]
        
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._connection: Optional[sqlite3.Connection] = None
    
    def connect(self) -> sqlite3.Connection:
        """获取数据库连接（单例模式）"""
        if self._connection is None:
            self._connection = sqlite3.connect(
                str(self.db_path),
                check_same_thread=False
            )
            self._connection.row_factory = sqlite3.Row
            # 启用外键约束
            self._connection.execute("PRAGMA foreign_keys = ON")
        return self._connection
    
    def close(self):
        """关闭数据库连接"""
        if self._connection:
            self._connection.close()
            self._connection = None
    
    def initialize(self):
        """初始化数据库，创建所有表"""
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            # 1. 临时表：存储编辑前的完整代码
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS temp_before_edit (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    code_before TEXT NOT NULL,
                    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(session_id, file_path)
                )
            """)
            
            # 2. 会话汇总表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS session_summary (
                    session_id TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    add_lines_count INTEGER NOT NULL DEFAULT 0,
                    modify_lines_count INTEGER NOT NULL DEFAULT 0,
                    total_lines_after INTEGER NOT NULL,
                    session_info TEXT,
                    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (session_id, file_path)
                )
            """)
            
            # 创建索引
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_session_id 
                ON session_summary(session_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_file_path 
                ON session_summary(file_path)
            """)
            
            # 3. 差异行明细表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS code_diff_lines (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    diff_type TEXT NOT NULL CHECK (diff_type IN ('add', 'modify')),
                    line_content TEXT NOT NULL,
                    line_number INTEGER NOT NULL,
                    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id, file_path) 
                    REFERENCES session_summary(session_id, file_path) 
                    ON DELETE CASCADE
                )
            """)
            
            # 创建索引
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_diff_session_file 
                ON code_diff_lines(session_id, file_path)
            """)
            
            # 4. 数据备份记录表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS backup_record (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    backup_path TEXT NOT NULL,
                    backup_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                    backup_size INTEGER NOT NULL
                )
            """)
            
            conn.commit()
            logger.info(f"Database initialized successfully at {self.db_path}")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        """执行SQL语句"""
        conn = self.connect()
        return conn.execute(sql, params)
    
    def commit(self):
        """提交事务"""
        if self._connection:
            self._connection.commit()
    
    def rollback(self):
        """回滚事务"""
        if self._connection:
            self._connection.rollback()


# 全局数据库实例
_db_instance: Optional[Database] = None


def get_db() -> Database:
    """获取全局数据库实例（单例模式）"""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
        _db_instance.initialize()
    return _db_instance

