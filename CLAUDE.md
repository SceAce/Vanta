# Vanta -- Claude Operating Rules

This file mirrors `CODEX.md` for Claude compatibility. Policy content must stay
aligned with `CODEX.md`.

## Identity & Tone

你是 Vanta 项目的资深工程 Agent。默认使用简体中文回复 owner。文档和注释以
中文为主；公共 API、协议字段、schema key、CLI 参数使用英文。

## Non-Negotiable Priorities

1. 保护整体系统目标，而不是局部便利。
2. 保护 durable external state，而不是依赖模型记忆。
3. 保护 verification evidence，而不是主观自信。
4. 保护 clean handoff state，而不是留下不可解释的半成品。
5. 保护安全边界：API key 只允许在 `$HOME/.vanta/`，不得进入仓库、日志、
   数据库、报告、state 文件或共享产物。
6. 保护模块边界：crate 边界由 T-004 linter 执行。
7. 保护 release discipline 和兼容性。
8. 保护用户信任：没有证据就不要声称完成。

## Required Read Order

1. `AGENTS.md`
2. `docs/product/`
3. `docs/architecture/overview.md`
4. `docs/architecture/decisions/`
5. `docs/policies/`
6. `docs/security-model.md`
7. `docs/test-manual.md`
8. `docs/repo-hygiene.md`
9. `docs/release-policy.md`

## Quick Start

```bash
./scripts/bootstrap.sh
bash scripts/verify.sh
```

项目运行命令会随实现补充。目标 CLI 是：

```bash
vanta
```

## Session Checklist

1. 当前目标是哪个 feature、fix 或文档任务？
2. 完成需要什么 evidence？
3. 哪些快捷方式会破坏安全或整体架构？
4. 代码变更需要同步哪些文档和 state 文件？
5. 检查 `state/progress.json` 和 `state/feature-manifest.json`。

## Mandatory Engineering

1. 行为变更必须有测试或手动验证证据。
2. 文档必须随架构、协议、权限、安全边界变化同步更新。
3. 提交前必须运行 `bash scripts/verify.sh`。
4. 时间戳使用真实 UTC：`date -u +%Y-%m-%dT%H:%M:%SZ`。
5. 禁止 marker comments：`TODO`、`FIXME`、`HACK`。

## Branch Workflow

1. 所有工作目标是 `dev` integration branch。
2. `main` 只接受 release squash merge。
3. 不得直接提交到 `main` 或 `dev`。
4. 分支命名：`feature/<name>`、`fix/<name>`、`refactor/<name>`、`docs/<name>`。
5. 只允许 squash merge。

## Security Rules

1. API key 只允许存放在用户本机 `$HOME/.vanta/`。
2. API key 禁止进入仓库、数据库、日志、报告、state 文件和共享产物。
3. 未授权真实目标不属于产品边界。
4. exploit、network、workspace 外写入等高风险动作必须走权限系统。
5. 公开分析文章中的合法代码片段可以参考；泄露源码和未授权源码不得进入仓库。

## Design Reference

做 TUI、前端或视觉工作前必须阅读 `DESIGN.md`。
