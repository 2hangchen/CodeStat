"""RecordAfterEdit 相关 FastAPI 路由，调用差异提取与存储层"""
import logging
from fastapi import APIRouter, HTTPException
from mcp.api_schemas import RecordAfterEditRequest, MCPResponse
from storage.models import (
    get_before_edit,
    delete_before_edit,
    save_session_summary,
    save_code_diff_lines
)
from compute.diff_engine import extract_diff_lines

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/mcp", tags=["MCP Tools"])


@router.post("/record_after", response_model=MCPResponse)
async def record_after_edit(request: RecordAfterEditRequest):
    """
    RecordAfterEdit Tool: 记录文件编辑后的代码，提取差异行并存储
    
    该Tool由Agent在编辑文件后调用，会：
    1. 从临时表读取编辑前的代码
    2. 计算差异行（新增/修改）
    3. 存储到会话汇总表和差异行明细表
    4. 清理临时数据
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
        
        if not request.code_after:
            raise HTTPException(
                status_code=400,
                detail="code_after不能为空"
            )
        
        # 获取编辑前的代码
        code_before = get_before_edit(request.session_id, request.file_path)
        if code_before is None:
            raise HTTPException(
                status_code=404,
                detail=f"未找到编辑前的代码记录，请先调用RecordBeforeEdit Tool (session_id={request.session_id}, file_path={request.file_path})"
            )
        
        # 提取差异行
        diff_lines = extract_diff_lines(code_before, request.code_after)
        
        # 统计新增和修改行数
        add_lines_count = sum(1 for d in diff_lines if d["diff_type"] == "add")
        modify_lines_count = sum(1 for d in diff_lines if d["diff_type"] == "modify")
        
        # 计算编辑后文件总行数
        total_lines_after = len(request.code_after.split("\n"))
        
        # 保存会话汇总
        success = save_session_summary(
            session_id=request.session_id,
            file_path=request.file_path,
            add_lines_count=add_lines_count,
            modify_lines_count=modify_lines_count,
            total_lines_after=total_lines_after,
            session_info=request.session_info
        )
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="保存会话汇总失败"
            )
        
        # 保存差异行明细
        if diff_lines:
            success = save_code_diff_lines(
                session_id=request.session_id,
                file_path=request.file_path,
                diff_lines=diff_lines
            )
            
            if not success:
                logger.warning("保存差异行明细失败，但会话汇总已保存")
        
        # 清理临时数据
        delete_before_edit(request.session_id, request.file_path)
        
        logger.info(
            f"RecordAfterEdit: session={request.session_id}, file={request.file_path}, "
            f"add={add_lines_count}, modify={modify_lines_count}, total_diff={len(diff_lines)}"
        )
        
        return MCPResponse(
            status="success",
            message="编辑后代码记录成功，差异行已提取并存储",
            data={
                "add_lines_count": add_lines_count,
                "modify_lines_count": modify_lines_count,
                "total_diff_lines": len(diff_lines),
                "total_lines_after": total_lines_after
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"RecordAfterEdit error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"内部错误: {str(e)}"
        )

