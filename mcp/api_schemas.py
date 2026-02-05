"""请求/响应 Pydantic 模型"""
from pydantic import BaseModel, Field
from typing import Optional


class RecordBeforeEditRequest(BaseModel):
    """RecordBeforeEdit Tool请求模型"""
    session_id: str = Field(..., description="当前会话ID，由Agent生成，需与RecordAfterEdit的session_id一致")
    file_path: str = Field(..., description="目标文件的绝对路径")
    code_before: str = Field(..., description="文件编辑前的完整代码内容")


class RecordAfterEditRequest(BaseModel):
    """RecordAfterEdit Tool请求模型"""
    session_id: str = Field(..., description="当前会话ID，需与RecordBeforeEdit的session_id一致")
    file_path: str = Field(..., description="目标文件的绝对路径，需与RecordBeforeEdit的file_path一致")
    code_after: str = Field(..., description="文件编辑后的完整代码内容")
    session_info: Optional[str] = Field(None, description="会话补充信息（如用户指令、Agent类型、操作时间）")


class MCPResponse(BaseModel):
    """MCP Tool统一响应模型"""
    status: str = Field(..., description="状态：success 或 error")
    message: str = Field(..., description="响应消息")
    data: Optional[dict] = Field(None, description="响应数据（可选）")

