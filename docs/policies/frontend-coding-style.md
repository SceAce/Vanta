# TUI / Frontend Coding Style

## Scope

适用于 Vanta 的 TypeScript TUI、未来 frontend，以及与终端交互相关的组件。

## 技术约束

1. TypeScript strict mode。
2. 禁止 `any`，优先使用 `unknown` 后收窄。
3. 禁止 `@ts-ignore`。
4. TUI 状态必须来自 runtime 事件，不得自行维护业务真相。
5. 工具日志默认折叠。
6. 权限确认必须展示 risk level、target、payload hash 和动作摘要。

## 组件命名

| 类型       | 规则                        |
| ---------- | --------------------------- |
| Components | `PascalCase`                |
| Hooks      | `camelCase` 且以 `use` 开头 |
| Utilities  | `camelCase`                 |
| Constants  | `SCREAMING_SNAKE_CASE`      |

## TUI 测试

1. 关键组件需要行为测试。
2. 不使用快照测试作为唯一验证。
3. 权限弹层、slash command 补全、折叠工具日志必须有测试或手动验证证据。

## 设计系统

实现 UI 前必须阅读 `DESIGN.md`。
