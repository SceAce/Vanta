# 安全模型

## 安全姿态

Vanta 是安全 Agent 平台，第一阶段聚焦 CTF pwn。安全模型的核心是：明确授权
边界、限制高风险工具调用、保护本机密钥、记录可审计证据，并避免 Agent 静默
执行危险动作。

## 信任边界

### API Key 本机边界

API key 只允许存储在用户本机 `$HOME/.vanta/`。API key 禁止进入仓库、数据库、
日志、报告、state 文件和共享产物。

### Target 执行边界

Target binary 的信任级别由 mode 决定：

1. `ctf`：默认可执行，首次提示风险。
2. `research`：默认不可信，执行前强确认。
3. `malware`：默认禁止直接执行，只允许静态分析或隔离执行。

### 工具权限边界

工具按 risk level 分级：

1. `read-only`
2. `write workspace`
3. `execute local`
4. `network`
5. `exploit`
6. `write outside workspace`

权限确认事件必须写入 transcript。

### Workspace 边界

`.vanta/` 是项目内工作区。Agent 默认只能自动写入 workspace。写入 workspace
外部路径需要人类确认。

### Shell 边界

获取 shell 后默认只允许读操作。白名单包括：

```text
ls
cat
pwd
find
id
whoami
```

白名单外命令需要人类确认。

## 安全要求

1. API key 只允许存放在 `$HOME/.vanta/`。
2. API key 不得进入仓库、日志、报告、数据库、state 文件和共享产物。
3. 本机敏感信息写入 transcript、报告或发送模型前必须 scrub。
4. 远程返回默认保留，但发送云模型前可配置 scrub flag/token。
5. 同一 remote target 首次连接需要确认。
6. 同一 payload 首次发送需要确认。
7. 同一 payload 以 payload sha256 和 target 标识判断。
8. 所有 upstream 连接必须使用 TLS，除非用户显式配置本地模型或本地服务。
9. 不支持未授权真实目标。

## 公开资料与代码片段

允许参考公开分析文章中的架构思想、交互模式、模块边界，以及文章中合法发布
的代码片段。禁止复制、移植或改写泄露源码和其他未授权源码进入仓库。

## Contributor 安全要求

所有贡献者和 Agent 必须：

1. 验证不可信输入。
2. 保持最小权限。
3. 不把 API key 写入仓库、日志、报告、数据库、state 文件或共享产物。
4. 给安全修复添加回归测试。
5. 修改信任边界时更新本文档。
6. 高风险变更需要人类审批。
