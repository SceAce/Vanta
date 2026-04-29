# ADR-0003: 工具运行时与权限模型

Status: accepted

Date: 2026-04-26

## Context

Agent 会调用本地命令、GDB、IDA MCP、远程连接和 exploit 脚本。没有权限分级
会导致误执行、误写文件、误连目标或发送未授权 payload。

## Decision

所有工具必须声明 risk level：

1. `read-only`
2. `write workspace`
3. `execute local`
4. `network`
5. `exploit`
6. `write outside workspace`

默认策略：

1. `read-only` 自动允许。
2. `write workspace` 自动允许。
3. `execute local` 在 CTF 模式首次确认。
4. `network` 对同一 target 首次确认。
5. `exploit` 对同一 payload 首次确认。
6. `write outside workspace` 每次确认。

同一 payload 用 payload sha256 和 target 标识判断。

## Consequences

1. 用户可以信任 Agent 不会静默执行高风险动作。
2. 权限事件必须写入 transcript。
3. 插件和内置工具都必须服从同一权限系统。
