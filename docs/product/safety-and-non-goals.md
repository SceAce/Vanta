# 安全边界与非目标

## 授权边界

Vanta 第一阶段只面向 CTF pwn。未授权真实目标不属于产品边界。除非人类明确
授权，Agent 不应把目标视为授权攻击对象。

## 模式

### ctf

1. 默认 target 可执行。
2. 本地执行首次提示风险。
3. 同一 remote target 首次连接需要确认。
4. 同一 payload 首次发送需要确认。

### research

1. target 默认不可信。
2. 执行前需要强确认。
3. 网络、exploit、workspace 外写入均需要显式授权。

### malware

1. 默认禁止直接执行。
2. 只允许静态分析或隔离执行。
3. MVP 不提供强制 sandbox，因此 malware 模式默认只能做静态分析。

## API Key

1. API key 允许存储在用户本机 `$HOME/.vanta/`。
2. API key 禁止进入仓库、数据库、日志、报告、state 文件和共享产物。
3. API key handling 变化需要人类审批。

## Shell 白名单

获取 shell 后默认只允许读操作。初始白名单包括：

```text
ls
cat
pwd
find
id
whoami
```

白名单外命令需要人类授权。

## 非目标

1. 不支持未授权真实目标。
2. MVP 不做 Web dashboard。
3. MVP 不强制 sandbox。
4. MVP 不提供团队共享 workspace。
5. MVP 不承诺覆盖所有 pwn 题型。
