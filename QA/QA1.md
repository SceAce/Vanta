• 我读完了 QA.md:1。我会严格按你的回答作为主约束。下面是我认为在补
文档前必须再确认的点，主要是因为里面有几处会直接影响 PRD、ADR、
安全模型和目录结构。

一、合规边界

1. 你在 clean-room 部分说“如果有需要可以复制代码片段”。这里我需
   要明确反对一下：如果来源是泄露源码，不能复制代码片段。
   我建议文档写成：允许参考公开分析文章总结出的架构思想，禁止复
   制、移植、改写泄露源码或非授权代码片段。
   你是否接受这个写法？
   A: 不，我认为，如果有需要那么复制代码是没有问题的，

2. 是否需要在文档里明确写：Vanta 不基于 Claude Code 泄露源码实
   现？
   你回答“不需要”，但开源项目可能会被质疑。我的建议是至少在 ADR
   里写 clean-room 原则，不点名也可以。你是否接受“不点名但声明
   clean-room”？
   A：可以
3. DCO/CLA 你没回答。开源初期是否需要贡献者签署？
   - 不需要，Apache-2.0 + 普通 PR 即可
   - 需要 DCO
   - 后续再考虑
     A：后续再考虑

二、语言与注释

1. 你希望默认文档、注释都用中文。这会影响当前 Trellis 规则。是否
   确认改成：
   - 文档：中文为主
   - 代码注释：中文为主
   - 公共 API 名称、协议字段、schema key、CLI 参数：仍使用英文
   - README 是否中文为主，附英文摘要？
     A：是

2. CLAUDE.md、CODEX.md、AGENTS.md 是否也全部改中文？还是保留关键
   工程术语英文？
   A：是
   三、安全模型的矛盾点

3. 你回答“默认运行必须进入 sandbox”，但 Sandbox 又回答“暂时不
   做”，且“CTF 直接允许运行”。
   我建议文档写成：
   - MVP：不强制 sandbox
   - CTF 模式：允许本地直接执行，但首次提示风险
   - Vulnerability research 模式：默认视为不可信，执行前强确认
   - Future：加入 sandbox runner
     是否接受？
     A：可以

4. Target binary 在 CTF 中默认可信，但 malware-like challenge 又
   支持。这里要不要区分模式？
   - mode = ctf：默认可执行
   - mode = research：默认不可信
   - mode = malware：默认禁止直接执行，只允许静态分析或隔离执行
     A:可以
5. shell 后续交互“只允许读文件”。需要定义允许命令白名单吗？例
   如：
   - ls
   - cat
   - pwd
   - find
   - id
   - whoami
     还是由 Agent 判断“读操作”？
     A：可以白名单，如果需要执行白名单之外的操作就需要向人类鉴权

6. “对于本机的敏感信息 scrub，对于其他人的不需要”这里有风险。远
   程返回也可能包含 token、flag、私密路径。
   是否改成：本机敏感信息强制 scrub；远程内容默认保留，但在发送
   云模型前可配置 scrub flag/token？
   A：可以
   四、API Key 与配置

7. 你希望配置文件在 ~/.vanta/config/toml，但又坚持 API key 不存
   储。
   是否确认配置文件只保存 provider 名称、base URL、model
   profile，不保存 key？例如：
   A：配置文件在 ~/.vanta/config/toml,API KEY 也存放在里面，API key不在项目中存储，并且不推送到远程

[providers.openai]
base_url = "<https://api.openai.com/v1>"
api_key_env = "OPENAI_API_KEY"

1. 外部模型的 API key 只从环境变量读取，是否可以？

- OPENAI_API_KEY
- ANTHROPIC_API_KEY
- DEEPSEEK_API_KEY
  A：不，写在文件里面，这样我更好配置
  1. 本地 llama 你提到 ~/tools/localAi-GEmini/，我会只写成“用户本
     地模型启动脚本可配置”，不固化路径。是否确认？
     A：可以，后续可以通过/model-add这个命令去添加本地模型启动脚本所在的路径

  五、技术架构
  1. 你偏向 Rust 主 CLI，又接受 TS Core + Python Worker，还说主
     runtime Rust、UI TS、worker Python。这里需要最终定案。
     我建议：

- Rust：apps/cli，进程入口、权限、配置、workspace、tool
  supervisor
- TypeScript：TUI 子进程或 package，负责 Claude Code-like 交互
- Python：pwn worker，负责 pwntools/GDB/IDA MCP 等
  这比 “TS Core” 更符合你的 Rust 偏好。是否接受？
  A：可以
  1. 如果 Rust 是主 runtime，TUI 用 TS/Ink 会增加进程通信复杂度。
     是否可以接受第一版用 Rust TUI，例如 ratatui，后续再评估 TS/
     Ink？
     你更看重：

- Claude Code-like UI 表现力
- Rust 单一主栈可维护性
  A: 表现力和性能，
  1. 发布你说 npm 和 cargo install，但又说不发布到 npm/PyPI/
     crates.io。这里是否表示：

- 第一阶段只支持本地安装，不发布公共 registry
- 以后再考虑 npm/crates.io
  A：如果npm必须发送到npm/PyPI/crates.io,那么就不发送，只使用cargo install

  六、Workspace 命名冲突
  1. 你前面 workspace 目录名回答 vantaPwn，后面又回答 vanta-
     workspace。最终用哪个？
     我建议：

- 项目内工作区目录：.vanta/
- 工作区类型名：vanta-workspace
- pwn 子目录：.vanta/pwn/
  这样更像标准工具，也不会污染 challenge 目录。是否接受？
  A：是
  1. 你是否坚持目录必须没有点号，比如 vanta-workspace/？
     我建议用隐藏目录 .vanta/，因为里面有 transcript、payload、
     tool logs。
     A： 使用隐藏目录
     七、MVP 范围

  2. 你希望第一版包含 ret2win、ret2libc、ROP、format string、
     heap、shellcode、IDA MCP、GDB MCP。这个范围对“一天原型”明显过
     大。
     我建议文档拆成：

- MVP-0：TUI + workspace + provider + tool runtime
- MVP-1：ELF triage + IDA MCP/GDB MCP 接入原型 + output.md
- MVP-2：ret2win/offset 自动化
- MVP-3：ret2libc/ROP
- MVP-4：fmt/heap/shellcode
  是否接受这种拆分？
  A：并不大，我有相关的skill，你可以拆分来快速的补全相关的信息，并且我有做好一个原型，它肯定是有可以借鉴的地方，这个项目在$HOME/My_github/AegisCodex
  1. “第一个 milestone 完成证据”你说“知道所有二进制漏洞、知道一些
     CVE”。这个更像长期目标。
     第一个 milestone 是否可以定义为：给定一个 Linux ELF，Vanta 能
     通过 TUI 调用 IDA MCP/GDB/基础工具，生成 output.md，列出伪代
     码分析、攻击面、可疑漏洞点和下一步利用建议？
     A: 可以，

  2. 第一版是否必须“自动获取 flag”，还是 demo 中必须获取 flag？
     这两个文档含义不同：

- 产品 MVP 必须自动拿 flag
- 首个 demo 选一个简单题自动拿 flag
  A：demo去获取一个简单题目的flag，并且对于难题也能够分析出漏洞

  八、IDA MCP / GDB MCP
  1. IDA MCP 第一版是强依赖还是可选？
     我建议可选强增强：没有 IDA MCP 时降级到 objdump/readelf/
     Ghidra 后续。
     A：强依赖，没有的时候自动降级为 objdump/readelf

  2. GDB MCP 你提到必须接入。这里是已有某个 GDB MCP 项目，还是我
     们自己实现一个 GDB worker/MCP server？
     A: 自己实现，但是我本机已经安装好了ida的mcp，参考$HOME/My_github/AegisCodex/

  3. IDA MCP 的运行方式是什么？

- 用户本地打开 IDA 后连接
- Vanta 启动 IDA headless
- 只调用已有 MCP server
  A: Vanta自动启动，
  1. 如果 IDA 没装，是否允许继续用基础工具分析？你前面说“提醒安
     装，不装则降级”，我会按这个写。
     A：允许
     九、工具权限

  2. “工具调用权限等级智能分配”需要落成规则。是否接受默认策略：

- read-only：自动允许
- write workspace：自动允许
- execute local：CTF 模式首次确认，之后同 binary 可继续
- network：同靶机首次确认
- exploit：同 payload 首次确认
- write outside workspace：每次确认
  A：是
  1. “同一个 payload 第一次需要确认”里的“同一个”用什么判断？
     我建议用 payload sha256 + target 标识。
     A：可以
     十、测试与 fixture

  2. 你说 vulnerable ELF fixture 可以放 repo，但是不推送。那开源
     仓库怎么跑测试？
     我建议：推送 C 源码和 Makefile，不推送编译好的 ELF；CI/本地测
     试时编译。是否接受？
     A：可以，但是需要放在一个测试的专用文件夹里面

  3. 真实模型调用测试你说会用 DeepSeek 和本地模型。是否把真实模型
     测试定义为手动测试，不放进默认 CI？
     默认 CI 用 mock provider，避免 API key 和费用问题。
     A：是
     十一、Provider 与隐私

  4. 你对“是否允许 binary metadata 发给云模型”回答“以后考虑，暂时
     不考虑”。那 MVP 默认是否禁止上传 binary metadata 到云模型？
     如果禁止，云模型只能看到人工允许的摘要；本地模型可以看完整分
     析结果。
  5. 是否需要在 TUI 中显示“当前会发送给模型的内容摘要”，尤其是云
     模型？
     A：这些暂不考虑
     十二、平台定位

  6. 你说 Vanta 是安全 Agent 平台，但先做 pwn。文档中是否写：

- Vanta Core：安全 Agent 平台底座
- Vanta Pwn：第一个领域工作流
- reverse/crypto/web/forensics 后续扩展
  A：是
  1. CLI 仍叫 vanta，那一键攻击命令叫什么？我建议：

- /solve
- /hunt
- /autopwn

  A: /vanta-solve
  你偏向哪个？
