# 通用简历制作 Agent 独立产品（resume-product）

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-26%2F26-brightgreen.svg)](tests/)

<p align="center">
  <strong>通用简历制作 Agent</strong> — 把真实经历翻译成岗位听得懂的简历
  <br>
  <em>经历采集 → 事实校验 → 定向表达 → 多格式导出（Markdown / HTML / Word / PDF）</em>
  <br>
  <em>双形态：独立网页产品（公网部署）+ MCP 标准化插件（PAEG 工具生态）</em>
</p>

---

## 这是什么

通用简历制作 Agent 独立产品——面向普通求职者的"经历 → 简历"一站式工具。基于两个基线项目改造升级（不重复造轮子）：

- **主基线**：ai-job-search（通用求职 Agent 框架——drafter-reviewer 双 Agent 流程、LaTeX 渲染、申请跟踪）
- **参考基线**：medical-resume-agent（事实校验-经历拆解-定向表达方法论、Role Pack 角色适配、Flask API、Docker 部署）

## 核心能力

| 能力 | 说明 |
|---|---|
| **经历采集** | 对话式/文本输入 → 结构化事实卡（主张校验——引用原文、保留量化数据） |
| **定向表达** | Role Pack 角色适配（能力重排/动词优化/句式模板——tech/consulting/finance 等可扩展） |
| **多格式导出** | Markdown / HTML / Word（python-docx）/ PDF（固定资产渲染：resume.css + render_pdf.py） |
| **通用化** | 全行业、全岗位、全场景（实习/校招/社招/升学）；8 类通用能力维度 |
| **MCP 标准化** | 3 工具 MCP server（generate_resume / enrich_experience / list_role_packs）+ tools/list 动态发现 |
| **网页产品** | Flask API + 前端（采集 → 预览 → 三格式下载） |

## 双形态交付

```
┌─────────────────────────────────────┐
│ 形态 1：独立网页产品                  │
│ Flask API + web/index.html           │
│ 用户上传经历 → 生成简历 → 导出下载    │
│ 公网部署（Docker/Render/cloudflared）│
├─────────────────────────────────────┤
│ 形态 2：MCP 标准化插件                │
│ resume-mcp（stdio MCP server）       │
│ 3 工具 schema + 统一调用契约          │
│ 可接入 PAEG 工具生态，被主 Agent 调度 │
└─────────────────────────────────────┘
```

## 快速开始

```bash
# 安装
pip install -e "product[dev]"

# 网页产品
python -c "from resume_product.api import create_app; create_app().run(port=5123)"
# 打开 http://localhost:5123

# MCP 插件
resume-mcp    # stdio MCP server

# Python API
from resume_product.core import enrich_experience, generate_resume, list_role_packs
facts = enrich_experience("我在字节跳动实习，负责推荐算法优化，提升点击率15%")
resume = generate_resume(facts, target_role="算法工程师", format="pdf")
```

## MCP 接入（第三方开发者）

```json
{
  "mcpServers": {
    "resume-product": {
      "command": "resume-mcp",
      "args": []
    }
  }
}
```

**工具 schema**（tools/list 动态发现）：
- `generate_resume`：结构化经历 → 定向简历（markdown/html/docx/pdf）
- `enrich_experience`：经历文本 → 结构化事实卡（主张校验）
- `list_role_packs`：可用行业 Role Pack 清单

## 架构

```
前端 web/index.html
    │ HTTP
Flask API（api.py）
    │
核心引擎（core.py——ResumeEngine）
    ├─ enrich：经历 → 事实卡（主张校验）
    ├─ compose：定向表达（Role Pack 适配）
    ├─ to_html / to_docx / to_pdf：多格式渲染
    └─ render/（固定资产：resume.css + render_pdf.py）
    │
MCP 层（mcp_server.py + tools/schema.py + executor.py）
```

## 测试

```bash
python -m pytest product/tests -q    # 26/26 全绿
```

## 参考文献

本项目基于以下基线项目改造升级（不重复造轮子）：

| 参考项目 | 网址 | 复用内容 |
|---|---|---|
| **ai-job-search**（主基线） | https://github.com/Golden2002/ai-job-search-derived-agent | 通用求职 Agent 工作流框架、drafter-reviewer 双 Agent 流程、LaTeX 简历渲染、申请跟踪 |
| **medical-resume-agent**（参考基线） | https://github.com/Golden2002/medical-resume-agent | 事实校验-经历拆解-定向表达方法论、Role Pack 角色适配结构、Flask API 模式、Docker/Render 部署方案 |
| 原版 ai-job-search（上游） | https://github.com/MadsLorentzen/ai-job-search | Claude Code 求职框架（工作流设计参考） |

> 注：本项目为原创实现，复用上述项目的架构与能力维度；wordfreq/python-docx/playwright 等为第三方库（各自许可）。

## License

MIT
