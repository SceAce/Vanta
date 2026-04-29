# Overview

`vanta-core` 是 Vanta 的 Rust runtime 基础库。当前负责 `.vanta/` workspace
初始化、workspace 状态检查、Case schema 加载校验、canonical pwn case
写入、provider fallback、Python worker JSON-RPC 调用、基础 workflow run
artifact 和 session JSONL 事件写入。

## Public API

- `init_workspace(project_root, mode)`：初始化或加载项目内 `.vanta/`。
- `workspace_status(project_root)`：只读检查 workspace 是否存在。
- `append_session_event(session_file, event_type, message)`：追加 session 事件。
- `load_case(path)`：读取并校验 `case.json` 或 `case.yaml`。
- `write_case_draft(path, case)`：写入最小 case 草案。
- `write_canonical_case(paths, case)`：写入 `.vanta/pwn/case.json`。
- `start_pwn_workflow(project_root, case)`：初始化 pwn workflow 目录和 run artifact。
- `provider_status()`：只读检查 `$HOME/.vanta/providers.json` 是否存在及 provider 形态。
- `write_provider_config(config)`：写入用户本机 provider 配置，不写项目 workspace。
- `infer_with_fallback(config, request)`：OpenAI-compatible 优先，本地 llama 进程兜底；当 OpenAI-compatible 请求失败且未配置本地进程兜底时，返回包含真实 HTTP 失败原因的错误。
- `PwnWorkerClient`：通过 JSON-RPC over stdio 调用 Python pwn worker。
- `solve_case(project_root, case)`：串联 worker、模型和 artifact 的 CLI solve 编排。
- `solve_case_with_reporter(project_root, case, reporter)`：同上，但向调用方报告阶段进度，供 CLI 输出 `[vanta solve] ...`。
- `PwnCase`：Vanta Pwn case schema。
- `RemoteTarget`：remote 元数据，真实连接仍由 runtime 权限系统确认。
- `WorkspacePaths`：集中描述 `.vanta/` 相关路径。
- `Workspace`：workspace metadata。
- `SessionEvent`：transcript JSONL 事件。

## Dependencies

- `serde`
- `serde_json`
- `serde_yaml`
- `reqwest`
- `thiserror`
- `time`
