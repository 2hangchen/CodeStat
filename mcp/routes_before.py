"""RecordBeforeEdit 相关 FastAPI 路由与业务逻辑"""
import logging
from fastapi import APIRouter, HTTPException
from mcp.api_schemas import RecordBeforeEditRequest, MCPResponse
from storage.models import save_before_edit

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/mcp", tags=["MCP Tools"])


@router.post("/record_before", response_model=MCPResponse)
async def record_before_edit(request: RecordBeforeEditRequest):
    """
    RecordBeforeEdit Tool: 记录文件编辑前的代码
    
    该Tool由Agent在编辑文件前调用，用于临时存储编辑前的代码内容，
    后续RecordAfterEdit Tool会使用此数据进行差异计算。
    """
    try:
        # 参数校验
        if not request.session_id or not request.session_id.strip():
            raise HTTPException(
                status_code=400,
                detail="session_id不能为空"
            )
        
        if not request.file_path or not request.file_path.strip():
            raise HTTPException(
                status_code=400,
                detail="file_path不能为空"
            )
        
        if not request.code_before:
            raise HTTPException(
                status_code=400,
                detail="code_before不能为空"
            )
        
        # 保存编辑前代码
        success = save_before_edit(
            session_id=request.session_id,
            file_path=request.file_path,
            code_before=request.code_before
        )
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="保存编辑前代码失败"
            )
        
        logger.info(f"RecordBeforeEdit: session={request.session_id}, file={request.file_path}")
        
        return MCPResponse(
            status="success",
            message="编辑前代码记录成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"RecordBeforeEdit error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"内部错误: {str(e)}"
        )

