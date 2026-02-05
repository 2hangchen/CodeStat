## CodeStat · AI 代码指标面板

> 量化你对 AI 编程助手的真实使用效果，而不仅仅是“感觉”。

`CodeStat` 是一个 **本地** 的 AI 代码统计工具，用来分析：

- 有多少代码行是 AI 生成的？
- 其中有多少被真正保留在最终代码里？
- 在不同文件 / 会话 / 项目之间，AI 的贡献情况有什么差异？

> English README: [`README.md`](./README.md)

---

## 功能亮点

- **全局看板（Global Dashboard）**
  - 汇总所有本地数据：AI 生成行数、采纳行数、采纳率、生成率、文件数、会话数  
  - 一眼看到 AI 对你整体代码库的贡献度

- **三种维度查询**
  - **按文件**：某个文件里有多少是 AI 写的、留住了多少  
  - **按会话**：某次编码会话的详细指标和 diff 行  
  - **按项目**：整个仓库的宏观统计

- **多 Agent / 多模型对比**
  - 将不同会话映射到不同 Agent / 模型 / Prompt  
  - 用 Compare Agents 看谁的“有效代码行”更多

- **完全本地，保护隐私**
  - 所有数据都来自你本机的 diff 和会话记录  
  - 不上传源码、不上传对话内容

- **体验友好的 CLI**
  - `rich` 渲染的表格和颜色、极简头部、方向键菜单  
  - Windows / Linux / macOS 终端体验统一

---

## 快速上手

### 安装

从 PyPI 安装（推荐）：

```bash
pip install aicodestat
```

从源码安装：

```bash
git clone https://github.com/2hangchen/CodeStat.git
cd CodeStat
pip install -r requirements.txt
```

### 启动 CLI

```bash
python .\cli\main.py
```

- 顶部会显示 MCP Server 在线状态  
- 用 **↑/↓** 选择菜单，回车确认  
- 选择 **“📈 Global Dashboard (All Data)”** 查看全局看板

---

## 典型使用场景

- **个人开发者：量化自己的 AI 使用习惯**
  - 统计最近一段时间 AI 生成 / 采纳的代码行数  
  - 找出哪些文件对 AI 依赖最多

- **团队 / 负责人：评估 AI 引入效果**
  - 以项目为维度看整体 AI 贡献度  
  - 判断 AI 是否真的提高了可维护的代码产出，而不是只增加 churn

- **Prompt / Agent 实验**
  - 不同 Prompt / 模型开几轮实验，各生成一个会话  
  - 用 Compare Agents 看谁的“有效代码行”更多
