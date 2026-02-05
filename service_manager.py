"""MCP服务进程管理器"""
import os
import sys
import subprocess
import signal
import time
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any

# 添加项目根目录到Python路径
_project_root = Path(__file__).parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from config import get_server_config

logger = logging.getLogger(__name__)


class ServiceManager:
    """MCP服务进程管理器"""
    
    def __init__(self, pid_file: Optional[str] = None):
        """
        初始化服务管理器
        
        Args:
            pid_file: PID文件路径，用于存储进程ID
        """
        if pid_file is None:
            # 默认PID文件路径
            pid_file = Path.home() / ".local-mcp-server" / "server.pid"
        
        self.pid_file = Path(pid_file)
        self.pid_file.parent.mkdir(parents=True, exist_ok=True)
        self._process: Optional[subprocess.Popen] = None
    
    def get_pid(self) -> Optional[int]:
        """从PID文件读取进程ID"""
        if not self.pid_file.exists():
            return None
        
        try:
            with open(self.pid_file, 'r') as f:
                pid = int(f.read().strip())
            return pid
        except (ValueError, IOError) as e:
            logger.warning(f"Failed to read PID file: {e}")
            return None
    
    def is_running(self) -> bool:
        """检查服务是否正在运行"""
        pid = self.get_pid()
        if pid is None:
            return False
        
        try:
            # 检查进程是否存在
            os.kill(pid, 0)
            return True
        except (OSError, ProcessLookupError):
            # 进程不存在，清理PID文件
            if self.pid_file.exists():
                self.pid_file.unlink()
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """
        获取服务状态
        
        Returns:
            状态字典，包含 running, pid, port, host 等信息
        """
        server_config = get_server_config()
        status = {
            "running": False,
            "pid": None,
            "host": server_config["host"],
            "port": server_config["port"],
            "pid_file": str(self.pid_file)
        }
        
        if self.is_running():
            status["running"] = True
            status["pid"] = self.get_pid()
        
        return status
    
    def start(self, background: bool = True) -> bool:
        """
        启动MCP服务
        
        Args:
            background: 是否后台运行
        
        Returns:
            是否成功启动
        """
        if self.is_running():
            logger.warning("Service is already running")
            return False
        
        try:
            # 获取服务器配置
            server_config = get_server_config()
            host = server_config["host"]
            port = server_config["port"]
            
            # 构建启动命令
            script_path = Path(__file__).parent / "local_mcp_server.py"
            cmd = [sys.executable, str(script_path), "start", "--host", host, "--port", str(port)]
            
            if background:
                # 后台运行
                if sys.platform == "win32":
                    # Windows: 使用CREATE_NEW_PROCESS_GROUP和DETACHED_PROCESS
                    creationflags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
                    process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        creationflags=creationflags,
                        start_new_session=True
                    )
                else:
                    # Unix: 使用nohup和后台运行
                    process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        start_new_session=True
                    )
                
                # 等待一下确保进程启动
                time.sleep(0.5)
                
                if process.poll() is None:
                    # 进程仍在运行，保存PID
                    pid = process.pid
                    with open(self.pid_file, 'w') as f:
                        f.write(str(pid))
                    logger.info(f"MCP Server started in background (PID: {pid})")
                    return True
                else:
                    logger.error("Failed to start MCP Server (process exited immediately)")
                    return False
            else:
                # 前台运行（用于测试）
                self._process = subprocess.Popen(cmd)
                return True
        
        except Exception as e:
            logger.error(f"Failed to start MCP Server: {e}", exc_info=True)
            return False
    
    def stop(self) -> bool:
        """
        停止MCP服务
        
        Returns:
            是否成功停止
        """
        pid = self.get_pid()
        if pid is None:
            logger.warning("Service is not running (no PID file)")
            return False
        
        try:
            if sys.platform == "win32":
                # Windows: 使用taskkill
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(pid)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False
                )
            else:
                # Unix: 发送SIGTERM
                os.kill(pid, signal.SIGTERM)
                # 等待进程结束
                try:
                    os.waitpid(pid, 0)
                except ChildProcessError:
                    pass
            
            # 清理PID文件
            if self.pid_file.exists():
                self.pid_file.unlink()
            
            logger.info(f"MCP Server stopped (PID: {pid})")
            return True
        
        except (OSError, ProcessLookupError) as e:
            logger.warning(f"Process {pid} not found: {e}")
            # 清理PID文件
            if self.pid_file.exists():
                self.pid_file.unlink()
            return False
        except Exception as e:
            logger.error(f"Failed to stop MCP Server: {e}", exc_info=True)
            return False
    
    def restart(self) -> bool:
        """
        重启MCP服务
        
        Returns:
            是否成功重启
        """
        if self.is_running():
            self.stop()
            time.sleep(1)
        return self.start()


def get_service_manager() -> ServiceManager:
    """获取全局服务管理器实例"""
    return ServiceManager()

