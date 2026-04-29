# ADR-0002: Rust Runtime、TypeScript TUI 与 Python Worker

Status: accepted

Date: 2026-04-26

## Context

Vanta 需要同时满足高性能、交互表现力和 pwn 工具生态接入。Rust 适合构建可靠
runtime，TypeScript 适合实现 Claude Code-like TUI，Python 是 pwn 工具生态
的事实标准。

## Decision

Vanta 采用三层跨语言架构：

1. Rust 作为主 runtime 和 CLI 入口。
2. TypeScript 负责 TUI 表现层。
3. Python 负责 pwn worker。

跨语言通信使用 JSON-RPC over stdio。Rust runtime 是权限、workspace、tool
supervisor 和 evidence 的控制层。

## Consequences

1. 可以同时利用 Rust 的可靠性、TypeScript 的 TUI 表现力和 Python 的 pwn
   生态。
2. 需要维护稳定的进程通信协议。
3. TUI 不持有业务真相，避免 UI 和核心状态耦合。
