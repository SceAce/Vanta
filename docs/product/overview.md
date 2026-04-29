# 产品概览

## Vanta 是什么

Vanta 是一个面向安全研究的 Agent 平台。第一阶段聚焦 `Vanta Pwn`：
一个用于 CTF pwn 和二进制漏洞研究辅助的终端工作台。用户启动 `vanta`
后进入 TUI，通过自然语言和 slash commands 驱动 Agent 调用 IDA MCP、
GDB、pwntools、objdump、readelf 等工具完成程序分析、漏洞定位、利用尝试
和报告生成。

## 核心定位

1. 帮助中高级 pwn 选手、战队、安全研究员和教学场景高效完成 CTF pwn
   分析与利用。
2. 以自动求解为目标，优先追求成功率，其次是速度、可解释性和学习价值。
3. 以 `Vanta Core` 提供安全 Agent 平台底座，以 `Vanta Pwn` 作为第一个
   领域工作流。
4. 通过结构化 evidence store、transcript replay 和 tool replay 保证过程
   可审计、可复现。

## 第一阶段范围

1. 第一阶段只面向 CTF pwn。
2. 默认目标是 Linux ELF，覆盖本地和远程 Linux 服务。
3. 支持 x86_64、i386、arm、aarch64、mips 等常见 CTF 架构。
4. 强化 IDA MCP 和 GDB MCP 集成；缺少 IDA 时降级到 `objdump`、`readelf`
   等基础工具。
5. demo 必须能在简单题目上自动获取 flag；复杂题目至少能给出伪代码分析、
   攻击面、可疑漏洞点和下一步利用建议。

## 非目标

1. MVP 不做 Web dashboard。
2. MVP 不强制 sandbox；sandbox runner 是后续能力。
3. MVP 不要求团队协作工作区。
4. MVP 不发布到 npm、PyPI 或 crates.io；先支持本地 `cargo install` 路线。
5. 未经授权的真实目标不在产品边界内。

## 安全约束

1. API key 只允许存储在用户本机 `$HOME/.vanta/`，禁止进入仓库、数据库、
   日志、报告、state 文件和共享产物。
2. CTF 模式允许直接运行本地 target，但首次执行需要提示风险。
3. research 模式默认 target 不可信，执行前需要强确认。
4. malware 模式默认禁止直接执行，只允许静态分析或隔离执行。
5. 获取 shell 后默认只允许白名单读操作；白名单外命令需要人类授权。

## 公开资料使用边界

允许参考公开分析文章中的架构思想、交互模式、模块边界，以及文章中合法发布
的代码片段。禁止复制、移植或改写泄露源码和其他未授权源码进入仓库。
