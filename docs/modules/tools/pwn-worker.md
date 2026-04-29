# Pwn Worker

`pwn-worker` 是 Vanta Pwn 的 Python 工具桥接层，通过 JSON-RPC over stdio
暴露二进制分析能力给 Rust runtime。

## Public API

- `worker.capabilities`：返回 worker 方法、risk level 和已支持分析能力。
- `ida.status`：检查 `VANTA_IDA_MCP_COMMAND` 指向的 IDA MCP stdio server。
- `ida.decompile_function`：通过 IDA MCP 获取单个函数伪代码。
- `ida.analyze_pseudocode`：批量获取关键函数伪代码摘要。
- `gdb.status`：检查本机 `gdb` 可用性和长驻 session 数量。
- `gdb.mcp_status`：`gdb.status` 的别名，用于检查 pwno-mcp 或本机 GDB 后端。
- `gdb.start`：启动长驻 GDB session，可沿用用户 pwndbg 初始化。
- `gdb.command`：在指定 GDB session 中执行调试命令。
- `gdb.snapshot`：提取 registers、stack、maps 和 backtrace 摘要。
- `gdb.stop`：结束指定 GDB session。
- `pwn.static_scan`：高层静态扫描合同；IDA 可用时采集关键函数伪代码，IDA 不可用时返回 `degraded` 并给出降级证据。
- `pwn.breakpoint_plan`：生成断点计划，不启动 GDB。
- `pwn.dynamic_verify`：检查动态验证就绪状态；GDB 不可用时返回 `tool_unavailable` failure。
- `pwn.poc_draft`：生成 PoC 草案 artifact 形状，不执行 exploit。
- `pwn.pattern_match`：基于当前发现给出 ret2win、ret2libc、fmtstr、tcache_poisoning 候选建议。

## Risk Levels

- IDA MCP 方法为 `read-only`。
- `gdb.start` 与 `gdb.command` 为 `execute local`，必须由 Rust runtime 权限系统确认。
- `gdb.snapshot` 和 `gdb.stop` 不启动新目标，标记为 `read-only`。
- `pwn.static_scan`、`pwn.breakpoint_plan`、`pwn.pattern_match` 为 `read-only`。
- `pwn.dynamic_verify` 为 `execute local`，实际执行前仍需 Rust runtime 权限确认。
- `pwn.poc_draft` 为 `write workspace`，只产生草案 artifact，不发送 payload。

## Dependencies

- Python 3.13+
- 本机可选 `gdb`
- 本机可选 IDA MCP stdio server，通过 `VANTA_IDA_MCP_COMMAND` 配置
- 本机可选 pwno-mcp stdio server，通过 `VANTA_GDB_MCP_COMMAND` 配置

## pwno-mcp

GDB 后端优先使用 `VANTA_GDB_MCP_COMMAND`。未配置时，worker 降级到内置本机
GDB CLI session。

本机 Python 方式：

```bash
export VANTA_GDB_MCP_COMMAND="python -m pwnomcp"
```

Docker 方式：

```bash
export VANTA_GDB_MCP_COMMAND='docker run --rm -i --cap-add=SYS_PTRACE --cap-add=SYS_ADMIN --security-opt seccomp=unconfined --security-opt apparmor=unconfined -v /path/to/workspace:/workspace pwno-mcp:latest'
```

`pwno-mcp` 的 Docker workspace mount 会改变容器内 binary 路径。传给
`gdb.start` 的 `binary_path` 应使用容器内路径，例如 `/workspace/chall`。

## Verification

- `uv run pytest tools/pwn-worker/tests`
- `uv run mypy tools scripts`
- `uv run ruff check tools scripts`
