# DESIGN.md -- Vanta

> 任何 UI、TUI、前端或视觉工作前必须阅读本文档。

## 设计目标

Vanta 的界面是面向 pwn 选手的终端工作台，不是普通聊天框。界面要高密度、
清晰、快速、可折叠，优先服务程序分析、调试和 exploit 工作流。

## 体验原则

1. 对话始终可输入。
2. 工具调用默认折叠。
3. 状态信息持续可见。
4. 高风险动作必须清楚确认。
5. 所有输出都能追溯 evidence。
6. 不用装饰性视觉元素干扰分析。

## TUI 布局

默认布局为三块：

```text
+----------------------+---------------------------+
| 文件 / 状态 / facts  | 对话流 / 工具日志         |
|                      |                           |
| checksec             | Agent plan summary        |
| arch                 | collapsed tool run        |
| libc                 | report excerpt           |
| offset               |                           |
| gadgets              |                           |
+----------------------+---------------------------+
| PromptInput                                      |
+--------------------------------------------------+
```

窄屏可以退化为双栏或单栏。

## 面板

### 状态面板

持续展示：

1. binary。
2. arch。
3. checksec。
4. libc。
5. remote target。
6. exploit 状态。
7. crash offset。
8. gadget 摘要。

### 对话面板

显示用户输入、Agent 计划摘要、工具结果摘要和报告片段。真实 hidden reasoning
不展示，允许展示 plan/summary。

### 工具面板

工具调用默认折叠，展开后显示：

1. tool name。
2. risk level。
3. input summary。
4. output summary。
5. evidence ref。
6. duration。

### 权限弹层

高风险动作必须显示：

1. risk level。
2. target。
3. payload hash。
4. 将要执行的动作。
5. 是否写入 workspace 外。

## 颜色语义

| 角色   | 用途                    |
| ------ | ----------------------- |
| green  | 成功、已验证、flag 获取 |
| yellow | 警告、需要确认、降级    |
| red    | 失败、高风险、权限拒绝  |
| blue   | 信息、链接、焦点        |
| cyan   | 当前选中、活动 session  |
| gray   | 折叠日志、低优先级信息  |

## Slash Commands

必须支持：

```text
/triage
/crash
/offset
/gdb
/exploit
/report
/compact
/vanta-solve
/model-add
```

输入 `/` 时应提供命令补全。

## 文案规则

1. UI 文案中文为主。
2. 命令、协议字段、文件名和 schema key 使用英文。
3. 错误消息必须包含可执行修复建议。
4. 不用营销式文案。
