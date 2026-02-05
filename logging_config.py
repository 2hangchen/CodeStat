"""统一日志配置模块"""
import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    module_name: Optional[str] = None,
    stream: Optional[object] = None
) -> logging.Logger:
    """
    设置日志配置
    
    Args:
        log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: 日志文件路径（可选）
        module_name: 模块名称（用于logger命名）
    
    Returns:
        配置好的logger实例
    """
    # 转换日志级别
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # 创建formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 创建logger
    logger_name = module_name if module_name else __name__
    logger = logging.getLogger(logger_name)
    logger.setLevel(numeric_level)
    
    # 清除已有的handlers
    logger.handlers.clear()
    
    # 控制台handler
    # IMPORTANT:
    # - MCP stdio mode uses stdout for JSON-RPC. Writing logs to stdout will break the protocol.
    # - Default to stderr to be safe for both CLI and MCP.
    if stream is None:
        stream = sys.stderr
    console_handler = logging.StreamHandler(stream)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 文件handler（如果指定）
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """获取指定名称的logger"""
    return logging.getLogger(name)

