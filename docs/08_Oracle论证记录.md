# 《Oracle 论证记录》— 波次 2 方案论证

> 论证角色：PAEG 工具生态 · Oracle 论证官（顶级架构评审）
> 论证时间：2026-08-23 · 论证类型：波次 2 全部方案严格论证（对照顶层铁律）
> 被审文档（以同步后的 14.x 项目 docs/ 路径为准）：
> 1. `14.1_paeg-lang-style-plugin/docs/05_技术架构设计.md`
> 2. `14.3_paeg-vocabulary-plugin/docs/05_技术架构设计.md`
> 3. `14.4_legal-research-skill/docs/05_技术架构设计.md`
> 4. `14.5_ai-job-search-derived-agent/docs/05_技术架构设计.md`
> 5. `14.5_ai-job-search-derived-agent/docs/06_双基线融合实施方案.md`
> 6. `14.5_ai-job-search-derived-agent/docs/07_网页端产品设计方案.md`
> 交叉核对依据：各项目 `02_顶尖标准对标表.md`、`03_基线能力清单*.md`、`04_审计报告_波次1/2.md`、14.5 `product/` 源码与 `product/docs/基线对齐补全规格.md`

---

## 0. 论证前事实核查（Oracle 声明：以下为源码级/文档级核实结果，非推测）

| # | 核查项 | 核查结果 | 影响 |
|---|---|---|---|
| 0-1 | 简历"主基线能力清单" | **`14.5/docs/03_基线能力清单_主基线.md` 内容实为辅助基线（medical-resume-agent，82 项 A-K 域/262 测试）的清单**（文件头部与 14.6 同名文档前 60 行完全一致；全文 grep 无 job_evaluation/salary_lookup/application_tracker 等主基线内容；第 193 行"合计 82 项真实能力"）。主基线（ai-job-search-derived-agent @ 2b13c92，616 用例）的逐项能力清单**未落盘**。而 `04_审计报告_波次2.md` §一 声称"主基线…616 用例 | docs/03_基线能力清单_主基线.md | ✅ 100% 拆解"——**该结论无对应文件支撑** | 能力不退化铁则的"逐项反向审计/熔断"失去锚定 |
| 0-2 | 14.3 能力项口径 | `03_基线能力清单.md` 明确：**50 项**（A 18 / B 12 / C 8 / D 9 / E 3），并注明"早期报告口径 48 项/A 组 16 系计数差异，以本文档表格为准"；但 `02_顶尖标准对标表.md` §二 仍写"48 项：A 管线 16…"（旧口径未同步）；05 架构用 50 项口径（正确） | 文档间口径不一致，波次 4 锚定需唯一 |
| 0-3 | 14.4 基线域编号 | `03_基线能力清单.md` 域编号：A=SKILL 提示词（A1-A38）、B=示例（B1-B4）、C=validator（C1-C7）、D=case_retriever（D1-D5）、E=reasoning（E1-E6）、F=MCP（F1-F11）、G=数据库（G1-G14）、H=web（H1-H3）、I=测试（I1-I6）、J=docx 子 Skill（J1-J16，**Anthropic 专有许可**）、K=工程文档（K1-K5）。05 架构 §2 模块表写"K 域 A/F/D/J"**与清单域编号错位**（validator 实为域 C、retriever 实为域 D、reasoning 实为域 E、数据库实为域 G、报告模板实为域 A） | 波次 4 反向审计无法按清单逐项对上 |
| 0-4 | 14.4 docx 子 Skill | 域 J（J1-J16，590 行 SKILL.md + unpack/pack/validate/comment 等 15 个脚本 + 39 个 XSD）在 05 架构**完全未出现**（无保留落点、无许可处置）；对标表 §四.3 明确要求"保留原样或按许可边界处理" | 能力不退化铁则真实缺口 |
| 0-5 | 主基线 product 已有通用域角色包 | `product/data/role_packs/{tech,consulting,finance,education}_v1.json` 与 `job_evaluation/cv_trim/rank/salary_benchmark/interview_prep/application_tracker/skill_gap` 等源码已存在（product/CHANGELOG.md）；05/06 仅映射辅助基线 4 套医学 Role Packs（D-03），**未提及主基线通用域 4 套的融合去向** | 角色包来源存在并置冲突风险 |

其余核查：14.1 基线 6 文件/L-01~L-12、14.3 基线 154 测试全绿、14.4 基线 39 用例、简历双基线文件级 100% 复制——与波次 1 审计一致，无异议。

---

## 1. 论证结论总表

| 文档 | 结论 | 主要问题 | 修改建议 |
|---|---|---|---|
| 1. 14.1 语言规范校对 `05_技术架构设计.md` | **需修改** | ① P-08 性能差距无架构落点、验收表无行；② 文体口径与对标表矛盾（行业 ≥6 / 差距 ≥5 / 架构 5）；③ MCP `proofread_export(report_id)` 与 API 返回无 id，接口不闭环；④ L-11/L-12 无逐项保留落点、验收表无基线保留审计行；⑤ semantic 级"规则通道"未定义 | 补 P-08 设计+验收；统一文体口径至 6 或明示取舍；API out 增 `id` 或改无状态导出；补 L-01~L-12 逐项映射表；定义规则通道形态与 L-03 防降级包装策略 |
| 2. 14.3 外语词汇表 `05_技术架构设计.md` | **需修改** | ① 无 50 项逐项映射表，02 对标表仍为旧口径 48 项；② 基线 11 个 MCP 工具逐项保留方式未列，V-08 语种扩展无接口暴露；③ ecdict.csv(65MB) 接线无加载/许可规格；④ V-01 断裂恢复率验收口径未区分文本层（硬门）与图像 OCR（可插拔） | 补逐项映射表+对标表口径同步；补 MCP 工具保留清单与 languages 接口；补 ecdict 加载规格；拆解 V-01 验收口径 |
| 3. 14.4 法律检索 `05_技术架构设计.md` | **需修改** | ① 域编号引用错位（"K 域 A/F/D/J" vs 清单域 C/D/E/G/A）；② 域 J（docx，Anthropic 专有许可）无处置决策、A22"Word 联动"无衔接；③ workflow[].result 与 trace 结构未定义；④ LR-03"真实适配"波次 3 交付边界未定（第三方不可控）；⑤ 基线 9 个 MCP 工具未逐项映射 | 域编号按清单精确引用；补约 100 项逐域保留审计（含 J 域处置）；定义五阶每阶产出 schema 与 trace 字段；LR-03 降为骨架+文档+模拟回退；补 MCP 工具映射 |
| 4. 14.5 通用简历 `05_技术架构设计.md` | **需修改** | ① 主基线 616 用例清单缺失/错位（见 0-1），§7"双基线 100% 保留"无锚定；② `versions` 结构与 `/api/resume/build` 一次调用是否产三档全集未定义；③ 全链路 build 与 ConfirmationGate 交互（未知项/未确认）未定义；④ Role Packs 主基线通用 4 套 vs 辅助基线医学 4 套来源未定；⑤ PDF 双引擎（LaTeX/WeasyPrint）一致性口径未定 | 补齐主基线清单；定义 versions 语义与 build 的 auto/strict 模式；补角色包来源决策与统一 schema；定义三格式一致性与默认引擎口径 |
| 5. 14.5 `06_双基线融合实施方案.md` | **需修改** | ① ExperienceKernelPort 契约方法签名无 schema 类型定义（CanonicalExperience/BulletClaim 字段未给出）；② drafter_reviewer 评审环节与内核校验的衔接语义未写死（唯一可能的混写/降级漏洞点）；③ 步骤 1"独立 venv 验证后合并"二义性，无依赖对齐矩阵；④ 主基线 product 已有源码/通用角色包未在映射中体现；⑤ 风险表缺"双改写路径残留"风险 | 契约附录贴 14.6 schema 并定义错误语义；写死"评审修改必须过 ClaimGate 带追溯"；输出依赖对齐矩阵；补主基线 product 现状映射；加 grep 断言防双改写路径 |
| 6. 14.5 `07_网页端产品设计方案.md` | **需修改** | ① 与主项目 dock 的集成契约缺失（双模式只有宣言无协议）；② 在线编辑"手动微调"内容的事实归属规则未定义（与 ClaimGate 门的关系）；③ 导出与"未确认不可导出"的触发行为未定义；④ SSE 长任务实现要点未注明 | 补 dock 调度最小契约；定义手动编辑=user_asserted 证据或禁入；定义导出拦截行为；补 SSE 实现约定；验收补 dock 集成项 |

---

## 2. 逐文档修改意见（可执行，直接引用章节）

### 2.1 14.1 语言规范校对 `05_技术架构设计.md`（5 条）

1. **补 P-08 性能差距（对标表 P-08：LLM 路径异步化，基础级 ≥1 万字/分钟）**：§1 L1 接口层补"异步任务队列 + 结果缓存"，§6 部署形态补"LLM 路径异步执行（后台任务 + 轮询/SSE）"；§7 验收对照表新增一行：`P-08 性能 | 异步化+缓存 | 基础级 ≥1 万字/分钟；语法/语义级可配置异步`。当前文档对 P-08 零落点，属于差距项遗漏。
2. **统一文体口径（对标表 §一"≥6 文体"、§三 P-02"≥5 文体"、架构 §2 style_presets"≥5"三者矛盾）**：在架构 §2 与对标表 P-02 同时加注"验收基线 5 文体（学术/公文/简历/法律/通用），第 6 文体（新闻或图书）为扩展目标"；若按行业标准从严，则直接补第 6 个文体预设。两表必须同口径。
3. **修复 MCP 导出闭环（架构 §3/§4）**：`POST /api/proofread` 的 out 增加 `id`（对应数据模型 ProofreadResult.id），或把 MCP `proofread_export` 改为无状态 `proofread_export(text_or_result, fmt, domain)`；同时补统一错误码表（§4"错误返回统一 {error:{code,message}}"需给出 code 枚举），否则波次 3 前端与 MCP 对不上 report_id。
4. **补 L-01~L-12 逐项保留映射与基线审计行**：§2 模块表新增一行或在 §7 验收对照表新增行 `基线保留 | L4 基础层逐项 | L-01~L-12 反向审计`；并显式列出 L-11（全链路异常静默回退策略）与 L-12（chat_fn 注入接口）的落点——当前 L4 仅列到 L-10，L-11/L-12 缺失（对标表 §四 有 L-11/L-12 行，架构未承接）。
5. **定义 semantic 级"规则通道"形态与 L-03 防降级包装**：§2 semantic_checker"规则+LLM 双通道"需写明规则通道的具体构成（复用 L-02 AITasteSignals/L-05 重复检测信号 + 新增逻辑矛盾/概念混淆规则包），并明确"语法级 LLM 矫正引擎对 L-03 Self-Refine 采用包装调用、内核只读不改"（对标表 §四：L-03"改可追溯输出"属输出层改造，须防降级）。

### 2.2 14.3 外语词汇表 `05_技术架构设计.md`（5 条）

1. **新增"50 项逐项映射表"并同步对标表口径**：在 §2 之后新增一表，按 03 清单编号逐项（A01~A18→extractor/pipeline、B01~B12→enrich/wordbank/ecdict_bridge、C01~C08→artifacts/render、D01~D09→registry/mcp_server/web、E01~E03→web/scripts）给出"模块/保留方式/验证"，作为波次 4 反向审计锚定；并在 `02_顶尖标准对标表.md` §二 加注"48 项/A16 系旧口径，以 03 清单 50 项/A18 为准"。
2. **基线 11 个 MCP 工具逐项保留 + 语种接口暴露**：§4 MCP 表补注"基线 11 工具（D03）逐一保留/合并：generate_vocabulary→vocab_build、lookup_word→vocab_lookup、list_languages/list_generators/validate_entry/clean_examples/extract_collocations/quantile_of/bank_coverage/list_tools 全量保留"；并补 `GET /api/vocab/languages` 或 MCP Resources `vocab_languages://list`，使 V-08"≥3 语种 + 扩展点"在接口层可见（当前 languages 只在 L3 模块，无任何接口出口）。
3. **补 ecdict_bridge 加载规格**：§5 数据模型后补一条：ecdict.csv(65MB) 采用 lazy 加载/分片索引、注明许可与下载来源（复用 E01 下载脚本）、加载失败降级路径（不阻塞构建，V-02 字段覆盖降级为可选），避免波次 3 启动即内存/时间爆炸。
4. **明确导入入口一致性**：§3 API 有 `/api/vocab/import`（PDF/文本导入含 OCR 修复），但 §4 MCP 无对应工具——补 `vocab_import` MCP 工具或在 §4 注明"导入仅走 Web API，MCP 侧由宿主先完成文件落地后调 vocab_build"，二选一并写死，否则 07 网页端与 MCP 调度语义分裂。
5. **拆解 V-01 验收口径**：§7"断裂恢复率 ≥95%"需区分：文本层 OCR 修复（基线 A02 5 层管道）为硬门（测试集从基线 test_ocr_repair 扩展）；图像 OCR（V-01 ocr_image，tesseract 等可插拔）为可选能力、缺失降级不算未达标——否则 V-01 硬门依赖外部 OCR 引擎，波次 3 不可控。

### 2.3 14.4 法律检索 `05_技术架构设计.md`（5 条）

1. **模块表"能力来源"按 03 清单域编号精确引用并补 MCP 工具映射**：§2 改"K 域 A/F/D/J"为"域 C（C1-C7）/域 D（D1-D5）/域 E（E1-E6）/域 G（G1-G14）/域 A 报告模板"；§4 补"基线 9 MCP 工具（F1-F11）逐一保留/合并：validate_citation→legal_validate_citation、reasoning_analysis/recommend→legal_reason、check_timeliness/validate_report/normalize_law_name/compare_source_level/list_databases/extract_case_keywords 全量保留进新 mcp_server"。
2. **补"约 100 项逐域保留审计"，重点处置域 J（docx 子 Skill）**：新增"基线保留审计"小节：域 A（38 项提示词→SKILL.md 层原样保留 + workflow_engine 沉淀为可执行引擎）、域 B（4 示例→report_builder 验收样本）、域 I（39 测试→测试迁移）、域 K（工程件→保留）；**域 J（J1-J16，Anthropic 专有许可）显式决策**：按许可边界隔离保留（不入 MCP、不入 Web 导出链、不改代码），并写明基线 A22"选择 Word 时调用 docx skill"在新架构的衔接方式（保留提示词引用或改为调用独立 docx 工具），对标表 §四.3 的处置要求必须落笔。
3. **定义 workflow[].result 与 trace 结构**：§3 补五阶每阶产出 schema（问题解析→{question, entities, profile}；层级检索→{queries[], hits[]}；冲突适用→{conflicts[], rules}；时效梳理→{timeline[], status}；报告→{sections[], citations[]}），并定义 `trace` 为 `conclusion_id → evidence_id[]` 映射（字段级），否则 07 号五阶进度条与"5 阶可追踪"验收无法实现。
4. **LR-03 波次 3 交付边界降档**：§6/§7 明确"北大法宝/裁判文书网真实适配"波次 3 交付 = 适配器骨架 + 配置文档化 + 模拟/降级回退（沿用基线 G3/G4 占位语义）；真实 API 调用登记为外部依赖风险（认证/反爬/配额，且基线 G3 已标 TODO），不得作为波次 3 硬门——否则开发被第三方不可控因素阻塞。
5. **§7 验收表补"基线保留"行**：新增 `基线保留 | L4 内核+SKILL.md+域B/I/K+域J（按许可隔离） | 逐域反向审计`，使波次 4"能力不退化"审计有对照。

### 2.4 14.5 通用简历 `05_技术架构设计.md`（5 条）

1. **补齐主基线 616 用例清单并修正引用（最高优先级）**：`docs/03_基线能力清单_主基线.md` 当前内容为辅助基线清单（见 0-1），须重写为 ai-job-search-derived-agent @ 2b13c92 的逐项清单（12 命令 + 9 技能 + 6 门户 + 8 工具脚本 + product 27 模块，616 用例，逐项到文件/测试）；§7"双基线 100% 保留"验收改为引用该文件；同步修正 `04_审计报告_波次2.md` §一"✅ 100% 拆解"结论（当前无文件支撑）。
2. **定义 versions 结构与 build 语义**：§5 补 `versions: {conservative, professional, high_impact}` 的字段结构（每档 = sections 全量还是仅 bullets 差异）与生成语义：一次 `/api/resume/build` 产三档全集（每 bullet 带三档 text + tier）还是分档调用——与 §3 out `versions` 及 07 号"三档 tab 切换"必须一致，二选一并写死。
3. **定义全链路 build 与 ConfirmationGate 交互**：§3 补 `/api/resume/build` 遇未知项（A-04）/未确认事实（B-01）时的行为：返回 `questions[]` 阻塞等待（strict 模式）或自动跳过未确认条目并标注（auto 模式），显式 `mode` 参数；与 07 号"未知项追问 ≤3 问题"衔接，防止全链路端点绕过确认门。
4. **Role Packs 来源决策**：§2 补主基线 product 已有通用域角色包（product/data/role_packs/{tech,consulting,finance,education}_v1.json，见 0-5）与辅助基线医学 4 套（D-03）的融合方案：统一走 `role-pack.schema.json`，通用域岗位用主基线 4 套、医学域用辅助基线 4 套，注册表合并——避免 L3"Role Packs 4 套保留"与主基线 4 套并置冲突。
5. **三格式一致性口径与默认引擎**：§6 补"三格式一致 = 内容一致（文本/结构/顺序）而非像素级一致"，默认 PDF 引擎 LaTeX、无 TeX 环境降级 WeasyPrint，且**降级路径产物同样必须过 ATS 文本层校验**（R-03/R-06 联动），防止双引擎漂移导致 R-03 评分失真。

### 2.5 14.5 `06_双基线融合实施方案.md`（5 条）

1. **Port 契约补类型定义与错误语义**：§3 附录（或直接引用）14.6 的 `canonical-experience-v2.schema.json` 与 `bullet-claim-v2.schema.json` 字段，并写死方法错误语义：`draft_experience` 返回 unknowns+questions、`compose_bullets` 返回 gate_status ∈ {ready, needs_confirmation, rejected} 时的调用方处理——当前签名只有返回类型名，波次 3 无法据此实现适配层。
2. **写死 drafter_reviewer 与内核校验的衔接（防混写唯一漏洞点）**：§3 补"DrafterReviewer 评审产生的修改意见必须回流 kernel.compose_bullets/rewrite_tier 重新生成并带 rewrite_source_traceability，评审本身不得直接改写 bullet 文本；主基线 reviewer 仅作质量门"——否则双 Agent 闭环可在内核外改文本，ClaimGate 形同虚设。
3. **步骤 1 补依赖对齐矩阵**：§5 步骤 1"独立 venv 验证后合并"改为：先输出"依赖对齐矩阵"（pydantic/llm 网关/httpx 等公共依赖，取兼容版本或命名空间隔离），再在单一 venv 验证全量测试；明确"合并"的验收 = 616+262 用例在合并库一次跑绿（当前表述二义，无法执行）。
4. **补主基线 product 现状映射**：§2 L2 表补"product 已有实现（job_evaluation/cv_trim/rank/salary_benchmark/interview_prep/application_tracker/skill_gap 源码 + 通用 role_packs）→ 融合后模块 = 复制 + 调用，不重写"，与 05 §2 的"原样保留 ✅"对齐；否则波次 3 团队可能误判为从零实现。
5. **风险表补"双改写路径残留"风险**：§6 风险表新增一行：`引擎层泛化润色路径未全量替换 → 双改写路径（引擎直改 + 内核改写）| 步骤 3 完成后 grep 断言禁用引擎直改调用（如 drafter_reviewer 内不得出现改写文本的函数调用），并入步骤 6 审计`。

### 2.6 14.5 `07_网页端产品设计方案.md`（5 条）

1. **补与主项目 dock 的集成契约**：§4"与主项目 dock 集成（双模式）"只有宣言无协议——补最小契约：dock 调度（tool-resume/legal/vocab）走 MCP 直调（宿主已装 mcp_server）还是 HTTP 回调；入口端点、会话/任务传递方式、错误回传格式。三者任一，必须写死，否则"双模式"无法在波次 3 验收。
2. **定义在线编辑"手动微调"内容的事实归属规则**：§1 简历"在线编辑"页与 §1 设计要点"未确认内容不可导出"需补：用户手动输入的文本 = 用户自证（user_asserted 证据记录）直接过 ClaimGate，还是须人工确认？建议"手动编辑视为用户声明，写入 claim_ledger 并标 user_asserted，可导出但标注来源"——与 05 §3"引擎层所有生成必须经 ClaimGate"区分开（生成层 vs 编辑层不同校验策略）。
3. **定义导出拦截行为**：§1 导出页补"存在 needs_confirmation 条目时导出按钮行为"：阻止导出并定位到未确认条目（与验收"事实门控演示通过"一致），而不是静默排除。
4. **补 SSE 实现要点**：§4"SSE 进度流"注明 Flask 实现约束（生成器响应 + 线程/任务隔离 + 断连处理），并约定长任务统一返回 `job_id` + 轮询兜底，防浏览器断连丢任务；简历生成/法律检索/词汇构建三个长任务都要有。
5. **验收补 dock 集成项**：§5 验收清单新增"dock 调度三工具各一次全链路可跑通（tool-resume/legal/vocab）"，使"双模式"成为可测验收而非口号。

---

## 3. 总体裁定

**裁定结论：不予无条件放行；全部 6 份文档按本记录修改后，方可放行进入波次 3。** 理由：各方案架构骨架、分层原则与 MCP 三原语结构总体成立（无否决性架构缺陷），但存在若干"会直接导致波次 3 返工或波次 4 审计无锚定"的必改项，不满足"可行且最优"标准。属"需修改后放行"，不属"否决重做"。

### 必须修改的 TOP 项（按影响排序）

1. **【简历 · 铁律 2 熔断级】主基线 616 用例能力清单缺失/错位**：`14.5/docs/03_基线能力清单_主基线.md` 内容实为辅助基线清单；06 §4"逐项反向审计"与波次 4 熔断（缺失 ≥1 项即熔断）失去锚定。→ 重写该文件（逐项到文件/测试），同步修正 04_波次2 审计结论。
2. **【14.1 · 差距遗漏】P-08 性能差距零落点**：对标表 P-08（LLM 异步化、基础级 ≥1 万字/分钟）在 05 架构无设计、验收表无行。→ 补异步任务设计 + 验收行。
3. **【14.4 · 铁律 2 缺口】域 J（docx 子 Skill，Anthropic 专有许可）无处置决策 + 域编号引用错位**：J1-J16 能力去向空白；"K 域 A/F/D/J"与清单域 C/D/E/G/A 对不上。→ 显式处置决策 + 按清单域编号精确引用。
4. **【简历 · 双基线融合】Port 契约缺 schema、评审衔接未写死、角色包来源并置、PDF 双引擎一致性口径**：波次 3 融合实现的四个直接阻塞点。→ 按 2.5-1/2/4 与 2.4-4/5 执行。
5. **【14.1/14.3 · 可审计性】基线保留审计行/逐项映射表缺失**：L-01~L-12（14.1 缺 L-11/L-12 落点）、词汇 50 项（14.3 无逐项表）→ 波次 4"能力不退化"审计无锚定。→ 按 2.1-4、2.2-1 执行。
6. **【07 · 集成契约】dock 调度契约与手动编辑事实归属规则缺失**：双模式无法实现、编辑层 ClaimGate 语义未定义。→ 按 2.6-1/2 执行。

### 放行条件与建议顺序

- 前置（修改后）：TOP 1~6 全部闭合 → 出具"Oracle 意见落实情况"追加至各项目 `04_审计报告_波次2.md` → 放行波次 3。
- 波次 3 启动建议顺序：先执行 06 §5 步骤 1（融合骨架 + 依赖对齐矩阵），并行重写主基线能力清单（TOP 1）；再按步骤 2→6 推进，每步以 616+262 用例全绿为门。

---

## 4. 附：论证依据文件清单（本记录核实对象）

- 14.1：`02_顶尖标准对标表.md`（P-01~P-08）、`03_基线能力清单.md`（L-01~L-12）、`04_审计报告_波次1.md`、`05_技术架构设计.md`
- 14.3：`02_顶尖标准对标表.md`（V-01~V-08，48 项旧口径）、`03_基线能力清单.md`（50 项/A18）、`04_审计报告_波次1.md`、`05_技术架构设计.md`
- 14.4：`02_顶尖标准对标表.md`（LR-01~LR-11）、`03_基线能力清单.md`（域 A-K，约 100 项）、`04_审计报告_波次1.md`、`05_技术架构设计.md`
- 14.5：`02_顶尖标准对标表.md`（R-01~R-09）、`03_基线能力清单_主基线.md`（内容错位，见 0-1）、`03_基线能力清单_辅助基线.md`（82 项）、`04_审计报告_波次1/2.md`、`01_需求规格说明书_v1.0/v2.0.md`、`05/06/07`、`product/CHANGELOG.md`、`product/docs/基线对齐补全规格.md`、`product/data/role_packs/`
- 14.6：`02_顶尖标准对标表.md`、`03_基线能力清单_辅助基线.md`

> 本记录随波次 2 审计存档；各项目按 TOP 项修订后，在 `04_审计报告_波次2.md` 追加"Oracle 意见落实情况"并复评放行。
