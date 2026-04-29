# MVP 范围

## MVP 目标

MVP 的目标不是做一个通用黑盒攻击系统，而是做出一个可运行、可审计、可扩展
的 Vanta Pwn 工作流原型：用户启动 `vanta`，通过 TUI 输入 binary 路径，
Agent 调用程序分析和调试工具，生成 `output.md`，并在简单 CTF pwn fixture
上自动获取 flag。

## MVP-0：平台底座

1. Rust 主 runtime：配置、权限、workspace、tool supervisor。
2. TypeScript TUI：Claude Code-like 多面板交互。
3. Python pwn worker：pwntools、GDB、IDA MCP 桥接。
4. JSON-RPC over stdio 作为跨语言通信协议。
5. `.vanta/` workspace 初始化。
6. transcript 和 tool run 事件记录。

## MVP-1：程序分析闭环

1. 基础 ELF triage：`file`、`checksec`、`readelf`、`objdump`、`strings`、`nm`。
2. IDA MCP 自动启动和伪代码分析。
3. 无 IDA MCP 时自动降级。
4. 生成 `output.md`。
5. 输出攻击面、危险函数、可疑输入路径和下一步利用建议。

## MVP-2：动态调试闭环

1. 自研 GDB MCP 或 GDB worker。
2. 长驻 GDB session。
3. pwndbg 集成。
4. cyclic offset 自动计算。
5. core dump 分析。
6. crash evidence 写入 `.vanta/`。

## MVP-3：简单自动利用

1. ret2win 自动识别与 exploit 草稿。
2. ret2libc 和基础 ROP chain 生成。
3. 同 payload 首次执行确认。
4. demo fixture 自动获取 flag。

## MVP-4：扩展题型

1. format string。
2. heap 基础分析。
3. shellcode。
4. qemu-user + gdbserver。
5. 更复杂的 remote exploit workflow。

## MVP 外延

MVP 不要求覆盖所有真实漏洞挖掘场景。复杂题目中，MVP 的最低目标是分析出
可信漏洞假设、证据引用和下一步利用路线。
