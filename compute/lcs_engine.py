"""LCS算法引擎：实现 lcs_calculate 与批量计算接口"""
import logging
from typing import List

logger = logging.getLogger(__name__)


def lcs_calculate(ai_diff_lines: List[str], latest_file_lines: List[str]) -> int:
    """
    计算AI生成的差异行与文件最新内容的最长公共子序列（公共行数）
    
    Args:
        ai_diff_lines: AI生成的差异行列表（从code_diff_lines表读取）
        latest_file_lines: 文件最新的代码行列表（读取本地文件）
    
    Returns:
        公共行数（采纳行数）
    """
    # 简化处理：提取非空代码行，去除首尾空白
    ai_lines = [line.strip() for line in ai_diff_lines if line.strip()]
    latest_lines = [line.strip() for line in latest_file_lines if line.strip()]
    
    if not ai_lines or not latest_lines:
        return 0
    
    # 构建LCS动态规划表
    m, n = len(ai_lines), len(latest_lines)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if ai_lines[i-1] == latest_lines[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1
            else:
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])
    
    lcs_length = dp[m][n]
    logger.debug(f"LCS calculation: {len(ai_lines)} AI lines vs {len(latest_lines)} latest lines, LCS={lcs_length}")
    
    return lcs_length


def calculate_adoption_rate(ai_total_lines: int, adopted_lines: int) -> float:
    """
    计算采纳率
    
    Args:
        ai_total_lines: AI生成总行数
        adopted_lines: 采纳行数
    
    Returns:
        采纳率（0-100）
    """
    if ai_total_lines == 0:
        return 0.0
    return round((adopted_lines / ai_total_lines) * 100, 2)


def calculate_generation_rate(ai_total_lines: int, file_total_lines: int) -> float:
    """
    计算生成率
    
    Args:
        ai_total_lines: AI生成总行数
        file_total_lines: 文件最新总行数
    
    Returns:
        生成率（0-100）
    """
    if file_total_lines == 0:
        return 0.0
    return round((ai_total_lines / file_total_lines) * 100, 2)

