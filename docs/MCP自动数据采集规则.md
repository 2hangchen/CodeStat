# MCP 自动数据采集规则

## 核心原则

- **有文件内容变更** → 必须记录
- **无文件内容变更** → 不需要记录
- **会话级别记录** → 每轮对话结束时记录会话元数据

## 触发条件

### 文件内容变更操作前
在执行以下操作**之前**，必须先调用 `RecordBeforeEdit`：
- `write` - 写入文件
- `search_replace` - 搜索替换内容
- `MultiEdit` - 多文件编辑
- `create_file` - 创建新文件
- `delete_file` - 删除文件
- `edit_notebook` - 编辑Jupyter Notebook
- 其他任何会修改文件内容的操作

### 文件内容变更操作后
在文件变更操作**完成后**，必须调用 `RecordAfterEdit`。

### 对话结束
每轮对话结束时，确保所有文件变更已记录。会话信息已通过 `RecordAfterEdit` 的 `session_info` 参数记录。

## 操作分类

### 需要MCP记录的操作（文件内容变更）

| 操作类型 | 工具名称 | 说明 |
|---------|---------|------|
| `create_file` | `RecordBeforeEdit` → `RecordAfterEdit` | 创建新文件（before为空内容） |
| `delete_file` | `RecordBeforeEdit` → `RecordAfterEdit` | 删除文件（after为空内容） |
| `search_replace` | `RecordBeforeEdit` → `RecordAfterEdit` | 搜索替换内容 |
| `write` | `RecordBeforeEdit` → `RecordAfterEdit` | 写入文件（覆盖） |
| `edit_file` | `RecordBeforeEdit` → `RecordAfterEdit` | 编辑文件内容 |
| `edit_notebook` | `RecordBeforeEdit` → `RecordAfterEdit` | 编辑Notebook |

### 不需要MCP记录的操作（只读操作）

| 操作类型 | 说明 |
|---------|------|
| `read_file` | 读取文件内容 |
| `list_dir` | 列出目录 |
| `grep` | 搜索文件内容 |
| `codebase_search` | 代码库搜索 |
| `glob_file_search` | 文件搜索 |
| `read_lints` | 读取linter错误 |
| 其他只读操作 | 任何不修改文件内容的操作 |

## 执行流程

### 场景1：纯对话（无文件变更）
```
对话结束 → 无需MCP调用
```

### 场景2：单文件内容变更
```
RecordBeforeEdit(file_path, code_before) 
  → [文件变更操作] 
  → RecordAfterEdit(file_path, code_after, session_info)
```

### 场景3：多文件内容变更
```
# 文件1
RecordBeforeEdit(file1_path, code_before_1) 
  → [文件变更操作1] 
  → RecordAfterEdit(file1_path, code_after_1, session_info)

# 文件2
RecordBeforeEdit(file2_path, code_before_2) 
  → [文件变更操作2] 
  → RecordAfterEdit(file2_path, code_after_2, session_info)
```

### 场景4：只读分析操作（不触发MCP）
```
[读取分析操作] → 分析结果 → 无需MCP调用
```

## 工具调用规范

### RecordBeforeEdit

**端点**：`POST /mcp/record_before`

**参数**：
```json
{
  "session_id": "string (required)",
  "file_path": "string (required, 绝对路径)",
  "code_before": "string (required, 文件编辑前的完整代码内容)"
}
```

**调用时机**：
- 在文件变更操作**之前**立即调用
- 必须读取文件当前内容作为 `code_before`

**注意事项**：
- `session_id` 必须在整个对话中保持一致
- `file_path` 必须是绝对路径
- `code_before` 必须包含完整文件内容（包括空行）

### RecordAfterEdit

**端点**：`POST /mcp/record_after`

**参数**：
```json
{
  "session_id": "string (required, 需与RecordBeforeEdit一致)",
  "file_path": "string (required, 需与RecordBeforeEdit一致)",
  "code_after": "string (required, 文件编辑后的完整代码内容)",
  "session_info": "string (optional, 会话补充信息)"
}
```

**调用时机**：
- 在文件变更操作**完成后**立即调用
- 必须读取文件新内容作为 `code_after`

**注意事项**：
- `session_id` 和 `file_path` 必须与对应的 `RecordBeforeEdit` 完全一致
- `code_after` 必须包含完整文件内容（包括空行）
- `session_info` 建议包含：Agent类型、用户指令、操作时间

### 会话信息记录

**说明**：
- 会话信息通过 `RecordAfterEdit` 的 `session_info` 参数记录
- 系统会自动汇总到 `session_summary` 表中
- 无需单独调用会话记录工具

## 强制要求

### 1. 100%覆盖
- ✅ 不允许任何文件内容变更操作遗漏记录
- ✅ 每个文件变更操作必须完整配对（before + after）

### 2. 严格配对
- ✅ 每次 `RecordBeforeEdit` 必须有且仅有一次对应的 `RecordAfterEdit` 调用
- ✅ 不允许遗漏、跳过或合并操作
- ✅ 不允许一个 `RecordBeforeEdit` 对应多个 `RecordAfterEdit`

### 3. 会话一致性
- ✅ 整个对话开始时应确定一个统一的 `session_id`
- ✅ 所有后续文件变更操作中保持该 `session_id` 不变
- ✅ `session_id` 建议格式：`{AgentName}_{Timestamp}_{RandomString}`
  - 示例：`Cursor_1735689000_abc123`

### 4. 绝对路径
- ✅ 必须使用文件的绝对路径
- ✅ 不允许使用相对路径
- ✅ 路径格式应与操作系统一致（Windows使用 `\`，Unix使用 `/`）

### 5. 即时调用
- ✅ `RecordBeforeEdit` 必须在文件变更操作**之前**立即调用
- ✅ `RecordAfterEdit` 必须在文件变更操作**之后**立即调用
- ✅ 不允许延迟或批量调用

## 违规处理

### 即时检测
- 每次文件操作后立即自检配对完整性
- 检查是否所有 `RecordBeforeEdit` 都有对应的 `RecordAfterEdit`

### 强制纠正
- 发现遗漏立即停止并补充缺失调用
- 如果 `RecordAfterEdit` 找不到对应的 `RecordBeforeEdit`，应返回错误并提示先调用 `RecordBeforeEdit`

### 重新执行
- 违规操作必须重新执行整个流程
- 确保数据完整性

## 常见违规案例

### ❌ 错误示例1：合并记录
```python
# 错误：将多次操作合并到一次RecordAfterEdit调用中
RecordBeforeEdit(file1)
editFile(file1)
RecordBeforeEdit(file2)
editFile(file2)
RecordAfterEdit(file1)  # 错误：缺少file2的RecordAfterEdit
```

### ✅ 正确示例1：完整配对
```python
# 正确：每个文件都有完整的配对
RecordBeforeEdit(file1)
editFile(file1)
RecordAfterEdit(file1)

RecordBeforeEdit(file2)
editFile(file2)
RecordAfterEdit(file2)
```

### ❌ 错误示例2：遗漏配对
```python
# 错误：RecordBeforeEdit后未调用对应的RecordAfterEdit
RecordBeforeEdit(file1)
editFile(file1)
# 遗漏：RecordAfterEdit(file1)
```

### ✅ 正确示例2：完整配对
```python
# 正确：完整的配对流程
RecordBeforeEdit(file1)
editFile(file1)
RecordAfterEdit(file1)
```

### ❌ 错误示例3：跳过记录
```python
# 错误：直接进行文件变更操作而未调用MCP工具
editFile(file1)  # 错误：没有RecordBeforeEdit
```

### ✅ 正确示例3：完整记录
```python
# 正确：完整的记录流程
RecordBeforeEdit(file1)
editFile(file1)
RecordAfterEdit(file1)
```

### ❌ 错误示例4：路径错误
```python
# 错误：使用相对路径
RecordBeforeEdit('./src/file.ts')  # 错误：相对路径
```

### ✅ 正确示例4：绝对路径
```python
# 正确：使用绝对路径
RecordBeforeEdit('/absolute/path/to/src/file.ts')
# 或 Windows
RecordBeforeEdit('E:\\code\\project\\src\\file.ts')
```

### ❌ 错误示例5：错误触发
```python
# 错误：对只读操作也调用RecordBeforeEdit/RecordAfterEdit
RecordBeforeEdit(file1)  # 错误：read_file是只读操作
readFile(file1)
RecordAfterEdit(file1)  # 错误：read_file不应该触发MCP
```

### ✅ 正确示例5：只读操作不触发
```python
# 正确：只读操作不触发MCP工具
readFile(file1)  # 只读操作，不需要MCP调用
```

### ❌ 错误示例6：session_id不一致
```python
# 错误：使用不同的session_id
RecordBeforeEdit(file1, session_id='session1')
editFile(file1)
RecordAfterEdit(file1, session_id='session2')  # 错误：session_id不一致
```

### ✅ 正确示例6：session_id一致
```python
# 正确：使用相同的session_id
session_id = 'Cursor_1735689000_abc123'
RecordBeforeEdit(file1, session_id=session_id)
editFile(file1)
RecordAfterEdit(file1, session_id=session_id)
```

## 验证清单

在执行文件变更操作时，请检查以下项目：

- [ ] 是否在文件变更操作前调用了 `RecordBeforeEdit`？
- [ ] 是否在文件变更操作后调用了 `RecordAfterEdit`？
- [ ] 每个 `RecordBeforeEdit` 是否都有对应的 `RecordAfterEdit`？
- [ ] 是否使用了文件的绝对路径？
- [ ] 是否在整个对话中保持 `session_id` 一致？
- [ ] 是否在 `RecordAfterEdit` 中提供了 `session_info` 信息？
- [ ] 是否对只读操作错误地调用了MCP工具？
- [ ] 是否将多次操作合并到一次 `RecordAfterEdit` 调用中？
- [ ] `session_id` 和 `file_path` 在配对调用中是否完全一致？

## 最佳实践

### 1. Session ID生成
- **格式**：`{AgentName}_{Timestamp}_{RandomString}`
- **示例**：`Cursor_1735689000_abc123`
- **要求**：在整个对话中保持不变

### 2. Session Info格式
- **建议包含**：Agent类型、用户指令、操作时间
- **示例**：`Agent: Cursor, User: 编写排序函数, Time: 2026-02-04 15:30:00`

### 3. 错误处理
- `RecordBeforeEdit` 失败不影响Agent正常编辑（但应记录警告）
- `RecordAfterEdit` 失败时，Agent应记录错误但不阻塞用户操作
- 如果 `RecordAfterEdit` 找不到对应的 `RecordBeforeEdit`，应返回明确的错误信息

### 4. 性能优化
- Tool调用应异步执行，不阻塞主流程（如果Agent支持）
- 对于大文件，考虑只记录关键部分（但需确保差异计算准确）

### 5. 代码内容要求
- `code_before` 和 `code_after` 必须包含完整文件内容
- 保留原始格式、空行，确保行号精准
- 使用原始编码（UTF-8）

## 特殊场景处理

### 场景1：创建新文件
```python
# code_before 应为空字符串
RecordBeforeEdit(file_path, code_before='')
createFile(file_path, content)
RecordAfterEdit(file_path, code_after=content)
```

### 场景2：删除文件
```python
RecordBeforeEdit(file_path, code_before=file_content)
deleteFile(file_path)
# code_after 应为空字符串
RecordAfterEdit(file_path, code_after='')
```

### 场景3：文件重命名
```python
# 旧文件
RecordBeforeEdit(old_path, code_before=old_content)
# 新文件
RecordBeforeEdit(new_path, code_before='')
renameFile(old_path, new_path)
RecordAfterEdit(old_path, code_after='')
RecordAfterEdit(new_path, code_after=old_content)
```

### 场景4：批量操作
```python
# 每个文件都需要独立的配对
for file in files:
    RecordBeforeEdit(file, code_before=read_file(file))
    editFile(file)
    RecordAfterEdit(file, code_after=read_file(file))
```

## 工具发现

Agent可以通过以下端点发现可用工具：

**端点**：`GET /mcp/tools`

**响应**：
```json
{
  "version": "1.0.0",
  "tools": [
    {
      "name": "RecordBeforeEdit",
      "description": "记录文件编辑前的完整代码内容",
      "endpoint": "/mcp/record_before",
      "method": "POST"
    },
    {
      "name": "RecordAfterEdit",
      "description": "记录文件编辑后的代码，提取差异行",
      "endpoint": "/mcp/record_after",
      "method": "POST"
    }
  ]
}
```

## 故障排查

### Tool调用返回404
- 检查MCP Server是否正在运行
- 检查端点路径是否正确（`/mcp/record_before` 或 `/mcp/record_after`）

### Tool调用返回500
- 查看Server日志
- 检查数据库是否正常初始化
- 确认文件路径格式正确

### 数据未记录
- 确认 `RecordBeforeEdit` 和 `RecordAfterEdit` 使用相同的 `session_id` 和 `file_path`
- 检查数据库文件权限
- 查看Server日志中的错误信息

### RecordAfterEdit找不到RecordBeforeEdit
- 确认先调用了 `RecordBeforeEdit`
- 检查 `session_id` 和 `file_path` 是否完全一致
- 检查临时数据是否被意外清理

