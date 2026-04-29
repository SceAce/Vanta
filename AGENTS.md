# AGENTS.md

Vanta 是一个面向安全研究的 Agent 平台。第一阶段聚焦 `Vanta Pwn`：用于 CTF
pwn 和二进制漏洞研究辅助的终端工作台。

## Repository

- **Project:** Vanta
- **Repository:** <https://github.com/Cubeyond/Vanta>
- **License:** Apache-2.0
- **Language:** 中文为主；公共 API、协议字段、schema key、CLI 参数使用英文
- **Default response language:** Simplified Chinese

## Tech stack

- **Runtime:** Rust 1.92.0
- **TUI:** TypeScript + pnpm，优先追求表现力和性能
- **Worker:** Python >= 3.13，uv，pwntools/GDB/IDA MCP 工具桥接
- **Database:** MVP 暂不需要 SQLite 或 PostgreSQL
- **Node tooling:** pnpm >= 10.32.1

## Key rules

1. 提交前必须运行 `bash scripts/verify.sh` 并通过。
2. 使用 Conventional Commits 和签名提交：`git commit -S`。
3. Rust 禁止 `unsafe`；clippy 禁止 `unwrap`、`expect`、`panic`。
4. API key 只允许存储在用户本机 `$HOME/.vanta/`，禁止进入仓库、数据库、
   日志、报告、state 文件和共享产物。
5. 行为变更必须有测试或手动验证证据。
6. 只能 squash merge，不允许 merge commit。
7. 禁止直接提交到 `main` 或 `dev`，必须走 PR。
8. 未授权真实目标不属于产品边界。

## Read order

开始工作前按顺序阅读：

1. `CLAUDE.md`
2. `CODEX.md`
3. `AGENTS.md`
4. `docs/product/`
5. `docs/architecture/overview.md`
6. `docs/architecture/decisions/`
7. `docs/backlog.md`
8. `DESIGN.md`
9. `docs/security-model.md`
10. `docs/test-manual.md`
11. `docs/repo-hygiene.md`
12. `docs/release-policy.md`
13. 相关 `docs/policies/*.md`

## Completion discipline

进度必须记录在机器可读状态文件中：

- `state/feature-manifest.json`
- `state/progress.json`
- `state/completion-ledger.json`
- `state/test-report.json`
- `state/quality-scores.json`
- `state/benchmark-baseline.json`
- `state/debt-ledger.json`

feature 状态流转：

```text
planned -> in_progress -> candidate_complete -> verified_complete
```

`candidate_complete` 或 `verified_complete` 必须带 evidence ref。

## Security discipline

1. API key 只允许保存在 `$HOME/.vanta/`。
2. API key 不得进入仓库、日志、报告、数据库、state 文件或共享产物。
3. 不得削弱认证、授权、权限确认或工具风险分级。
4. 不得把未授权真实目标当作授权攻击目标。
5. 修改 API key、TLS、权限模型、shell 白名单和 exploit 执行边界需要人类审批。

## Coding style

| Language         | Policy document                          |
| ---------------- | ---------------------------------------- |
| Rust             | `docs/policies/rust-coding-style.md`     |
| Python           | `docs/policies/python-coding-style.md`   |
| TypeScript/TUI   | `docs/policies/frontend-coding-style.md` |
| Environment vars | `docs/policies/env-vars.md`              |
| Testing          | `docs/policies/test-gate.md`             |

不要在本文件内重复完整编码规范，使用策略文档和 linters 执行。
