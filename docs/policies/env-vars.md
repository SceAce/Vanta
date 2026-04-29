# Environment Variables

## Rules

1. Vanta 使用的环境变量必须列在本文档。
2. API key 可以存储在用户本机 `$HOME/.vanta/`。
3. API key 禁止进入仓库、数据库、日志、报告、state 文件和共享产物。
4. 本地模型启动脚本路径通过配置或 `/model-add` 添加，不固化用户机器路径。

## Variables

| Variable                   | Required | Default                                    | Description                            |
| -------------------------- | -------- | ------------------------------------------ | -------------------------------------- |
| `RUST_LOG`                 | No       | `info`                                     | Rust runtime 日志级别                  |
| `VANTA_HOME`               | No       | `$HOME/.vanta`                             | 用户本机配置目录                       |
| `VANTA_WORKSPACE`          | No       | `.vanta`                                   | 项目内 workspace 目录                  |
| `VANTA_MODE`               | No       | `ctf`                                      | `ctf`、`research` 或 `malware`         |
| `VANTA_IDA_MCP_COMMAND`    | No       | --                                         | IDA MCP stdio server 启动命令          |
| `VANTA_GDB_MCP_COMMAND`    | No       | --                                         | GDB/pwndbg MCP stdio server 启动命令   |
| `VANTA_PWN_WORKER_COMMAND` | No       | `uv run python -m vanta_pwn_worker.server` | Python pwn worker 启动命令             |
| `REPO_ROOT_OVERRIDE`       | No       | --                                         | lint scripts 测试用 repo root override |

## API Key Storage

API key 默认由 `$HOME/.vanta/` 下的用户配置读取。配置文件不得提交到仓库。
未来如支持 keychain，也必须保持同样的仓库隔离规则。

## Provider Config

模型 provider 配置位于 `$HOME/.vanta/providers.json`，由 `vanta model status`
只读检查，由 `vanta model init-local` 写入本地 llama fallback 草案。该文件可
包含 OpenAI-compatible endpoint、模型名、API key 文件路径、本地 llama 命令和
模型路径，但不得写入仓库、项目 `.vanta/` workspace、日志、报告或 state 文件。
