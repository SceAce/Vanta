# ADR-0006: 模型 Provider 与本机密钥存储

Status: accepted

Date: 2026-04-26

## Context

Vanta 需要支持 DeepSeek、OpenAI、Anthropic、本地 llama，以及 provider
fallback 和 model profiles。用户希望 API key 配置简单，同时项目要求密钥不
进入仓库和共享产物。

## Decision

Vanta 允许 API key 只存储在用户本机 `$HOME/.vanta/`。API key 禁止进入仓库、
数据库、日志、报告、state 文件和共享产物。

provider 配置、model profiles、本地模型启动脚本路径也存放在 `$HOME/.vanta/`。
本地模型路径通过 `/model-add` 配置，不固化用户机器路径。

## Consequences

1. 用户可以使用文件配置 API key。
2. 仓库和协作产物仍保持无密钥。
3. 所有日志、报告和 transcript 写入前必须执行敏感信息 scrub。
