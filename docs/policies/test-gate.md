# Test Gate

## Hard Rule

提交前必须通过：

```bash
bash scripts/verify.sh
```

## Testing Discipline

1. 行为变更必须有测试或手动验证证据。
2. 协议变更必须更新 schema 和 contract tests。
3. 权限策略变更必须有 regression tests。
4. 安全边界变更必须更新 `docs/security-model.md`。
5. 工具输出格式变更必须更新 evidence 和 replay 测试。

## Required Actions

| Change                | Required Action                     |
| --------------------- | ----------------------------------- |
| 新 tool               | 添加 input/output schema 和权限测试 |
| 新 slash command      | 添加解析测试和 TUI 手动验证         |
| 新 provider           | 添加 mock provider 测试             |
| 新 worker method      | 添加 JSON-RPC contract test         |
| GDB worker 变化       | 添加或更新 GDB smoke 测试           |
| IDA MCP 变化          | 更新手动测试 checklist              |
| Workspace schema 变化 | 更新 schema version 和 migration    |
| API key handling 变化 | 人类审批并更新安全文档              |
