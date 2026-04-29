# 架构总览

## 架构目标

Vanta 的架构目标是把 Claude Code-like 的交互体验、可审计的 Agent runtime、
和 pwn 领域工具链结合起来。UI 可以快速演进，但核心 runtime、工具协议、
workspace 格式和 evidence store 必须稳定、可测试、可复现。

## 总体分层

```text
用户
  |
  v
TypeScript TUI
  |
  v
Rust Runtime
  |
  +-- Provider Adapter
  +-- Permission Engine
  +-- Workspace Manager
  +-- Tool Supervisor
  |
  v
Python Pwn Worker
  |
  +-- IDA MCP
  +-- GDB Worker / MCP
  +-- pwntools
  +-- ELF 工具
```

## Rust Runtime

Rust runtime 是主进程和可信控制层，负责：

1. CLI 入口 `vanta`。
2. 配置读取，包括 `$HOME/.vanta/`。
3. 权限判断。
4. workspace 管理。
5. tool supervisor。
6. provider adapter。
7. transcript 和 evidence 事件写入。

Rust runtime 不直接实现所有 pwn 分析细节，而是通过协议调用 Python worker。

## TypeScript TUI

TypeScript TUI 负责交互表现：

1. 多面板布局。
2. 对话流。
3. 状态面板。
4. 折叠工具日志。
5. slash command 输入。
6. 权限确认弹层。
7. transcript replay 展示。

TUI 不是业务真相来源。它消费 runtime 事件，并把用户输入交给 runtime。

## Python Pwn Worker

Python worker 承接 pwn 生态：

1. `pwntools`。
2. GDB 自动化。
3. pwndbg。
4. IDA MCP 调用。
5. ROPGadget、ropper、one_gadget。
6. `file`、`checksec`、`readelf`、`objdump`、`strings`、`nm` 的结构化封装。

Python worker 通过 JSON-RPC over stdio 与 Rust runtime 通信。

## Workspace

项目内 workspace 使用 `.vanta/`：

```text
.vanta/
  workspace.json
  session.jsonl
  facts.json
  tool-runs.jsonl
  pwn/
    case.json
    crashes/
    payloads/
    exploits/
    reports/
    gdb/
    ida/
    runs/
      <run_id>/
        run.json
        static-scan.json
        breakpoint-plan.json
        dynamic-verify.json
        poc-draft.json
    knowledge/
      patterns.json
```

所有关键文件带 `schema_version`。未来格式变化通过 migration 升级。

## Tool Runtime

工具定义必须包含：

1. name。
2. input schema。
3. output schema。
4. risk level。
5. timeout。
6. permission policy。
7. evidence writer。

默认权限策略：

1. `read-only` 自动允许。
2. `write workspace` 自动允许。
3. `execute local` 在 CTF 模式首次确认。
4. `network` 对同一 target 首次确认。
5. `exploit` 对同一 payload 首次确认。
6. `write outside workspace` 每次确认。

## Evidence

Agent 的结论必须尽量绑定 evidence ref。关键证据包括：

1. binary hash。
2. tool run 输入和输出摘要。
3. crash dump。
4. payload hash。
5. exploit run 结果。
6. generated report。

## Provider

MVP 支持 DeepSeek、OpenAI、Anthropic、本地 llama。provider fallback 和 model
profiles 是 runtime 能力，但真实模型调用测试不进入默认 CI。

当前 CLI 闭环优先实现 OpenAI-compatible provider 和本地 CUDA llama 进程
fallback。provider 配置只从 `$HOME/.vanta/providers.json` 读取；OpenAI 请求
失败、超时、认证缺失或网络错误时自动切换本地 llama 进程。provider 日志和
artifact 只记录 provider 名称、模型名、fallback 状态和摘要，不记录 API key。

## 安全模式

1. `ctf`：默认可执行，首次提示。
2. `research`：默认不可信，执行前强确认。
3. `malware`：默认只允许静态分析或隔离执行。
