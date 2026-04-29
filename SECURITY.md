# SECURITY.md

## 安全姿态

Vanta 是安全 Agent 平台。第一阶段聚焦 CTF pwn，但仍然必须保持清晰的授权、
密钥和工具执行边界。

## 支持版本

在项目发布稳定版本前，安全支持适用于当前活跃开发分支。

## 漏洞报告

不要在公开 issue 中提交 exploit 细节。

请通过 GitHub Security Advisory 私下报告：

- `https://github.com/Cubeyond/Vanta/security/advisories/new`

报告请包含：

1. 受影响版本或 commit。
2. 影响范围。
3. 复现步骤。
4. 安全的 proof of concept。
5. 建议修复方案。

## API Key

1. API key 只允许存储在用户本机 `$HOME/.vanta/`。
2. API key 禁止进入仓库、数据库、日志、报告、state 文件和共享产物。
3. 修改 API key handling 需要人类审批。

## 敏感区域

以下区域属于高风险修改：

1. API key 存储、读取和 scrub。
2. provider 调用。
3. tool permission engine。
4. GDB worker。
5. IDA MCP 自动启动。
6. exploit 执行。
7. remote target 连接。
8. shell 命令白名单。
9. workspace 导出、压缩和隐私数据删除。
