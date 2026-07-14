---
type: codex-project-memory
status: active
project: codex-obsidian-memory
path: /Users/bea/Desktop/obsidian
updated: 2026-07-10
---

# Codex Obsidian Memory

## 目标

- 用 Obsidian Markdown 保存用户可查看、可编辑的长期记忆。
- 通过本地检索和 MCP 让 Codex 按需读取相关记忆并保留来源。
- 将通用代码和模板开源，同时避免上传真实客户数据、认证秘密和生成索引。

## RAG v0 决策

- 第一版采用本地 SQLite FTS5 词法检索，不依赖 API Key 或云端向量数据库。
- Markdown 是唯一事实来源；`.rag/index.sqlite3` 是可删除、可重建的派生缓存。
- 按 Markdown 标题切分，并在每个结果中返回文件路径和章节引用。
- MCP 只暴露只读工具 `search_memory` 和 `read_note`。
- 语义向量检索、OCR、自动监听和 reranking 留到后续版本。
- Relay MCP 负责执行外部自动化；本地 Memory MCP 负责知识检索，二者保持分离。

## 安全约束

- 生成索引不提交 Git。
- 公开仓库只保存通用代码、模板和虚构示例。
- 真实公司运营数据应使用单独的私有 Vault。

## 当前状态

- RAG v0 核心、CLI、测试、MCP Server 和文档已实现。
- 下一阶段：在新 Codex 任务中加载本地 Memory MCP，并用虚构数据完成端到端测试。
