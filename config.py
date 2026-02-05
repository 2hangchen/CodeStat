"""配置管理模块，支持从config.json和环境变量加载配置"""
import json
import os
from pathlib import Path
from typing import Any, Dict
import logging

logger = logging.getLogger(__name__)

# 全局配置缓存
_config: Dict[str, Any] = None


def get_config_path() -> Path:
    """获取配置文件路径"""
    config_file = Path(__file__).parent / "config.json"
    return config_file


def load_config() -> Dict[str, Any]:
    """加载配置文件，支持环境变量覆盖"""
    global _config
    
    if _config is not None:
        return _config
    
    config_path = get_config_path()
    
    # 默认配置
    default_config = {
        "server": {
            "host": "127.0.0.1",
            "port": 54546,
            "log_level": "info",
            "log_file": "~/.local-mcp-server/server.log"
        },
        "database": {
            "path": "~/.local-mcp-server/db.sqlite",
            "backup_path": "~/.local-mcp-server/backup/",
            "clean_cycle": 30
        },
        "cli": {
            "cache_time": 300,
            "default_time_range": 7
        }
    }
    
    # 从文件加载配置
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                file_config = json.load(f)
                default_config.update(file_config)
        except Exception as e:
            logger.warning(f"Failed to load config file: {e}, using defaults")
    else:
        logger.info(f"Config file not found at {config_path}, using defaults")
    
    # 环境变量覆盖
    env_mappings = {
        "MCP_SERVER_HOST": ("server", "host"),
        "MCP_SERVER_PORT": ("server", "port"),
        "MCP_SERVER_LOG_LEVEL": ("server", "log_level"),
        "MCP_SERVER_LOG_FILE": ("server", "log_file"),
        "MCP_DB_PATH": ("database", "path"),
        "MCP_DB_BACKUP_PATH": ("database", "backup_path"),
        "MCP_DB_CLEAN_CYCLE": ("database", "clean_cycle"),
        "MCP_CLI_CACHE_TIME": ("cli", "cache_time"),
        "MCP_CLI_DEFAULT_TIME_RANGE": ("cli", "default_time_range"),
    }
    
    for env_key, (section, key) in env_mappings.items():
        env_value = os.getenv(env_key)
        if env_value is not None:
            if key in ["port", "clean_cycle", "cache_time", "default_time_range"]:
                try:
                    env_value = int(env_value)
                except ValueError:
                    logger.warning(f"Invalid integer value for {env_key}: {env_value}")
                    continue
            default_config[section][key] = env_value
    
        # 展开路径中的 ~
        if "database" in default_config:
            db_path = default_config["database"]["path"]
            if db_path.startswith("~"):
                default_config["database"]["path"] = os.path.expanduser(db_path)
            
            backup_path = default_config["database"]["backup_path"]
            if backup_path.startswith("~"):
                default_config["database"]["backup_path"] = os.path.expanduser(backup_path)
        
        if "server" in default_config and "log_file" in default_config["server"]:
            log_file = default_config["server"]["log_file"]
            if log_file and log_file.startswith("~"):
                default_config["server"]["log_file"] = os.path.expanduser(log_file)
    
    _config = default_config
    return _config


def get_config() -> Dict[str, Any]:
    """获取配置（懒加载）"""
    return load_config()


def get_server_config() -> Dict[str, Any]:
    """获取服务器配置"""
    return get_config()["server"]


def get_database_config() -> Dict[str, Any]:
    """获取数据库配置"""
    return get_config()["database"]


def get_cli_config() -> Dict[str, Any]:
    """获取CLI配置"""
    return get_config()["cli"]

