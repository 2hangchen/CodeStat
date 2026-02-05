"""可选，封装不同Agent字段名差异的映射"""
from typing import Dict, Any, Optional

# Agent参数映射表
AGENT_FIELD_MAPPINGS = {
    "cursor": {
        "file_path": "file_path",
        "target_file": "file_path",  # 别名
    },
    "claude": {
        "file_path": "file_path",
        "target_file": "file_path",
    },
    "trea": {
        "file_path": "file_path",
    },
    "qoder": {
        "file_path": "file_path",
    }
}


def normalize_request_params(agent_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    标准化不同Agent的请求参数
    
    Args:
        agent_type: Agent类型（cursor/claude/trea/qoder）
        params: 原始请求参数
    
    Returns:
        标准化后的参数
    """
    agent_type_lower = agent_type.lower()
    mapping = AGENT_FIELD_MAPPINGS.get(agent_type_lower, {})
    
    normalized = params.copy()
    
    # 字段映射
    for alias, target_field in mapping.items():
        if alias in normalized and alias != target_field:
            if target_field not in normalized:
                normalized[target_field] = normalized[alias]
            del normalized[alias]
    
    return normalized


def detect_agent_type(session_info: Optional[str]) -> str:
    """
    从session_info中检测Agent类型
    
    Args:
        session_info: 会话信息字符串
    
    Returns:
        Agent类型（默认返回"unknown"）
    """
    if not session_info:
        return "unknown"
    
    session_info_lower = session_info.lower()
    
    for agent_type in ["cursor", "claude", "trea", "qoder"]:
        if agent_type in session_info_lower:
            return agent_type
    
    return "unknown"

