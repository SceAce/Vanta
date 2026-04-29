# Environment Variables

## Rules

1. Vanta 使用的环境变量必须列在本文档。
2. API key 可以存储在用户本机 `$HOME/.vanta/`。
3. API key 禁止进入仓库、数据库、日志、报告、state 文件和共享产物。
4. 本地模型启动脚本路径通过配置或 `/model-add` 添加，不固化用户机器路径。

## Variables

| Variable             | Required | Default        | Description                            |
| -------------------- | -------- | -------------- | -------------------------------------- |
| `RUST_LOG`           | No       | `info`         | Rust runtime 日志级别                  |
| `VANTA_HOME`         | No       | `$HOME/.vanta` | 用户本机配置目录                       |
| `VANTA_WORKSPACE`    | No       | `.vanta`       | 项目内 workspace 目录                  |
| `VANTA_MODE`         | No       | `ctf`          | `ctf`、`research` 或 `malware`         |
| `REPO_ROOT_OVERRIDE` | No       | --             | lint scripts 测试用 repo root override |

## API Key Storage

API key 默认由 `$HOME/.vanta/` 下的用户配置读取。配置文件不得提交到仓库。
未来如支持 keychain，也必须保持同样的仓库隔离规则。
