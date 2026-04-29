# 产品需求文档

## 背景

CTF pwn 解题过程通常需要在多个工具之间切换：IDA、GDB、pwntools、
checksec、readelf、objdump、ROPgadget、远程连接脚本和 writeup。上下文包括
伪代码、保护信息、寄存器、栈、crash、payload、libc、gadget 和失败尝试。
普通聊天框无法稳定承载这些状态，也难以复现分析过程。

Vanta 的目标是提供一个 Claude Code-like 的终端工作台，让用户通过对话和
slash commands 驱动 Agent 完成半自动化或自动化 pwn 工作流。

## 用户

1. 中高级 pwn 选手。
2. CTF 战队。
3. 安全研究员。
4. 教学场景中的讲师和学习者。

用户默认理解 pwntools、GDB 和基础二进制分析概念。

## 用户价值

1. 将程序分析、调试、利用尝试和报告生成放进同一个可恢复会话。
2. 自动沉淀 facts、crashes、payloads、tool logs 和 evidence refs。
3. 降低重复操作成本，例如 checksec、offset、GDB crash dump、exploit 草稿。
4. 在简单 CTF pwn 题上形成自动拿 flag 的闭环。
5. 在复杂题目上给出高质量伪代码分析、漏洞假设和利用建议。

## 核心需求

### TUI 工作台

1. 输入 `vanta` 后进入终端 TUI。
2. 支持自然语言对话。
3. 支持 slash commands，包括 `/triage`、`/crash`、`/offset`、`/gdb`、
   `/exploit`、`/report`、`/compact`、`/vanta-solve`。
4. 工具日志默认折叠。
5. 状态面板持续展示 checksec、架构、libc、remote target、exploit 状态、
   crash offset、gadget 信息。
6. 支持 session resume 和 transcript replay。

### 程序分析

1. 支持 IDA MCP 自动启动和调用。
2. IDA MCP 缺失时提醒用户，并降级到 `objdump`、`readelf`、`strings`、
   `nm` 等基础工具。
3. 输出 `output.md`，包含伪代码分析、关键函数、攻击面、可疑漏洞点和利用建议。
4. 支持多 binary workspace。

### 动态调试

1. 第一版必须集成 GDB。
2. 自研 GDB MCP 或 GDB worker，采用长驻 session，直到对话结束或用户手动结束。
3. 支持 pwndbg。
4. 支持 core dump 分析。
5. 支持 cyclic offset 自动计算。
6. 需要时提取 registers、stack、maps 和 backtrace。
7. 调试 exploit 脚本时支持 attach。

### 利用生成

1. 自动生成 `exploit.py`。
2. 同一个 payload 首次执行需要确认，后续用 payload sha256 和 target 标识识别。
3. CTF 环境允许自动对远程服务发送 payload；非 CTF 环境需要人类明确授权。
4. demo 必须在简单题目中自动获取 flag。

### Evidence Store

1. 项目内使用隐藏目录 `.vanta/`。
2. workspace 类型名为 `vanta-workspace`。
3. 保存 session transcript、facts、crashes、payloads、generated exploit、
   reports、tool logs、model summaries。
4. facts 使用 JSON，notes 使用 Markdown。
5. 支持 schema version 和 migration。
6. 支持 tool replay 和 transcript replay。

### Provider

1. 支持 DeepSeek、OpenAI、Anthropic、本地 llama。
2. 支持 provider fallback。
3. 支持 model profiles，例如 `fast`、`smart`、`local`。
4. 真实模型测试作为手动测试；默认 CI 使用 mock provider。

## 验收标准

1. 给定一个 Linux ELF，Vanta 能在 TUI 中完成基础分析并生成 `output.md`。
2. 有 IDA MCP 时能提取伪代码分析；无 IDA MCP 时能降级到基础工具。
3. 能通过 GDB worker/MCP 维护长驻 session 并提取 crash 证据。
4. 能生成 `exploit.py`。
5. demo fixture 能自动获取 flag。
6. 所有关键结论都带 evidence ref。
