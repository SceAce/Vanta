# Backlog

## 0. 治理与框架

- [x] 从 Trellis scaffold 初始化仓库
- [x] 将 API key 治理调整为只允许 `$HOME/.vanta/` 本机存储
- [x] 补齐 Vanta 产品、需求、架构和 ADR 文档
- [ ] 配置 Cargo workspace
- [ ] 配置 `.config/arch-boundaries.toml`
- [ ] 建立 CI pipeline

## 1. Vanta Core

- [ ] Rust CLI 入口 `vanta`
- [ ] `$HOME/.vanta/` 用户配置
- [ ] `.vanta/` workspace 初始化
- [ ] permission engine
- [ ] tool supervisor
- [ ] transcript writer
- [ ] evidence ref writer
- [ ] provider adapter
- [ ] model profiles
- [ ] provider fallback

## 2. TUI

- [ ] TypeScript TUI scaffold
- [ ] 对话面板
- [ ] 状态面板
- [ ] 文件/facts 面板
- [ ] 折叠工具日志
- [ ] 权限确认弹层
- [ ] slash command 补全
- [ ] transcript replay 视图

## 3. Python Pwn Worker

- [ ] JSON-RPC over stdio server
- [ ] ELF triage tools
- [ ] IDA MCP 自动启动和调用
- [ ] GDB worker/MCP
- [ ] pwndbg 集成
- [ ] pwntools exploit runner
- [ ] ROPGadget/ropper/one_gadget wrappers

## 4. Pwn Workflows

- [ ] `/triage`
- [ ] `/crash`
- [ ] `/offset`
- [ ] `/gdb`
- [ ] `/exploit`
- [ ] `/report`
- [ ] `/vanta-solve`
- [ ] ret2win demo
- [ ] ret2libc demo
- [ ] ROP demo
- [ ] format string workflow
- [ ] heap workflow

## 5. 测试与 Benchmark

- [ ] fixture 测试目录
- [ ] ret2win C fixture
- [ ] mock provider tests
- [ ] JSON-RPC contract tests
- [ ] GDB smoke tests
- [ ] IDA MCP manual test checklist
- [ ] `triage-small-elf` benchmark
- [ ] `offset-ret2win` benchmark
- [ ] `exploit-ret2win` benchmark
