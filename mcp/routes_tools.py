"""MCP Tool发现端点，返回可用工具列表"""
from fastapi import APIRouter
from typing import List, Dict, Any

router = APIRouter(prefix="/mcp", tags=["MCP Tools"])


@router.get("/tools", response_model=Dict[str, Any])
async def list_tools():
    """
    MCP Tool发现端点
    
    返回所有可用的MCP Tools列表，供Agent自动发现和注册
    """
    tools = [
        {
            "name": "RecordBeforeEdit",
            "description": "记录文件编辑前的完整代码内容（仅本地临时存储，后续自动清理，不冗余保留）",
            "schema_version": "v1",
            "capabilities": ["read"],
            "endpoint": "/mcp/record_before",
            "method": "POST",
            "actions": [
                {
                    "name": "record_before",
                    "description": "记录文件编辑前的代码，用于后续对比差异",
                    "parameters": [
                        {
                            "name": "session_id",
                            "type": "string",
                            "required": True,
                            "description": "当前会话ID，由Agent生成，需与RecordAfterEdit的session_id一致，用于关联同一编辑操作"
                        },
                        {
                            "name": "file_path",
                            "type": "string",
                            "required": True,
                            "description": "目标文件的绝对路径（如/Users/xxx/project/test.py），用于关联文件"
                        },
                        {
                            "name": "code_before",
                            "type": "string",
                            "required": True,
                            "description": "文件编辑前的完整代码内容（保留原始格式、空行，确保行号精准）"
                        }
                    ]
                }
            ]
        },
        {
            "name": "RecordAfterEdit",
            "description": "记录文件编辑后的完整代码，提取具体差异行（新增/修改）及行号，清理临时数据，仅保留差异信息",
            "schema_version": "v1",
            "capabilities": ["write"],
            "endpoint": "/mcp/record_after",
            "method": "POST",
            "actions": [
                {
                    "name": "record_after_and_calc_diff",
                    "description": "记录编辑后代码，计算并存储具体差异行，清理编辑前的完整代码",
                    "parameters": [
                        {
                            "name": "session_id",
                            "type": "string",
                            "required": True,
                            "description": "当前会话ID，需与RecordBeforeEdit的session_id一致，用于关联同一编辑操作"
                        },
                        {
                            "name": "file_path",
                            "type": "string",
                            "required": True,
                            "description": "目标文件的绝对路径，需与RecordBeforeEdit的file_path一致"
                        },
                        {
                            "name": "code_after",
                            "type": "string",
                            "required": True,
                            "description": "文件编辑后的完整代码内容（保留原始格式、空行，确保行号精准）"
                        },
                        {
                            "name": "session_info",
                            "type": "string",
                            "required": False,
                            "description": "会话补充信息（如用户指令、Agent类型、操作时间），用于后续统计筛选"
                        }
                    ]
                }
            ]
        }
    ]
    
    return {
        "version": "1.0.0",
        "tools": tools,
        "server_info": {
            "name": "本地MCP Server AI代码统计系统",
            "description": "基于MCP协议的AI代码统计工具"
        }
    }

