# ADR-0007: MVP Sandbox 策略

Status: accepted

Date: 2026-04-26

## Context

二进制 target 可能不可信，malware-like challenge 风险更高。理想状态下所有
target 执行都应进入 sandbox，但 MVP 需要优先完成 pwn workflow 原型。

## Decision

MVP 不强制 sandbox。

运行模式定义如下：

1. `ctf`：默认可执行，首次提示风险。
2. `research`：默认不可信，执行前强确认。
3. `malware`：默认禁止直接执行，只允许静态分析或隔离执行。

sandbox runner 作为后续能力，候选方案包括 Docker、nsjail、firejail、
bubblewrap 和 qemu-user。

## Consequences

1. MVP 可以快速形成闭环。
2. 用户需要明确理解无 sandbox 执行风险。
3. 安全模型必须在 TUI 权限确认中清楚表达当前 mode 和风险。
