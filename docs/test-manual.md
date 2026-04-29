# 测试手册

## 目的

本文档定义 Vanta 的验证路径、测试类别和验收证据。默认目标是让 Agent 的程序
分析、工具调用、权限系统、workspace 和报告生成保持可复现。

## 默认验证命令

```bash
bash scripts/verify.sh
```

该命令必须在提交前通过。当前仓库使用 Trellis 验证框架，覆盖 Rust、Python、
Node、Markdown、JSON/YAML、ADR、状态文件和自定义 taste checks。

## 测试类别

### 单元测试

覆盖：

1. Rust runtime 配置解析。
2. 权限策略。
3. workspace schema。
4. provider profiles。
5. tool input/output schema。

### 集成测试

覆盖：

1. Rust runtime 与 Python worker 的 JSON-RPC 通信。
2. TUI 与 runtime 事件流。
3. tool supervisor 的超时、取消和并发。
4. evidence ref 写入。

### Fixture Binary 测试

测试专用目录保存 C 源码和 Makefile，不提交编译后的 ELF。测试时编译小型
vulnerable ELF fixture。

第一批 fixture：

1. ret2win。
2. stack overflow offset。
3. ret2libc smoke。

### GDB Smoke 测试

本地测试必须覆盖 GDB worker 基础能力：

1. 启动长驻 session。
2. 运行到 crash。
3. 提取寄存器和栈摘要。
4. 计算 cyclic offset。

默认 CI 暂不强制跑 GDB。

当前 worker contract 测试覆盖 `gdb.status`、`gdb.start`、`gdb.command`、
`gdb.snapshot` 和 `gdb.stop` 的 JSON-RPC 形状。真实 GDB smoke 可在装有
GDB/pwndbg 的机器上通过 worker stdio 调用手动执行。

### Case Workflow Smoke

Pwn case workflow 的最小本地验证不启动真实 exploit 或 remote 连接：

```bash
root=/tmp/vanta-case-smoke
rm -rf "$root"
mkdir -p "$root"
printf elf > "$root/chall"
cargo run -q -p vanta-cli -- case init "$root/chall" --output "$root/case.json"
cargo run -q -p vanta-cli -- case validate "$root/case.json"
cargo run -q -p vanta-cli -- solve "$root/case.json"
test -f "$root/.vanta/pwn/case.json"
test -f "$root/.vanta/pwn/knowledge/patterns.json"
find "$root/.vanta/pwn/runs" -maxdepth 2 -type f | sort
```

该 smoke 应生成 `run.json`、`static-scan.json`、`breakpoint-plan.json`、
`dynamic-verify.json`、`poc-draft.json` 和 `capability-check.json`。

### Model Provider Smoke

本地模型 fallback smoke 使用临时 `VANTA_HOME`，不写仓库或项目 state：

```bash
root=/tmp/vanta-solve-smoke
home=/tmp/vanta-home-smoke
rm -rf "$root" "$home"
mkdir -p "$root" "$home"
printf elf > "$root/chall"
cat > "$home/providers.json" <<JSON
{
  "schema_version": "vanta.providers.v1",
  "default_profile": "local",
  "openai_compatible": {
    "base_url": "http://127.0.0.1:9",
    "model": "unavailable",
    "timeout_seconds": 1
  },
  "local_llama_process": {
    "command": ["sh", "-c", "printf 'Static analysis complete; no gdb needed.' > {output_file}"],
    "model_path": "$root/model.gguf",
    "timeout_seconds": 10
  }
}
JSON
cargo run -q -p vanta-cli -- case init "$root/chall" --output "$root/case.json"
VANTA_HOME="$home" cargo run -q -p vanta-cli -- solve "$root/case.json"
find "$root/.vanta/pwn/runs" -maxdepth 2 -type f | sort
```

预期 `solve` 输出 `provider: local_llama_process` 和 `fallback_used: true`，
并生成 `analysis.json`。

如果使用 pwno-mcp，先配置 `VANTA_GDB_MCP_COMMAND`。官方推荐的 Docker
运行方式需要 `SYS_PTRACE`、`SYS_ADMIN`、禁用默认 seccomp/apparmor 限制，并把
当前题目目录 mount 到容器内 `/workspace`。配置后 `gdb.start` 的
`binary_path` 使用容器内路径，例如 `/workspace/chall`。

### IDA MCP 手动测试

IDA MCP 作为强增强能力，默认 CI 不要求安装 IDA。手动测试需要覆盖：

1. 自动启动 IDA MCP。
2. 获取函数列表。
3. 获取伪代码摘要。
4. 缺失 IDA 时降级。

手动配置入口为 `VANTA_IDA_MCP_COMMAND`，该命令必须启动一个 newline
JSON-RPC MCP stdio server。worker 当前会调用 `tools/list` 并优先选择
`decompile_function`、`get_pseudocode`、`decompile` 或
`ida_decompile_function` 作为伪代码工具。

### 模型测试

默认 CI 使用 mock provider。真实模型测试为手动测试，优先使用 DeepSeek 和
本地 llama。

### Benchmark

benchmark 用于记录速度、稳定性和成功率。第一批 benchmark：

1. `triage-small-elf`
2. `offset-ret2win`
3. `exploit-ret2win`

## 验收标准

1. `bash scripts/verify.sh` 通过。
2. 关键行为有测试或手动证据。
3. 行为变更更新 `state/progress.json`。
4. 完成状态需要 evidence ref。
5. 生成报告能追溯到 tool run 和 evidence。
