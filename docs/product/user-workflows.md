# 用户工作流

## 启动工作台

用户执行：

```bash
vanta
```

TUI 启动后，用户可以直接输入：

```text
binary 的路径是 ./chall，对它进行分析，先分析伪代码，输出到 output.md，
包括分析内容、可能攻击方式，最后尝试获取 flag。
```

Agent 应自动建立 `.vanta/` workspace，识别 mode，加载 provider profile，
并开始工具编排。

## 基础分析工作流

1. 用户输入 binary 路径。
2. Agent 运行只读 triage 工具。
3. Agent 调用 IDA MCP 获取伪代码和函数信息。
4. IDA MCP 不可用时，Agent 降级到 `objdump`、`readelf`、`strings`、`nm`。
5. Agent 写入 facts 和 evidence refs。
6. Agent 生成 `output.md`。

## 一键求解工作流

用户输入：

```text
/vanta-solve ./chall
```

Agent 执行：

1. triage。
2. 伪代码分析。
3. crash 尝试。
4. cyclic offset。
5. exploit 草稿生成。
6. 本地验证。
7. remote 验证。
8. 获取 flag 后生成 `writeup.md`。

如果未获取 flag，则生成 `report.md`，记录漏洞假设、失败尝试和下一步建议。

## GDB 工作流

1. Agent 启动长驻 GDB session。
2. 用户和 Agent 可以围绕同一个 session 继续分析。
3. Agent 需要时提取 registers、stack、maps、backtrace。
4. session 结束前，关键状态写入 `.vanta/gdb/`。

## 远程连接工作流

1. 同一 remote target 首次连接需要人类确认。
2. 同一 payload 首次发送需要人类确认。
3. remote 输出允许记录，但进入云模型前按策略 scrub 本机敏感信息。
4. 获取 shell 后只能执行白名单读命令；白名单外命令需要人类授权。

## 回放工作流

1. `transcript replay` 视觉回放会话事件。
2. `tool replay` 重新执行工具调用并比较结果。
3. 回放用于复现、教学、writeup 和问题定位。
