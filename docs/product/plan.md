# 项目计划

## 近期目标

1. 完成 Vanta 项目文档、治理规则、架构决策和路线图。
2. 建立 Rust 主 runtime、TypeScript TUI、Python pwn worker 的模块边界。
3. 实现 `.vanta/` workspace 和事件日志协议。
4. 接入基础 ELF triage。
5. 接入 IDA MCP 和 GDB worker/MCP 原型。

## 第一里程碑

给定一个 Linux ELF，Vanta 能通过 TUI 调用 IDA MCP、GDB 和基础工具，生成
`output.md`，列出伪代码分析、攻击面、可疑漏洞点和下一步利用建议。

## 第二里程碑

实现 ret2win demo 自动求解：

1. 自动 triage。
2. 自动 crash。
3. 自动计算 offset。
4. 自动生成 `exploit.py`。
5. 自动获取 flag。
6. 自动生成 `writeup.md`。

## 第三里程碑

扩展 ret2libc、ROP、format string、heap 和 shellcode workflow。

## 长期方向

1. `Vanta Core` 作为安全 Agent 平台底座。
2. `Vanta Pwn` 作为第一个领域工作流。
3. 后续扩展 reverse、crypto、web、forensics。
4. 插件协议、MCP、provider fallback、model profiles 和 benchmark 持续演进。
