# ADR-0004: `.vanta/` Workspace 与 Evidence Store

Status: accepted

Date: 2026-04-26

## Context

pwn 解题过程包含大量临时状态：伪代码摘要、工具输出、crash、payload、
exploit、flag、报告和模型摘要。如果这些状态只存在对话上下文中，Agent 会
难以复现和审计。

## Decision

Vanta 在 challenge 目录下创建隐藏目录 `.vanta/`，workspace 类型名为
`vanta-workspace`。

workspace 保存：

1. `session.jsonl`
2. `facts.json`
3. `tool-runs.jsonl`
4. `pwn/case.json`
5. `pwn/crashes/`
6. `pwn/payloads/`
7. `pwn/exploits/`
8. `pwn/reports/`
9. `pwn/gdb/`
10. `pwn/ida/`
11. `pwn/runs/<run_id>/`
12. `pwn/knowledge/patterns.json`

关键文件必须包含 `schema_version`。后续格式变化通过 migration 处理。

## Consequences

1. session resume、transcript replay 和 tool replay 有稳定数据来源。
2. 结论可以绑定 evidence ref。
3. workspace 目录可能包含敏感材料，导出、压缩、删除隐私数据都需要人类确认。
