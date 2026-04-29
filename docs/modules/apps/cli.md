# Overview

`vanta-cli` 提供 `vanta` 命令入口。当前实现最小骨架命令：

- `vanta init`
- `vanta status`
- `vanta help`

## Public API

这是应用入口 crate，不提供稳定库 API。命令行为：

- `vanta init [path] [--mode ctf|research|malware]`：初始化 `.vanta/` workspace。
- `vanta status [path]`：查看 workspace 是否存在。

## Dependencies

- `anyhow`
- `vanta-core`
