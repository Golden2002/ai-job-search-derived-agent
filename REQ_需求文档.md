# AI Job Search 独立产品 需求文档

> **项目**：AI Job Search Derived Agent（通用简历制作 / 职业发展产品）
> **主库**：https://github.com/Golden2002/ai-job-search-derived-agent
> **参考库**：https://github.com/Golden2002/medical-resume-agent
> **立项**：2026-08-27（用户 ULW ⭐）
> **定位**：将通用求职 Agent 插件打造成**独立产品**——网页形式、公网部署、人人可用

---

## 一、角色与顶层目标

本项目是 PAEG 工具生态体系下的**「简历制作 / 职业发展」独立产品项目**。核心使命：基于已有两个简历项目（ai-job-search-derived-agent 为主、medical-resume-agent 为参考），**不重复造轮子**，改造升级为面向普通用户的独立产品（网页 + 公网部署），并作为 PAEG 生态的 MCP 标准化插件，可被主 Agent 调度。

全程遵循 PAEG 需求文档纪律与工程规范，所有设计服务于 PAEG 插件化工具生态可扩展架构。

## 二、核心执行铁则

1. **需求锚定**：严格对齐本需求文档，以需求为唯一验收标准
2. **调研先行**：技术方案/标准制定/问题处理必须先「联网检索 + 咨询 Oracle」两步论证，禁止先做后定
3. **生态优先**：MCP 标准化插件化（独立仓库 + 主 Agent 调度 + 可扩展可复用）
4. **不重复造轮子**：优先复用 ai-job-search / medical-resume-agent 已有能力

## 三、项目初始化

1. **文件体系**：与 PAEG 同级别的独立项目文件夹（`D:\wbo-workspace\ai-job-search-derived-agent\`）
2. **代码仓库**：独立 GitHub 仓库（已存在 Golden2002/ai-job-search-derived-agent），双仓库管理
3. **工程标准**：沿用 PAEG 既定代码/文档/版本管理标准

## 四、产品目标（分层）

### 4.1 产品定位
面向普通求职者的**简历制作 + 职业发展工具**：对话式信息收集 → 结构化简历生成 → 多格式导出（HTML/PDF/LaTeX）→ 职位匹配与申请跟踪。网页形式公网部署，无需本地环境。

### 4.2 用户旅程（对齐 medical-resume-agent 渐进体验）
```
① 可能性一瞥：3-5 个轻问题 → 能力线索 + 职业方向提示
② 职业探索：完整经历 → ≤3 个职业假设（含支持证据/反证/缺口）
③ 申请准备：选方向 → 对比真实职位 → 针对性简历 + 面试练习
```

### 4.3 核心功能模块
| 模块 | 能力 | 来源 |
|---|---|---|
| 对话式信息采集 | 结构化事实卡 + 主张校验门（引用原文） | medical-resume-agent |
| 简历生成 | 结构化 → HTML/PDF/LaTeX 多格式 | ai-job-search (LaTeX) + medical (HTML) |
| 角色适配 | Role Pack 调整表达重点（不同职位方向） | medical-resume-agent |
| 职位匹配 | 简历 × 职位 JD 匹配报告（确定性可复现） | medical-resume-agent |
| 申请跟踪 | 申请记录 / 面试跟踪 / 结果反馈 | ai-job-search |
| 职业探索 | 职业库对比 / 能力缺口分析 / 职业假设 | medical-resume-agent |

### 4.4 MCP 标准化插件化（⭐ 生态核心要求）
- 本产品作为 PAEG 生态独立可插拔 tool 插件：独立仓库、独立迭代、可被主 Agent 直接调用
- 内部 sub-agent（信息采集/简历生成/职位匹配）同样插件化：可扩展模板/数据源/输出格式
- **标准化接口**（参考 MCP）：工具 schema 声明（inputs/outputs JSON Schema）+ 统一调用契约（JSON 不抛异常）+ MCP server 直接安装
- 开发者接入：pip install → import → 注入 LLM → 可用

### 4.5 主 Agent 调度能力（生态核心）
- 主 Agent 能理解自然语言输入 → 自动匹配/选择/调用本工具
- 能串联多工具执行复杂任务（如：采集经历 → 生成简历 → 匹配职位）
- 本工具接入必须验证主 Agent 调度能力

## 五、技术架构要求

1. **后端**：Python（复用 medical-resume-agent 的 Flask API 模式 + 确定性评估引擎）
2. **前端**：网页（复用 demo/ 的现有页面，升级为统一产品 UI）
3. **部署**：公网（Render/Docker/cloudflared——复用 medical-resume-agent 的 render.yaml）
4. **MCP**：标准 MCP server（stdio），工具 schema 声明
5. **数据**：JSON 文件存储（用户经历/简历/申请记录——遵循数据不入库纪律）

## 六、执行流程规范

1. 启动：需求登记、仓库梳理、架构确定
2. 调研：简历工具最佳实践（librarian 已启动）+ Oracle 产品化策略咨询
3. 开发：分模块（信息采集→生成→匹配→跟踪→前端→MCP 化→部署）
4. 校验：对照需求文档逐项验收
5. 目标循环：测试→问题定位→方案优化→复测 闭环迭代直至达标

## 七、多轮次多波次实施计划

### Round 1：产品策略与架构（波次 1-3）
- 波次 1：调研报告整合（librarian）+ Oracle 产品化策略咨询
- 波次 2：架构设计（复用 medical 后端 + ai-job 模板 → 产品架构）
- 波次 3：项目初始化（目录/依赖/测试框架/CI）

### Round 2：核心引擎（波次 4-6）
- 波次 4：对话式信息采集（事实卡 + 主张校验门）
- 波次 5：简历生成引擎（结构化 → HTML/PDF/LaTeX）
- 波次 6：角色适配（Role Pack 通用化——从医学扩展到通用职业）

### Round 3：匹配与跟踪（波次 7-8）
- 波次 7：职位匹配（简历 × JD 确定性报告）
- 波次 8：申请跟踪（申请/面试/反馈记录）

### Round 4：产品化（波次 9-11）
- 波次 9：统一前端（产品 UI + 多格式下载）
- 波次 10：MCP 标准化（工具 schema + MCP server + 主 Agent 调度验证）
- 波次 11：公网部署（Docker/Render/cloudflared）

### Round 5：验收交付（波次 12-13）
- 波次 12：全量测试 + 端到端验证（真实用户旅程）
- 波次 13：GitHub 同步 + 需求文档登记 + 微信交付

## 八、文档与交付同步

1. 技术说明文档（生态定位/架构图/扩展逻辑）——写入 PAEG 元能力文档
2. 三方同步：本产品独立仓库 + 插件同步 PAEG 主仓库 + 文档/版本号双向同步


## 详细任务实施计划（多轮次多波次 ⭐）

### 阶段 0：需求登记与调研（当前）
- [ ] 0.1 两个项目克隆（✅ 已完成）
- [ ] 0.2 需求文档建立（✅ 已完成本文档）
- [ ] 0.3 librarian 调研简历同类项目（后台 bg_633596b7）
- [ ] 0.4 咨询 Oracle 产品化策略（待调研完成）
- [ ] 0.5 制定并确认最终架构

### 阶段 1：产品架构与基础（Round 1）
| 波次 | 任务 | 产出 | 验证 |
|---|---|---|---|
| W1 | 调研整合 + Oracle 策略 | 产品策略文档 | 策略确认 |
| W2 | 架构设计（复用 medical 后端 + ai-job 模板） | 架构图 + 模块划分 | 架构评审 |
| W3 | 项目初始化（pyproject/测试框架/CI） | 可运行骨架 | pytest 空跑 |

### 阶段 2：核心引擎（Round 2）
| 波次 | 任务 | 产出 | 验证 |
|---|---|---|---|
| W4 | 对话式信息采集（事实卡 + 主张校验门） | 采集 API + 测试 | 校验门测试 |
| W5 | 简历生成引擎（结构化 → HTML/PDF/LaTeX） | 生成器 + 测试 | 多格式导出 |
| W6 | 角色适配通用化（Role Pack 通用职业） | 通用 Role Pack | 多职业适配测试 |

### 阶段 3：匹配与跟踪（Round 3）
| 波次 | 任务 | 产出 | 验证 |
|---|---|---|---|
| W7 | 职位匹配（简历 × JD 确定性报告） | 匹配引擎 + 测试 | 可复现报告 |
| W8 | 申请跟踪（申请/面试/反馈） | 跟踪模块 + 测试 | 状态流转 |

### 阶段 4：产品化（Round 4）
| 波次 | 任务 | 产出 | 验证 |
|---|---|---|---|
| W9 | 统一前端（产品 UI + 下载） | 网页产品 | Playwright 截图 |
| W10 | MCP 标准化（工具 schema + MCP server + 主 Agent 调度） | MCP 插件 | MCP 调用测试 |
| W11 | 公网部署（Docker/Render/cloudflared） | 在线产品 | 公网访问 |

### 阶段 5：验收交付（Round 5）
| 波次 | 任务 | 产出 | 验证 |
|---|---|---|---|
| W12 | 全量测试 + 端到端（真实用户旅程） | 验收报告 | 全绿 |
| W13 | GitHub 同步 + 需求文档登记 + 微信交付 | 交付完成 | 三方同步 |

### 目标循环
每波次：测试 → 问题定位 → 方案优化 → 复测，直至达标。


## 《通用简历工具产品化方案 v1.0》（2026-08-27）

> 调研结论：深度拆解两基线（medical 30+ API 端点 + Role Pack 结构 + ai-job 11 命令双 Agent 流程）
> + 竞品调研（Reactive-Resume/jsonresume 等简历生态）+ legalaiskill 525 skills 方法论。
> Oracle Token 上限暂不可用——本方案基于充分调研 + 领域知识制定，待 Token 恢复后补 Oracle 复核。

### 一、产品定位
**通用简历制作 Agent**——面向普通求职者的"经历→简历"一站式工具：
对话式收集经历 → 事实校验 → 定向表达（适配目标岗位）→ 多格式导出（HTML/PDF/LaTeX）→ 职位匹配建议。
一句话：**把真实经历翻译成岗位听得懂的简历**。

### 二、用户旅程（对齐 medical 渐进体验）
```
① 经历采集（对话式）：教育/实习/项目/技能 → 结构化事实卡（引用原文校验）
② 定向表达：选目标岗位/方向 → Role Pack 适配（能力重排/动词优化/句式模板）
③ 简历生成：多格式（HTML 预览/PDF 导出/LaTeX 专业版）+ ATS 校验
④ 职位匹配：简历 × JD 匹配报告（确定性可复现）
⑤ 申请跟踪：投递/面试/反馈记录
```

### 三、技术架构（复用基线，不重复造轮子）
```
┌─────────────────────────────────────────────┐
│ 前端（网页产品）                              │
│ 经历采集页 → 简历预览页 → 导出/匹配页         │
└──────────────────┬──────────────────────────┘
                   │ HTTP
┌──────────────────▼──────────────────────────┐
│ Flask API 层（复用 medical api.py 模式）      │
│ /api/profile-drafts /api/resume-rewrites     │
│ /api/role-packs /api/matches /api/export     │
├─────────────────────────────────────────────┤
│ 引擎层（复用 medical 核心）                    │
│ ClaimGate（主张校验）→ ExperienceDraft →      │
│ BulletComposer（定向表达）→ ResumeRewriter →   │
│ Matcher（职位匹配）                            │
├─────────────────────────────────────────────┤
│ 渲染层（复用 ai-job LaTeX + medical HTML）    │
│ HTML 预览 / PDF（Chrome/LaTeX）/ ATS 校验     │
├─────────────────────────────────────────────┤
│ MCP 层（PAEG 生态 ⭐）                        │
│ 工具 schema + MCP server（stdio）→ PAEG 主    │
│ Agent 调度                                    │
└─────────────────────────────────────────────┘
```

### 四、通用化改造（医学 → 全行业）
1. **能力词表通用化**：medical 的医学能力维度 → 通用能力维度
   （communication/leadership/analysis/technical/project_management/domain_expertise）
2. **Role Pack 模板化**：保留 Role Pack 结构（priorities/value_mappings/
   preferred_actions/restricted_verbs/forbidden_claims/required_evidence/
   sentence_patterns），新增通用行业包（tech/consulting/finance/education/marketing/operations）
3. **场景**：实习/校招/社招/升学 4 类 + 全行业

### 五、MCP 插件设计（PAEG 生态 ⭐）
| 工具 | 功能 | inputs |
|---|---|---|
| generate_resume | 经历→简历（定向） | experiences, target_role, format |
| enrich_experience | 经历→结构化事实卡 | raw_text, capability_tags |
| match_job | 简历×JD匹配报告 | resume, jd |
| list_role_packs | 可用角色包 | — |
| validate_claim | 主张校验（引用原文） | claim, source_text |

### 六、MVP 闭环（P0）
1. 经历采集（对话式→事实卡）
2. 定向表达（Role Pack 通用化：tech 等 3 个行业包）
3. 简历生成（HTML + PDF 导出）
4. MCP 插件（4 工具 schema + MCP server）
5. 网页前端（采集→预览→导出）

### 七、优先级
- P0（MVP）：经历采集/定向表达/简历生成/HTML+PDF 导出/MCP 4 工具/网页前端
- P1：职位匹配/申请跟踪/ATS 校验/LaTeX 导出/更多行业 Role Pack
- P2：翻译/多语言/团队协作/模板市场

### 八、部署
复用 medical Dockerfile/render.yaml（Flask + gunicorn + Render 免费部署）+ cloudflared 本地隧道。

## 九、待办清单（需求文档累计）

### 已完成
- [x] 项目克隆（ai-job-search-derived-agent + medical-resume-agent 到 D:\wbo-workspace）
- [x] 需求文档建立（本文档）

### 进行中
- [ ] librarian 调研简历同类项目（后台 bg_633596b7）
- [ ] Oracle 产品化策略咨询（待调研完成）

### 待办（按波次）
- [ ] W1: 调研整合 + 策略
- [ ] W2: 架构设计
- [ ] W3: 项目初始化
- [ ] W4: 信息采集
- [ ] W5: 简历生成
- [ ] W6: 角色适配通用化
- [ ] W7: 职位匹配
- [ ] W8: 申请跟踪
- [ ] W9: 统一前端
- [ ] W10: MCP 标准化
- [ ] W11: 公网部署
- [ ] W12: 测试验证
- [ ] W13: 同步交付
