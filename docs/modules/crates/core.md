# Overview

`vanta-core` 是 Vanta 的 Rust runtime 基础库。当前负责 `.vanta/` workspace
初始化、workspace 状态检查、基础 schema version 和 session JSONL 事件写入。

## Public API

- `init_workspace(project_root, mode)`：初始化或加载项目内 `.vanta/`。
- `workspace_status(project_root)`：只读检查 workspace 是否存在。
- `append_session_event(session_file, event_type, message)`：追加 session 事件。
- `WorkspacePaths`：集中描述 `.vanta/` 相关路径。
- `Workspace`：workspace metadata。
- `SessionEvent`：transcript JSONL 事件。

## Dependencies

- `serde`
- `serde_json`
- `thiserror`
- `time`
