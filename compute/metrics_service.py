"""指标服务层：对外提供统一指标计算接口"""
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from storage.models import get_session_summaries, get_code_diff_lines
from compute.lcs_engine import lcs_calculate, calculate_adoption_rate, calculate_generation_rate
from compute.cache import get_cache

logger = logging.getLogger(__name__)


def read_file_lines(file_path: str) -> List[str]:
    """
    从文件系统读取最新文件内容，分割为行
    
    Args:
        file_path: 文件路径
    
    Returns:
        文件行列表
    """
    try:
        file = Path(file_path)
        if not file.exists():
            logger.warning(f"File not found: {file_path}")
            return []
        
        with open(file, 'r', encoding='utf-8', errors='ignore') as f:
            return f.readlines()
    except Exception as e:
        logger.error(f"Failed to read file {file_path}: {e}")
        return []


def calculate_session_metrics(session_id: str) -> Dict[str, Any]:
    """
    计算会话维度的指标
    
    Args:
        session_id: 会话ID
    
    Returns:
        指标字典，包含：
        - ai_total_lines: AI生成总行数
        - adopted_lines: 采纳行数
        - adoption_rate: 采纳率
        - generation_rate: 生成率（按所有涉及文件的总行数计算）
        - file_count: 涉及文件数
        - summaries: 会话汇总列表
        - diff_lines: 差异行列表
    """
    cache = get_cache()
    cache_key = f"session_metrics:{session_id}"
    
    # 检查缓存
    cached_result = cache.get(cache_key)
    if cached_result is not None:
        logger.debug(f"Using cached metrics for session {session_id}")
        return cached_result
    
    # 获取会话汇总
    summaries = get_session_summaries(session_id=session_id)
    
    if not summaries:
        return {
            "session_id": session_id,
            "ai_total_lines": 0,
            "adopted_lines": 0,
            "adoption_rate": 0.0,
            "generation_rate": 0.0,
            "file_count": 0,
            "summaries": [],
            "diff_lines": []
        }
    
    # 获取所有差异行
    all_diff_lines = get_code_diff_lines(session_id=session_id)
    
    # 计算AI生成总行数
    ai_total_lines = len(all_diff_lines)
    
    # 按文件分组计算采纳行数
    file_groups: Dict[str, List[Dict[str, Any]]] = {}
    for diff_line in all_diff_lines:
        file_path = diff_line["file_path"]
        if file_path not in file_groups:
            file_groups[file_path] = []
        file_groups[file_path].append(diff_line)
    
    total_adopted_lines = 0
    total_file_lines = 0
    
    for file_path, diff_lines in file_groups.items():
        # 读取文件最新内容
        latest_lines = read_file_lines(file_path)
        total_file_lines += len(latest_lines)
        
        # 提取AI生成的差异行内容
        ai_diff_content = [d["line_content"] for d in diff_lines]
        
        # 计算LCS（采纳行数）
        adopted = lcs_calculate(ai_diff_content, latest_lines)
        total_adopted_lines += adopted
    
    # 计算指标
    adoption_rate = calculate_adoption_rate(ai_total_lines, total_adopted_lines)
    generation_rate = calculate_generation_rate(ai_total_lines, total_file_lines) if total_file_lines > 0 else 0.0
    
    result = {
        "session_id": session_id,
        "ai_total_lines": ai_total_lines,
        "adopted_lines": total_adopted_lines,
        "adoption_rate": adoption_rate,
        "generation_rate": generation_rate,
        "file_count": len(file_groups),
        "summaries": summaries,
        "diff_lines": all_diff_lines
    }
    
    # 缓存结果
    cache.set(cache_key, result)
    
    return result


def calculate_file_metrics(file_path: str) -> Dict[str, Any]:
    """
    计算文件维度的指标
    
    Args:
        file_path: 文件路径
    
    Returns:
        指标字典
    """
    cache = get_cache()
    cache_key = f"file_metrics:{file_path}"
    
    # 检查缓存
    cached_result = cache.get(cache_key)
    if cached_result is not None:
        logger.debug(f"Using cached metrics for file {file_path}")
        return cached_result
    
    # 获取文件相关的所有会话汇总
    summaries = get_session_summaries(file_path=file_path)
    
    if not summaries:
        return {
            "file_path": file_path,
            "ai_total_lines": 0,
            "adopted_lines": 0,
            "adoption_rate": 0.0,
            "generation_rate": 0.0,
            "session_count": 0,
            "summaries": [],
            "diff_lines": []
        }
    
    # 获取所有差异行
    all_diff_lines = get_code_diff_lines(file_path=file_path)
    
    # 计算AI生成总行数
    ai_total_lines = len(all_diff_lines)
    
    # 读取文件最新内容
    latest_lines = read_file_lines(file_path)
    total_file_lines = len(latest_lines)
    
    # 提取AI生成的差异行内容
    ai_diff_content = [d["line_content"] for d in all_diff_lines]
    
    # 计算LCS（采纳行数）
    adopted_lines = lcs_calculate(ai_diff_content, latest_lines)
    
    # 计算指标
    adoption_rate = calculate_adoption_rate(ai_total_lines, adopted_lines)
    generation_rate = calculate_generation_rate(ai_total_lines, total_file_lines) if total_file_lines > 0 else 0.0
    
    result = {
        "file_path": file_path,
        "ai_total_lines": ai_total_lines,
        "adopted_lines": adopted_lines,
        "adoption_rate": adoption_rate,
        "generation_rate": generation_rate,
        "session_count": len(summaries),
        "summaries": summaries,
        "diff_lines": all_diff_lines
    }
    
    # 缓存结果
    cache.set(cache_key, result)
    
    return result


def calculate_project_metrics(project_root: str) -> Dict[str, Any]:
    """
    计算项目维度的指标
    
    Args:
        project_root: 项目根目录路径
    
    Returns:
        指标字典
    """
    cache = get_cache()
    cache_key = f"project_metrics:{project_root}"
    
    # 检查缓存
    cached_result = cache.get(cache_key)
    if cached_result is not None:
        logger.debug(f"Using cached metrics for project {project_root}")
        return cached_result
    
    # 获取所有会话汇总
    all_summaries = get_session_summaries()
    
    # 过滤出项目内的文件
    project_path = Path(project_root).resolve()
    project_summaries = [
        s for s in all_summaries
        if Path(s["file_path"]).resolve().is_relative_to(project_path)
    ]
    
    if not project_summaries:
        return {
            "project_root": project_root,
            "ai_total_lines": 0,
            "adopted_lines": 0,
            "adoption_rate": 0.0,
            "generation_rate": 0.0,
            "file_count": 0,
            "session_count": 0,
            "summaries": [],
            "diff_lines": []
        }
    
    # 获取所有相关差异行
    project_files = {s["file_path"] for s in project_summaries}
    all_diff_lines = []
    for file_path in project_files:
        all_diff_lines.extend(get_code_diff_lines(file_path=file_path))
    
    # 计算AI生成总行数
    ai_total_lines = len(all_diff_lines)
    
    # 按文件分组计算采纳行数
    total_adopted_lines = 0
    total_file_lines = 0
    
    file_groups: Dict[str, List[Dict[str, Any]]] = {}
    for diff_line in all_diff_lines:
        file_path = diff_line["file_path"]
        if file_path not in file_groups:
            file_groups[file_path] = []
        file_groups[file_path].append(diff_line)
    
    for file_path, diff_lines in file_groups.items():
        latest_lines = read_file_lines(file_path)
        total_file_lines += len(latest_lines)
        
        ai_diff_content = [d["line_content"] for d in diff_lines]
        adopted = lcs_calculate(ai_diff_content, latest_lines)
        total_adopted_lines += adopted
    
    # 计算指标
    adoption_rate = calculate_adoption_rate(ai_total_lines, total_adopted_lines)
    generation_rate = calculate_generation_rate(ai_total_lines, total_file_lines) if total_file_lines > 0 else 0.0
    
    result = {
        "project_root": project_root,
        "ai_total_lines": ai_total_lines,
        "adopted_lines": total_adopted_lines,
        "adoption_rate": adoption_rate,
        "generation_rate": generation_rate,
        "file_count": len(file_groups),
        "session_count": len(set(s["session_id"] for s in project_summaries)),
        "summaries": project_summaries,
        "diff_lines": all_diff_lines
    }
    
    # 缓存结果
    cache.set(cache_key, result)
    
    return result


def calculate_global_metrics() -> Dict[str, Any]:
    """
    计算全局（所有项目 / 会话）的总体指标，用于全局看板。
    """
    cache = get_cache()
    cache_key = "global_metrics"

    cached_result = cache.get(cache_key)
    if cached_result is not None:
        logger.debug("Using cached global metrics")
        return cached_result

    # 获取所有会话汇总
    all_summaries = get_session_summaries()
    if not all_summaries:
        result = {
            "ai_total_lines": 0,
            "adopted_lines": 0,
            "adoption_rate": 0.0,
            "generation_rate": 0.0,
            "file_count": 0,
            "session_count": 0,
            "summaries": [],
            "diff_lines": [],
        }
        cache.set(cache_key, result)
        return result

    # 关联所有文件与差异行
    all_files = {s["file_path"] for s in all_summaries}
    all_diff_lines: List[Dict[str, Any]] = []
    for file_path in all_files:
        all_diff_lines.extend(get_code_diff_lines(file_path=file_path))

    ai_total_lines = len(all_diff_lines)

    total_adopted_lines = 0
    total_file_lines = 0
    file_groups: Dict[str, List[Dict[str, Any]]] = {}

    for diff_line in all_diff_lines:
        file_path = diff_line["file_path"]
        if file_path not in file_groups:
            file_groups[file_path] = []
        file_groups[file_path].append(diff_line)

    for file_path, diff_lines in file_groups.items():
        latest_lines = read_file_lines(file_path)
        total_file_lines += len(latest_lines)

        ai_diff_content = [d["line_content"] for d in diff_lines]
        adopted = lcs_calculate(ai_diff_content, latest_lines)
        total_adopted_lines += adopted

    adoption_rate = calculate_adoption_rate(ai_total_lines, total_adopted_lines)
    generation_rate = (
        calculate_generation_rate(ai_total_lines, total_file_lines)
        if total_file_lines > 0
        else 0.0
    )

    result = {
        "ai_total_lines": ai_total_lines,
        "adopted_lines": total_adopted_lines,
        "adoption_rate": adoption_rate,
        "generation_rate": generation_rate,
        "file_count": len(file_groups),
        "session_count": len(set(s["session_id"] for s in all_summaries)),
        "summaries": all_summaries,
        "diff_lines": all_diff_lines,
    }

    cache.set(cache_key, result)
    return result
