# Overview

`vanta-cli` 提供 `vanta` 命令入口。当前实现最小骨架命令：

- `vanta init`
- `vanta status`
- `vanta case init`
- `vanta case validate`
- `vanta model status`
- `vanta model init-local`
- `vanta solve`
- `vanta help`

## Public API

这是应用入口 crate，不提供稳定库 API。命令行为：

- `vanta init [path] [--mode ctf|research|malware]`：初始化 `.vanta/` workspace。
- `vanta status [path]`：查看 workspace 是否存在。
- `vanta case init <binary> [--output case.json]`：生成最小 `case.json` 草案。
- `vanta case validate <case.json|case.yaml>`：加载、默认值填充并输出规范化摘要，不启动工具。
- `vanta model status`：只读展示 `$HOME/.vanta/providers.json` 的 provider 配置状态。
- `vanta model init-local <model.gguf> --command <llama-program>`：写入本机 llama 进程 fallback 草案。
- `vanta solve <case.json|case.yaml>`：校验 case，初始化 workspace，调用 Python worker 和模型 provider，并写入分析 artifact；运行时会向 stderr 输出 `[vanta solve] ...` 阶段进度，避免长时间模型请求看起来像卡住。

## Dependencies

- `anyhow`
- `serde_json`
- `vanta-core`
