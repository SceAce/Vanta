# Python Coding Style

## Scope

适用于 `tools/`、`scripts/` 和未来 Python pwn worker。

## Formatter & Linter

1. Ruff：规则 E、F、I、UP、B。
2. line length：100。
3. mypy strict。
4. pytest。

## Type Annotations

1. 所有函数签名必须有类型注解。
2. 每个 module 顶部使用 `from __future__ import annotations`。

## Pwn Worker 规则

1. Python worker 通过 JSON-RPC over stdio 与 Rust runtime 通信。
2. worker 不自行绕过 runtime 权限系统。
3. worker 输出必须结构化，避免把超长 stdout 直接塞给模型。
4. GDB、IDA MCP、pwntools 执行结果必须返回 evidence-friendly 摘要。
5. API key 不得写入 worker 日志。
6. 本机敏感信息写入 transcript 前必须 scrub。

## Error Handling

1. 使用具体异常类型。
2. 禁止裸 `except`。
3. 脚本退出使用 `raise SystemExit()` 或 `sys.exit()`。

## Testing

1. 测试文件放在相邻 `tests/` 目录。
2. 测试函数命名 `test_<scenario>()`。
3. 真实模型、IDA MCP 和完整 GDB 环境测试默认作为手动测试。
