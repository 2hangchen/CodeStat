"""差异提取引擎：封装 extract_diff_lines，用 difflib 实现精准差分"""
import difflib
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


def extract_diff_lines(code_before: str, code_after: str) -> List[Dict[str, Any]]:
    """
    提取具体差异行（新增/修改），返回差异行列表
    
    Args:
        code_before: 编辑前的代码
        code_after: 编辑后的代码
    
    Returns:
        差异行列表，每个元素包含：
        - diff_type: 'add' 或 'modify'
        - line_content: 差异行内容
        - line_number: 差异行在编辑后文件中的行号
    """
    # 拆分代码为行列表（保留空行、原始格式）
    before_lines = code_before.split("\n")
    after_lines = code_after.split("\n")
    
    diff_lines = []
    
    # 使用 SequenceMatcher 计算差异
    matcher = difflib.SequenceMatcher(None, before_lines, after_lines)
    
    # 追踪编辑后文件的行号
    current_after_line = 0
    
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            # 相同部分，更新行号
            current_after_line += (j2 - j1)
        elif tag == 'delete':
            # 删除的行，不记录（因为我们要的是新增/修改）
            pass
        elif tag == 'insert':
            # 新增的行
            for idx, line in enumerate(after_lines[j1:j2]):
                line_content = line.strip()
                if line_content:  # 过滤空的新增行
                    diff_lines.append({
                        "diff_type": "add",
                        "line_content": line_content,
                        "line_number": current_after_line + idx + 1
                    })
            current_after_line += (j2 - j1)
        elif tag == 'replace':
            # 修改的行（先删后加）
            # 我们记录新增的内容作为修改后的差异行
            for idx, line in enumerate(after_lines[j1:j2]):
                line_content = line.strip()
                if line_content:  # 过滤空的修改行
                    diff_lines.append({
                        "diff_type": "modify",
                        "line_content": line_content,
                        "line_number": current_after_line + idx + 1
                    })
            current_after_line += (j2 - j1)
    
    logger.debug(f"Extracted {len(diff_lines)} diff lines: {sum(1 for d in diff_lines if d['diff_type'] == 'add')} add, {sum(1 for d in diff_lines if d['diff_type'] == 'modify')} modify")
    
    return diff_lines

