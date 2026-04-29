# ADR-0005: IDA MCP 与 GDB Worker

Status: accepted

Date: 2026-04-26

## Context

Vanta 需要伪代码级程序分析和动态调试能力。`objdump` 能提供基础反汇编，但不
能替代 decompiler。GDB 是 pwn 动态分析核心工具，需要与 Agent 稳定集成。

## Decision

IDA MCP 是第一阶段强增强能力。Vanta 尝试自动启动并调用 IDA MCP；如果 IDA
不可用，则提醒用户并降级到 `objdump`、`readelf`、`strings`、`nm` 等基础
工具。

GDB 能力由 Vanta 自研 GDB worker 或 GDB MCP 提供。第一版采用长驻 session，
直到对话结束或用户手动结束。GDB worker 支持 pwndbg、core dump、cyclic
offset 和需要时的 registers、stack、maps、backtrace 提取。

## Consequences

1. 有 IDA 时获得高质量伪代码分析。
2. 没有 IDA 时系统仍可运行。
3. 长驻 GDB session 状态管理复杂，需要 transcript 和 evidence 记录每个关键动作。
