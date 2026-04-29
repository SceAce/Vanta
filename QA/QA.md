1. 项目身份

1. 项目正式名称是什么？例如 Vanta、PwnAgent、VantaPwn、Vanta CLI。

A：Vanta

1. GitHub 仓库最终会叫什么？是否继续用 /Vanta？

A：Vanta

1. 这个项目是开源、私有、还是先私有后开源？

A： 开源 4. License 想用什么？MIT、Apache-2.0、AGPL、商业闭源？
A: Apache-2.0

1. 项目一句话定位是什么？
   A: 我希望它能够高效的挖掘二进制漏洞，并且可以非常轻易的解决CTF PWN REVERSE

2. 你希望它被理解成：- CTF pwn 自动化工具 - 二进制漏洞研究助手 - Claude Code-like 安全研究 Agent - 通用安全 Agent 平台
   A：二进制漏洞研究员+CTF pwn自动化工具

3. 默认文档语言继续全英文吗？

A：默认文档为中文,只有必须使用英文的才使用英文，其余的时候全部使用中文，并且注释也是中文

1. 面向国内用户、国际用户，还是都要？

A：先是国内用户

1. 产品边界

1. 第一阶段只做 CTF pwn，还是也覆盖真实漏洞研究？

A：第一阶段只做CTF pwn

1. 是否明确禁止未授权真实目标？

A：是，授权只有人类明确要求，否则是不授权

1. 是否支持远程服务连接，例如 nc host port？

A: 支持，因为pwn需要

1. 是否允许 Agent 自动对远程服务发 payload？

A：在CTF pwn的环境里面允许，在正常的环境里面只有人类明确授权

1. 是否允许 Agent 自动生成 exploit？

A：是

1. 是否允许 Agent 自动执行 exploit？
   A：是

2. 是否允许 Agent 获取 shell 后继续交互？
   A：最多允许读取文件,不允许修改文件和破坏文件

3. 是否支持 malware-like challenge，还是只处理普通 ELF？
   A：都支持

4. 是否支持 Windows PE、Mach-O，还是第一阶段只支持 Linux ELF？
   A：第一阶段只支持Linux

5. 是否支持多架构：x86_64、i386、arm、aarch64、mips？
   A: 是

6. 第一版是否只支持本地 Linux？
   A：包括远程的linux

7. 是否需要支持 WSL、macOS、Docker 环境？
   A：支持，

8. 目标用户

9. 主要用户是谁？
   - CTF 新手
   - 中高级 pwn 选手
   - 战队
   - 安全研究员
   - 教学场景

   A: 中高级 pwn 选手 战队 安全研究员 教学场景

10. 用户是否懂 pwntools/GDB？
    A: 是

11. 你希望它更多是“自动求解”，还是“辅助人类解题”？
    A：自动求解

12. 用户是否需要看到 Agent 的完整推理过程？
    A：是，但是一般是折叠的，除非人类手动打开思考过程

13. 用户是否更看重速度、成功率、可解释性，还是学习价值？
    A：成功率>速度>可解释性>学习价值

14. 是否需要团队协作，例如多人共享同一个 challenge workspace？
    A: 暂时不考虑

15. MVP 范围

16. 第一版必须完成哪条闭环？- 静态 triage - crash offset - ret2win - ret2libc - ROP chain - format string - heap - shellcode
    A：这些都需要完成，但是优先做出基础的，包括ida的mcp接入和gdb的mcp接入

17. 第一版是否必须能自动 solve 一个简单 pwn 题？
    A：是

18. 是否要内置 demo challenge/fixture？
    A：是

19. 第一版是否需要 TUI，还是 CLI + 文档先行？
    A：需要TUI

20. 第一版是否必须支持模型 tool calling？
    A：是

21. 第一版是否必须支持多个模型 provider？
    A：至少支持外部的大模型和本地的大模型

22. 你希望第一个可展示版本是什么样的命令？

例如：

vanta ./chall
vanta triage ./chall
vanta solve ./chall

A：我希望能够看到的是我输入vanta，出现TUI，然后我直接对话，binary的路径是：xxxxx，对它进行分析，先分析伪代码，输出到output.md，包括分析的内容，可能的攻击方式。最后获取flag

1. UX/TUI 体验

1. 你想更接近 Claude Code、Codex CLI，还是自定义 pwn 工作台？
   Claude code

1. TUI 布局希望是什么？- 单列聊天流 - 双栏：对话 + 状态面板 - 三栏：文件/状态/对话 - 可折叠工具日志
   A: 双栏：对话 + 状态面板 三栏：文件/状态/对话 可折叠工具日志

1. 是否需要始终显示：
   - checksec
   - 架构
   - libc
   - remote target
   - 当前 exploit 状态
   - crash offset
   - gadget 信息

A： 需要显示，可以在TUI开辟出多个窗口，一个窗口用于存放这些不变的信息；

1. 工具调用日志默认展开还是折叠？
   A: 折叠

2. Agent 的“思考过程”要显示到什么程度？注意模型真实 hidden reasoning 不应该暴露，但可以显示 plan/summary。
   A：同意

3. 是否需要 slash commands？- /triage - /crash - /offset - /gdb - /exploit - /report - /compact
   A: 需要，最好再加入一个一键去进行攻击和漏洞挖掘的slash commands

4. 是否需要 vim/emacs 快捷键？
   A：可以配置vim的，这个只做拓展，

5. 是否需要 session resume？
   A：需要，到时候用于复现或者其他的情况

6. 是否需要 transcript 回放？
   A: 需要，

7. 是否需要导出 writeup？
   A：需要，ctf是导出write up，如果是漏洞挖掘就是导出报告

8. 是否需要 dashboard/web UI，还是只做 terminal？
   A：不需要
9. 技术栈选择

10. 你偏向什么语言做主 CLI？
    - TypeScript + Ink
    - Rust + Ratatui
    - Python + Textual/Rich

A: rust

1. 你能接受 TS Core + Python Worker 的混合架构吗？
   A: 能

2. 是否希望尽量少依赖 Node？
   A: 如果可以尽量减少，如果有需要那就一定需要写到READEME.md上

3. 是否希望主 runtime 用 Rust，UI 用 TS，worker 用 Python？
   A：是

4. 是否计划作为 npm 包、pip 包、cargo crate，还是二进制发布？
   A：npm和cargo crate

5. 是否要求跨平台安装简单？
   A：不要求

6. 是否接受 Docker 作为强依赖，还是只能可选？
   A：不接受，只是作为可选

7. 是否接受 uv 管理 Python worker？
   A：是，并且默认是uv

8. 是否接受 pnpm 管理 TUI？
   A：是

9. 是否需要支持本地模型，如 Ollama/vLLM？
   A：是，并且优先支持llama，参考我部署在本地的模型，启动脚本路径在~/tools/localAi-GEmini/,注意，这是我的本机路径，不要固化

10. 模型 Provider

11. 第一版支持哪些模型？
    - OpenAI
    - Anthropic
    - Gemini
    - DeepSeek
    - Qwen
    - Ollama
      A：DeepSeek,OpenAI Anthropic, llama
12. API key 怎么传入？环境变量、系统 keychain、每次输入、配置文件引用？
    A：生成配置文件，~/.vanta/config/toml

13. 当前 Trellis 规则禁止 API key 存储。你是否坚持这一点？
    A: 是

14. 是否需要 provider fallback？
    A: 需要

15. 是否需要 model profiles，例如 fast、smart、cheap？
    A：需要

16. 是否需要 token/cost 统计？
    A:以后考虑，暂时不考虑

17. 是否允许把 binary metadata 发给云模型？
    A:以后考虑，暂时不考虑

18. 是否需要“本地-only 模式”？
    A:以后考虑，暂时不考虑

19. 安全模型

20. Target binary 默认是否视为不可信？
    A：在CTF中默认是可信的，在二进制漏洞挖掘中是不可信的

21. 默认运行是否必须进入 sandbox？
    A：是

22. Sandbox 用什么？- Docker - nsjail - firejail - bubblewrap - qemu-user - 先不做
    A：暂时不做

23. 没有 sandbox 时是否允许运行 target？
    A: 是 CTF直接允许

24. 生成的 exploit 是否默认需要人工确认后执行？
    A：同一个payload，第一次需要，

25. 远程连接是否需要人工确认？
    A：同一个靶机第一次需要

26. 获取 shell 后是否禁止执行危险命令？
    A：是，仅仅允许读文件，不允许写或者破坏

27. 是否记录所有 payload？
    A：可以记录在文件里面

28. 是否允许日志包含远程返回内容？
    A：是，日志分为本地和远程两种格式

29. 是否要做敏感信息 scrub？
    A: 对于本机的需要，对于其他人的不需要

30. 是否支持 challenge 文件隔离目录？
    A：不需要

31. 是否允许 Agent 写入 challenge 目录外的文件？
    A：允许，但是需要鉴权

32. Tool Runtime

33. 你希望工具是内置为主，还是插件为主？
    A：插件，但是一些基本的工具需要内置，比如：bash，objdump，python，

34. 工具调用权限等级怎么分？
    - read-only
    - write workspace
    - execute local
    - network
    - exploit
      A:智能分配

35. 哪些工具第一版必须支持？- file - checksec - readelf - objdump - strings - nm - gdb - pwndbg - pwntools - ROPgadget - ropper - one_gadget - angr - z3
    A: file checksec readelf objdump strings nm gdb pwndbg pwntools ROPgadget ropper one_gadget ida

36. 没装某个工具时是降级、提示安装，还是自动安装？
    A：提醒安装，给出选择，如果用户选择不安装就降级

37. 是否允许 Agent 自动安装依赖？
    A：提醒安装，给出选择，如果用户选择不安装就选择其他的方式

38. 工具输出保存多久？
    A：给出报告之后，在这之前可以写在文件里面，

39. 工具结果是否需要 hash 和 evidence ref？
    A: 需要

40. 是否需要 tool replay？
    A：需要

41. 是否支持后台任务、取消任务、并发任务？
    A：是

42. GDB / 动态分析

43. 第一版是否必须集成 GDB？
    A: 是
44. 是否要求 pwndbg/gef/peda？
    A：pwndbg即可

45. GDB 是一次性 batch，还是长驻 session？
    A：长驻，直到对话结束，哪怕是人类手动结束

46. 是否需要 core dump 分析？
    A: 是

47. 是否需要自动 cyclic offset？
    A：是，并且这个应该在代码审计的部分就做好

48. 是否需要自动提取寄存器、栈、maps、backtrace？
    A：需要的时候再提取

49. 是否要支持 attach 到进程？
    A：调试脚本的时候需要

50. 是否要支持 qemu-user + gdbserver？
    A：需要，但是暂时不着急

51. 是否需要 heap 分析，还是后续版本？
    A：需要，

52. GDB 输出要保存成文本、JSON，还是两者都要？
    A：输出成适合AI阅读的格式即可

53. Evidence Store / Workspace

54. workspace 目录名用什么？- .vanta/ - .pwnagent/ - .vanta-pwn/
    A：vantaPwn

55. 是否允许在 challenge 目录中创建 workspace？
    A: 是
56. workspace 要保存哪些内容？
    - session transcript
    - facts
    - crashes
    - payloads
    - generated exploit
    - reports
    - tool logs
    - model summaries
      A： 都需要
57. 是否需要可删除隐私数据？
    A：询问人类，由人类手动确认

58. 是否需要压缩归档？
    A：询问人类，由人类手动确认

59. 是否需要导出给队友？
    A：询问人类，由人类手动确认

60. 是否需要支持一个 workspace 多个 binary？
    A: 是
61. facts 用 JSON，notes 用 Markdown，可以吗？
    A: 可以

62. 是否需要 SQLite？
    A：暂时不需要

63. 是否需要 schema version 和 migration？
    A: 需要
64. 插件和扩展

65. 是否第一版就设计插件协议？
    A： 是

66. 插件用 Node、Python，还是跨语言 JSON-RPC？
    A：node python都行

67. 是否支持 MCP？
    A：是

68. 是否允许第三方工具插件？
    A：暂时不考虑

69. 是否需要插件权限声明？
    A：暂时不考虑

70. 是否需要插件签名或信任等级？
    A：暂时不考虑

71. 是否计划支持其他 CTF 类别？
    - reverse
    - crypto
    - web
    - forensics
      A:等pwn的完善了，再考虑

72. pwn 是唯一方向，还是 Vanta 是安全 Agent 平台？
    A： Vanta 是安全 Agent 平台

73. 测试与质量门禁

74. 第一版你能接受哪些测试？- unit tests - integration tests - golden output tests - fixture binary tests - TUI rendering tests - GDB smoke tests - sandbox tests
    A:都接受

75. 是否可以把小型 vulnerable ELF fixture 放进 repo？
    A:是，但是不推送

76. 如果不能放 binary，是否可以从 C 源码测试时编译？

77. 是否需要 CI 跑 GDB？
    A: 不需要，只需要测试即可

78. 是否需要 CI 跑 Docker sandbox？
    A: 不需要，暂时不考虑，

79. 是否需要真实模型调用测试，还是全部 mock？
    A：是，我将使用deepseek和本地模型进行测试

80. 是否要有 benchmark？
    A: 是

81. 成功标准怎么定义？例如 offset 正确、exploit 输出 flag、报告生成。
    A：exploit获取flag > 代码分析正确 > 报告生成

82. 发布与分发

83. 第一版怎么安装？
    - npm global
    - pipx
    - cargo install
    - GitHub release binary
    - Docker image
      A： npm 和 cargo install

84. 是否需要离线安装？
    A：否

85. 是否需要自动更新？
    A：否

86. 版本策略是否 SemVer？
    A: 是

87. 是否需要 nightly/dev channel？
    A：是

88. 是否要发布到 npm/PyPI/crates.io？
    A: no

89. 是否需要 Docker image 包含 pwn 工具链？
    A：否，以后再考虑

90. 合规与开源风险

91. 是否明确采用 clean-room 原则？
92. 是否允许参考公开分析文档，但禁止复制泄露源码？
    A：如果有需要可以复制代码片段，

93. 是否需要在文档里写明“不基于泄露源码”？
    A：不需要

94. 是否允许使用 Claude Code / Codex 作为对标描述？
    A：允许

95. 是否担心商标或品牌混淆？
96. 是否计划商业化？
97. 是否需要贡献者签署 DCO/CLA？

98. 当前 Trellis 框架适配

99. 是否保留 Trellis 作为治理框架名称，还是完全改成 Vanta？
    A：完全修改成Vanta

100. CLAUDE.md 和 CODEX.md 是否都保留？
     A：是

101. AGENTS.md 里是否继续要求所有 artifacts 用英文？
     A：如果不是必须，那就改为中文

102. 是否继续强制 signed commits？
     A：是

103. 是否继续禁止 TODO/FIXME/HACK？
     A：是
104. 是否继续要求每次代码变更更新 state/progress.json？
     A：是
105. 是否接受 .config/arch-boundaries.toml 作为硬门禁？
     A：是
106. Rust 1.92、Python 3.13、pnpm 10 是否都保留？
     A：是

107. 是否会新增 Cargo workspace？
     A：如果有需要，允许

108. 是否需要 apps/cli、tools/pwn-workers、crates/core 这种目录结构？
     A：如果这种格式不够优秀可以换更优秀的

109. 命名和目录结构

110. CLI 命令叫什么？
     - vanta
     - pwnagent
     - vanta-pwn
       A：vanta

111. 代码目录想怎么放？
     - apps/cli
     - packages/tui
     - packages/core
     - tools/pwn-workers
     - crates/\*
       A：apps/cli

112. workspace 目录叫什么？
     A: vanta-workspace

113. 默认生成 exploit 文件叫什么？
     - exploit.py
     - solve.py
     - pwn.py
       A: exploit.py

114. 报告文件叫什么？
     - writeup.md
     - report.md
       A:如果是CTF,并且获取了flag，那就叫writeup.md；否则就叫report.md

115. 用户配置文件放哪里？
     - repo-local
     - home config
     - 不存配置
       A：$HOME/.vanta/

116. 成功标准

117. 你认为第一个 milestone 完成的证据是什么？
     A: 知道当前的所有的二进制的漏洞，知道一些cve，至少可以调用mcp去完整的分析伪代码去辅助做pwn题。

118. 第一个公开 demo 要展示什么？
     A：pwn的辅助能力

119. 你希望它在什么题型上稳定工作？
     A：所有的题型

120. 成功率重要，还是可解释过程重要？
     A：都重要，

121. 你希望多久做出第一个原型？
     A：一天

122. 这个项目是个人长期项目、团队项目，还是准备开源吸引贡献者？
     A：目前是个人项目，会开源，
