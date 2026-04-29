# Vanta

Vanta 是一个面向安全研究的 Agent 平台。第一阶段聚焦 `Vanta Pwn`：一个用于
CTF pwn 和二进制漏洞研究辅助的终端工作台。

用户启动 `vanta` 后进入 TUI，通过自然语言和 slash commands 驱动 Agent 调用
IDA MCP、GDB、pwntools、objdump、readelf 等工具完成程序分析、漏洞定位、
利用尝试和报告生成。

## 当前目标

1. 构建 Rust 主 runtime、TypeScript TUI、Python pwn worker 的三层架构。
2. 实现 `.vanta/` workspace、transcript、tool replay 和 evidence refs。
3. 接入 IDA MCP、GDB worker/MCP 和基础 ELF triage 工具。
4. 生成 `output.md`、`exploit.py`、`writeup.md` 或 `report.md`。
5. 在简单 CTF pwn demo 中自动获取 flag。

## 核心命令愿景

```bash
vanta
```

进入 TUI 后可以输入：

```text
binary 的路径是 ./chall，对它进行分析，先分析伪代码，输出到 output.md，
包括分析内容、可能攻击方式，最后尝试获取 flag。
```

常用 slash commands：

```text
/triage
/crash
/offset
/gdb
/exploit
/report
/compact
/vanta-solve
/model-add
```

## 架构

```text
TypeScript TUI
  |
Rust Runtime
  |
Python Pwn Worker
  |
IDA MCP / GDB / pwntools / ELF tools
```

Rust runtime 是权限、配置、workspace、provider、tool supervisor 和 evidence
的控制层。TypeScript TUI 负责 Claude Code-like 交互表现。Python worker 负责
pwn 生态工具接入。

## 安全边界

1. 第一阶段只面向 CTF pwn。
2. 未经授权的真实目标不在产品边界内。
3. API key 只允许存储在用户本机 `$HOME/.vanta/`。
4. API key 禁止进入仓库、数据库、日志、报告、state 文件和共享产物。
5. 高风险工具调用需要权限确认。
6. 公开分析文章中的合法代码片段可以作为参考；泄露源码和未授权源码不能进入仓库。

## 文档

| 文档                                   | 说明             |
| -------------------------------------- | ---------------- |
| `docs/product/prd.md`                  | 产品需求         |
| `docs/product/mvp.md`                  | MVP 范围         |
| `docs/product/user-workflows.md`       | 用户工作流       |
| `docs/product/safety-and-non-goals.md` | 安全边界与非目标 |
| `docs/architecture/overview.md`        | 架构总览         |
| `docs/architecture/decisions/`         | ADR              |
| `docs/security-model.md`               | 安全模型         |
| `docs/test-manual.md`                  | 测试手册         |
| `DESIGN.md`                            | TUI 设计系统     |

## 验证

```bash
bash scripts/verify.sh
```

提交前必须通过验证。当前仓库仍沿用 Trellis 的工程治理框架，包括 signed
commits、状态文件、文档同步和 taste checks。

## License

Apache-2.0
