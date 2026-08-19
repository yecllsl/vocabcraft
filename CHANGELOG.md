# Changelog

All notable changes to this project will be documented in this file.

## [0.7.0] - 2026-08-17

### 目录重构：单目录自包含 Agent Plugin
- **`.agents/` 重命名为 `vocabcraft.plugin/`**：彻底采用 Agent Plugins 1.0 规范，目录名即插件标识，不再使用点前缀隐藏目录。
- **MCP Server 内联**：`vocabcraft-mcp/` 整体移入 `vocabcraft.plugin/vocabcraft-mcp/`，插件成为完全自包含、可整体分发到任意位置的单目录。
- **启动路径同步**：`mcp.json` 指向 `${PLUGIN_ROOT}/vocabcraft-mcp`；`runtime/trae.json` + `codebuddy.json` + `opencode.json` 指向 `${workspaceFolder}/vocabcraft.plugin/vocabcraft-mcp`；`goose.json` 的 `--directory` 指向 `vocabcraft.plugin/vocabcraft-mcp`。
- **脚本与配置同步**：`scripts/`（sync / generate-* / build-release / install / pre-commit / check-config-drift）、`package.json`、`test.yml`、根 `.gitignore` 全部指向新布局；`package.json` 的 `generate-*` 脚本因 server 下移两级，相对脚本路径由 `../scripts/` 改为 `../../scripts/`。
- **数据零迁移**：`Storage` 基于 server `__file__` 解析 `data/`，随 server 内联自动落在 `vocabcraft.plugin/vocabcraft-mcp/data/`，历史词汇数据无需迁移。
- **服务器名不变**：MCP server 名（`vocabcraft-mcp`）与 Python 包名保持不变，仅目录位置变更，各 harness 个人级配置无需改键。

### 文档与脚本一致性修正
- **A**：`AGENTS.md`（真相源与根镜像）的「MCP Tools 参考」表补全 `query_vocab` / `update_vocab` / `delete_vocab`，现完整列出 11 个工具，与 `server.py` 注册、`tools.json` 一致。
- **B**：修正 `CHANGELOG.md` 中「`.workbuddy/` → `.codebuddy/`」表述，明确为**项目级配置目录重命名**；个人级 harness 的 WorkBuddy / Hermes 仍为 `~/.workbuddy` / `~/.hermes`，互不影响（按现状保留）。
- **C**：`generate_quiz` 的题型描述（`server.py` 校验 + 生成的 `tools.json` / `workflows.json`）补全「文言文释义」，与项目定义的 5 题型一致。
- **D**：`scripts/generate-aaif-declarations.py` docstring 示例路径 `../scripts/` 修正为 `../../scripts/`。
- **E**：`scripts/build-release.ps1` / `build-release.sh` 版本默认值改为从真相源 `pyproject.toml` 动态读取，消除硬编码漂移（与 `check_version.py` 同一真相源）。

## [0.6.2] - 2026-08-16

### 安全加固
- **修复释义类题空作答评分漏洞**：`grade_quiz` 在入口统一拦截空 `response`，防止释义题走默认 grade=3 推进 SM-2 复习周期；客观题额外拦截 answer 为空的占位题，避免 `""==""` 得 grade=4 污染记忆状态。
- **修复文件路径越界读取**：`import_xlsx_vocab` 与 `parse_vocab` 对文件路径 `resolve()` 规范化并限定在项目 `data/` 目录内，拒绝 `..` 跨目录读取任意文件。

### 质量与 CI 加固
- **启用 E2E 测试**：`e2e-tests` job 在 push 时运行（11 个 Playwright 用例，覆盖页面加载、Tab 切换、图表渲染、复习出题、批量复习、词汇编辑、语种洞察）；修正 `test_batch_review_flow` 过时断言（"完成题数"→"完成词数"）。
- **消除 Node 20 弃用警告**：升级全部 GitHub Actions 至 Node 24 兼容版本（checkout@v6、setup-python@v6、setup-uv@v7、cache@v5、codecov-action@v6、upload-artifact@v5、softprops/action-gh-release@v3）。
- 修复 config-drift 脚本 bash 特有语法致 dash 下 CI 失败；pre-commit 钩子改为内容一致性校验，并在 CI 新增配置漂移检查兜底。

### 打包规范（Agent Plugins 1.0）
- 将 `.agents/` 对齐为 **Agent Plugins 1.0**（Vercel 等厂商中立打包规范，与 AAIF 无隶属关系）规范：新增 `plugin.json`（manifest）与 `mcp.json`（标准 `mcpServers` stdio 配置），`skills/` 保持 5 个 Skill；插件可作为标准 Agent Plugin 分发，各 harness 原生目录仍由 `scripts/sync-agent-configs` 单向生成、互不冲突。
- 版本号统一为 0.6.2（`plugin.json` 与 `package.json` / `tools.json` 一致）。

### 不变
- 数据模型、`(word, language)` 唯一约束、复习算法、历史数据（零迁移）。

## [0.6.1] - 2026-08-15

### 义项级通假出题
- 通假识别从记录级下沉到**义项级**：实词记录中释义以「同X，」前缀的义项（如"陈"的「同阵，布阵」）自动识别为本字，出「写本字 + 释义」题（答案 `本字|释义`，释义尾部注音剥离），评分走既有 `_grade_loan_char` 双维匹配（本字精确 + 释义模糊）。

### 采集冲突降级流程
- capture Skill 新增重复冲突降级（3.6 节）：`save_vocab` 返回"已存在"时按义项比对——已收录跳过、缺义项经用户确认后 `update_vocab` 合并，不新建记录；`word_type` 双向合并（先实词后通假保持"实词"、先通假后实词改标"实词"并保留 `original_char` 溯源）；同步 AGENTS.md 采集规则 #11。

### 不变
- 数据模型、`(word, language)` 唯一约束、独立通假字记录路径、历史数据（零迁移）。

## [0.6.0] - 2026-08-15

### 文言文虚词与通假字功能闭环
- `StructuredVocab` 新增 `word_type`（实词/虚词/通假字）与 `original_char`（通假字本字）字段，`VALID_WORD_TYPES = {"实词", "虚词", "通假字"}`。
- 文言文解析提示词增强：虚词每个义项即一个用法，通假字必须输出本字。
- 出题按 `word_type` 分支：虚词支持「句中用法辨析」「用法相同选择」，通假字支持「写本字 + 释义」。
- 评分新增 `_grade_loan_char`：本字精确匹配 + 释义模糊匹配双维度。
- Web 词汇列表 / 详情 / 编辑页新增 `word_type` 与 `original_char` 的展示与编辑。
- 五平台 Skill 文档同步更新（capture / review / quiz）。

### 文言文历史数据迁移与修复
- 为 202 个文言文词汇自动补齐 `word_type="实词"`、`original_char=""`；迁移前完整备份至 `data/backups/20260815/`。
- 修复 98 个文言文词汇顶层 `part_of_speech` 为空：从义项词性去重后按顿号连接填充，并清理释义中残留的 `【X】` 词性前缀；全部 315 个词汇文件通过 `VocabRecord` 模型校验。

### Excel 批量导入支持通假字 / 虚词
- 标准格式支持 `word_type` / `original_char` 列，文言文格式支持「词汇类型」/「本字」列。
- 非法 `word_type` 值（非 实词/虚词/通假字）校验并跳过，错误行汇总报告。

### 版本号统一
- 版本号统一至 0.6.0（pyproject.toml / package.json / install.* / README.md / DEPLOY.md / CHANGELOG / build-release.* / web/app.py），并通过 `scripts/check_version.py` 校验。

## [0.5.5] - 2026-08-11

### 新增个人级 Harness：WorkBuddy / Hermes
- WorkBuddy 与 Hermes 属于**仅支持个人级配置**的 Agent Runtime，无法通过项目级 `.agents/` 统一配置体系（单向同步到 `.trae/` / `.opencode/` / `.codebuddy/` / `.goose/`）管理，因此不纳入同步生成，亦不在 `scripts/pre-commit` 拦截名单中。
- 项目根目录新增 `.workbuddy/` 与 `.hermes/` 目录，各自仅含一份 `README.md`，说明如何为个人级 harness 加载配置：配置文件存放路径、MCP stdio 格式要求、符号链接加载机制，以及与现有配置体系的兼容性。
- `install.*` 增加 `workbuddy` / `hermes` 运行时选项：检测对应可执行文件 → 解析个人配置目录（`~/.workbuddy` / `~/.hermes`，Windows 为 `%USERPROFILE%\.workbuddy` 等）→ 写入绝对路径 `mcp.json` → 为 `AGENTS.md` 与 `skills/` 建立符号链接（失败降级复制）→ 提示验证。
- `build-release.*` 打包清单新增 `.workbuddy/README.md` 与 `.hermes/README.md`，便于发布包内用户查阅个人级配置说明。

### Runtime 重命名：WorkBuddy → CodeBuddy
- 项目面向的是腾讯 **CodeBuddy**（AI 代码编辑器），因此将**项目级**生成目录由 `.workbuddy/` 改为 `.codebuddy/`，与 CodeBuddy 的配置目录约定一致；个人级 harness 的 WorkBuddy / Hermes 仍为 `~/.workbuddy` / `~/.hermes`，互不影响。
- `.agents/runtime/workbuddy.json` → `codebuddy.json`；`scripts/sync-agent-configs.*`、`generate-platform-configs.py`、`install.*`、`.git/hooks/pre-commit` 的目标运行时由 workbuddy 改为 codebuddy。
- 修正先前对 OpenCode 的误判：`.opencode/opencode.json` 是 OpenCode 官方支持的（且优先级更高）的项目配置位置，配置本身有效。

### 新增 Agent Runtime：Goose (AAIF)
- 根目录新增 `.goose/` 目录，由 AAIF 配置层单向同步生成（Goose 为 Block 开源 Agent 运行时）。
- 新增 `.agents/runtime/goose.json`（Goose 原生 `extensions`/`stdio` schema）；新增 `scripts/generate-goose-config.py` 将其转换为 `.goose/config.yaml`，并把 `uv --directory` 解析为绝对项目路径（无需 `${workspaceFolder}`）。
- `scripts/sync-agent-configs.*` 增加 `--skip-goose` / `-SkipGoose`，同步 Skills 与 `AGENTS.md` 到 `.goose/`。
- `scripts/pre-commit` 生成目录拦截名单新增 `.goose/*`。
- `install.*` 增加 `goose` 运行时选项；`README.md` / `QUICKSTART.md` / `DEPLOY.md` 增加 Goose 配置说明与运行时计数更新。

### 文档清理：移除遗留 WorkBuddy 引用
- 清理混淆「WorkBuddy 个人级 harness」与「项目级 `.codebuddy/` 生成目录」的过时表述：`WorkBuddy` 仍作为个人级 harness 保留（install.* 写入 `~/.workbuddy`），与项目级 CodeBuddy（`.codebuddy/`）互不混淆；同步修正 `.agents/AGENTS.md`、`AGENTS.md`、`README.md`、`DEPLOY.md`、`scripts/pre-commit`、`install.*` 中的安装提示文案。

### 版本号统一
- 版本号统一至 0.5.5（pyproject.toml / package.json / install.* / README.md / DEPLOY.md / QUICKSTART.md / CHANGELOG / build-release.*），并通过 `scripts/check_version.py` 校验。

### AAIF 声明文件改为脚本生成（消除死配置漂移）
- 新增 `scripts/generate-aaif-declarations.py`，从**真实源**生成 `.agents/` 下三个 AAIF 标准声明文件，杜绝手工维护漂移：
  - `tools.json` ← 自省实时 MCP 服务（`vocabcraft_mcp.server`，11 个工具及参数 schema 自动产出）；
  - `triggers.json` ← 聚合各 Skill 的「When to Use」自然语言触发词 + `/<skill>` 命令别名；
  - `workflows.json` ← 聚合各 Skill 实际引用的 MCP 工具（按文中出现顺序）。
- 三个文件现为**生成产物**，由 AAIF 工具链（`agents publish .agents`）消费；`package.json` 新增 `generate-declarations`，`generate-configs` 与 `scripts/sync-agent-configs.*` 在同步时一并重生。
- 修正原 `triggers.json` 命令触发器格式错误（旧的 `/vocabcraft\s+(capture...)` 改为与真实命令一致的 `/capture`）。
- README / DEPLOY / 本文件注明其为脚本生成、勿手工编辑。

### 修复：Release 工作流构建失败
- 根因：`scripts/build-release.sh` 将四个运行时平台配置写入**不带点前缀**的目录（`trae/` / `opencode/` / `codebuddy/` / `goose/`），但验证步骤与 IDE 识别均要求**带点前缀**目录（`.trae/` / `.opencode/` / `.codebuddy/` / `.goose/`），导致 verify 阶段报 `Missing required files` 后 `exit 1`，Release 工作流失败。PowerShell 版 `build-release.ps1` 本就使用带点目录名，两者不一致。
- 修复：在 `build-release.sh` 新增 `CFG_DOT` 映射（`[trae]=".trae"` 等），步骤 [2]/[3] 改用 `$STAGING_DIR/${CFG_DOT[$p]}`，与 PowerShell 版对齐；本地复现构建已通过 verify（110 文件、无 `.venv`）。

## [0.5.4] - 2026-08-09

### AAIF Migration
- 配置真相源由 `.trae/` 迁移到 AAIF 标准目录 `.agents/`（含 `runtime/`、`skills/`、`AGENTS.md`、`tools.json`、`triggers.json`、`workflows.json`）。
- `scripts/sync-agent-configs` 改为以 `.agents/` 为唯一来源，单向同步到 `.trae/` / `.opencode/` / `.workbuddy/` 三平台目录（含 `AGENTS.md`、Skills、runtime 配置）。
- `scripts/generate-platform-configs.js` 重写为 Python `scripts/generate-platform-configs.py`（与项目 Python 技术栈统一）；`package.json` 的 `generate-configs` / `sync-configs` 同步更新。
- `scripts/pre-commit` 机械防线扩展为拦截 `.trae/` / `.opencode/` / `.workbuddy/` 全部生成目录的直接编辑，要求改动先落在 `.agents/`。
- `install.*` 的 FixPath 路径修复改以 `.agents/runtime/` 为对象并重新同步；`build-release.*` 打包源改为 `.agents/skills/` 与 `.agents/AGENTS.md`。
- `.agents/tools.json` 工具名对齐真实 MCP 工具（`grade_quiz` / `export_data`），并补全 `update_vocab` / `delete_vocab` / `import_xlsx_vocab`。
- 版本号统一至 0.5.4（package.json / install.* / README.md / DEPLOY.md / QUICKSTART.md / CHANGELOG）。

## [0.5.2] - 2026-08-07

### Quality / Compliance
- 引入 ruff 严格集（E,F,W,I,N,UP,B,SIM）并清零；`scripts/` 下 `import_xlsx.py` 一并修复（F401/E501/E741/W292/B905）。
- 接入 mypy 类型检查（项目源码零错误）。
- 接入 bandit 安全扫描：B704（Markup 已逐片段 escape）、B110（导入失败仅上报不放大）、B311（random 仅出题/抽样）经审查后集中豁免；B104（绑定 0.0.0.0）保留为本地工具预期行为，地址可由 `VOCABCRAFT_WEB_HOST` 覆盖。
- CI（`test.yml`）新增 `quality-gates` job 运行 ruff / mypy / bandit；单元测试增加 `--cov-fail-under=80` 覆盖率门槛。
- `ruff` / `mypy` / `bandit` 加入 `dev` 可选依赖。

### Behavior
- 评分改为四级制 **4/3/2/1**（4 完全记住 / 3 勉强记住 / 2 部分错 / 1 几乎忘），替代原 5/3/2/0 与 5/0 混合尺度；客观题答对=4、答错=1，zh_classical 释义题按词性+释义维度评 4/3/2/1，主观释义题 LLM 评分范围同步改为 1-4。grade<3 仍视为失败并重置复习周期（与 SM-2 边界一致）。
- `/stats` 维度文档对齐实现（`language`/`mastery`/`date`/`quiz_type`），移除未实现的 `overview`/`review`。
- 五个 Skill 的约束规则去重，仅保留 Prompt 防御红线，其余引用 `AGENTS.md` 为唯一真相源。

## [0.5.1] - 2026-08-04

- Fix null handling in multi-language part-of-speech import
- Optimize filtering logic for word example sentences
- Fix empty result issue in Classical Chinese question generation
- Documentation updates: Added 0.5.1 update content

## [0.5.0] - 2026-08-02

### Documentation / Baseline Alignment
- Remove deprecated PaddleOCR optional dependency notice - image collection now uses host LLM's multimodal parsing, no OCR engine installation required. Install scripts and documentation references to `uv sync --extra ocr` have been cleaned up.
- Deployment and project structure documentation aligned with actual `.trae/` directory (only `skills/`, `mcp.json`, `skill-config.json`). Removed non-existent `rules/`, `agents/`, `commands/`, `documents/`, `hooks.json`, `BMAD` descriptions.
- Install scripts remove `-InstallOcr` / `--install-ocr` parameters and OCR installation prompts.
- `README.md` / `DEPLOY.md` / `QUICKSTART.md` version references updated to `0.5.1`.