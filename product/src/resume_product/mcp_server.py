# -*- coding: utf-8 -*-
"""resume_product.mcp_server — 简历工具 MCP server（W10 ⭐ PAEG 生态）。

像 MCP 一样直接安装即可用：
- pip install + MCP 配置声明即接入
- console_scripts: resume-mcp
- 可被 PAEG 主 Agent 调度（工具 schema + 统一调用契约）
"""

from __future__ import annotations

import json
import os
import sys

try:
    from fastmcp import FastMCP
except ImportError:
    FastMCP = None

from .executor import execute

SERVER_NAME = "resume-product"


def build_server() -> "FastMCP":
    """构建 MCP server（幂等）。"""
    if FastMCP is None:
        raise RuntimeError("fastmcp 未安装：pip install 'resume-product[mcp]'")

    mcp = FastMCP(name=SERVER_NAME, strict_input_validation=True)

    @mcp.tool()
    def generate_resume(experiences_json: str, target_role: str = "",
                        format: str = "markdown") -> str:
        """生成简历：结构化经历 → 定向简历（markdown/html）。"""
        return execute("generate_resume", {
            "experiences_json": experiences_json,
            "target_role": target_role, "format": format})

    @mcp.tool()
    def enrich_experience(raw_text: str) -> str:
        """经历文本 → 结构化事实卡（主张校验，引用原文）。"""
        return execute("enrich_experience", {"raw_text": raw_text})

    @mcp.tool()
    def list_role_packs() -> str:
        """可用通用 Role Pack 清单（行业方向）。"""
        return execute("list_role_packs", {})

    @mcp.tool()
    def list_tools() -> str:
        """工具 schema 清单（MCP tools/list 等价）。"""
        from .tools.schema import list_tool_schemas
        return json.dumps({"ok": True, "tools": list_tool_schemas()},
                          ensure_ascii=False)

    # ---- 基线对齐补全工具（批次 A-E · 20 工具全量暴露）----

    @mcp.tool()
    def evaluate_fit(posting: dict, profile: dict) -> str:
        """职位匹配度五维度评估评分（资格门+语言门+技术/经验/行为/地点/职业对齐）。"""
        return execute("evaluate_fit", {"posting": posting, "profile": profile})

    @mcp.tool()
    def trim_experience(entries: list, target_role: str = "", max_items: int = 5) -> str:
        """相关性加权裁剪（相关性+独特性+依赖度，非机械时间裁剪）。"""
        return execute("trim_experience", {
            "entries": entries, "target_role": target_role, "max_items": max_items})

    @mcp.tool()
    def rank_postings(postings: list, profile: dict) -> str:
        """多职位批量评分排序。"""
        return execute("rank_postings", {"postings": postings, "profile": profile})

    @mcp.tool()
    def salary_benchmark(role: str = "", region: str = "", years: float = 0,
                         sources: list = None, expected: float = None) -> str:
        """薪资基准对比（分位区间 + 低于/符合/高于市场结论）。"""
        return execute("salary_benchmark", {
            "role": role, "region": region, "years": years,
            "sources": sources, "expected": expected})

    @mcp.tool()
    def prepare_interview(role: str = "", company: str = "", profile: dict = None,
                          jd_text: str = "") -> str:
        """面试准备（STAR 故事 + 高频难题 + 反问清单）。"""
        return execute("prepare_interview", {
            "role": role, "company": company, "profile": profile, "jd_text": jd_text})

    @mcp.tool()
    def simulate_interview(role: str = "", profile: dict = None, rounds: int = 1) -> str:
        """STAR 框架模拟面试（问答结构）。"""
        return execute("simulate_interview", {
            "role": role, "profile": profile, "rounds": rounds})

    @mcp.tool()
    def track_application(company: str = "", role: str = "", source: str = "",
                          deadline: str = "") -> str:
        """记录一条求职申请（状态机 applied→interview→offer→rejected→withdrawn）。"""
        return execute("track_application", {
            "company": company, "role": role, "source": source, "deadline": deadline})

    @mcp.tool()
    def generate_followup(entry: dict, days_since: int = 7) -> str:
        """生成跟进信（按 7/14/21 天分档）。"""
        return execute("generate_followup", {"entry": entry, "days_since": days_since})

    @mcp.tool()
    def analyze_skill_gaps(jobs: list, profile: dict) -> str:
        """技能缺口分析 + 学习路径建议（频率热图 + 权重）。"""
        return execute("analyze_skill_gaps", {"jobs": jobs, "profile": profile})

    @mcp.tool()
    def claim_review(claims: list, evidence: dict = None) -> str:
        """事实校验（verified/unverified/exaggerated，不静默升级）。"""
        return execute("claim_review", {"claims": claims, "evidence": evidence})

    @mcp.tool()
    def generate_versions(content: str = "", target: str = "") -> str:
        """多版本输出（稳妥版/专业版/高竞争力版）。"""
        return execute("generate_versions", {"content": content, "target": target})

    @mcp.tool()
    def decompose_experience(raw_experience: str = "", target_direction: str = "") -> str:
        """经历拆解六要素（研究对象/方法/工具/角色/交付物/可迁移能力）。"""
        return execute("decompose_experience", {
            "raw_experience": raw_experience, "target_direction": target_direction})

    @mcp.tool()
    def tag_experience(experience: dict) -> str:
        """经历标签化（能力分类体系）。"""
        return execute("tag_experience", {"experience": experience})

    @mcp.tool()
    def list_templates() -> str:
        """列出简历模板（moderncv_banking/resume_html/generic_md 等）。"""
        return execute("list_templates", {})

    @mcp.tool()
    def register_template(template_id: str = "", name: str = "", format: str = "",
                          path: str = "") -> str:
        """注册自定义模板（校验文件存在 + 格式合法）。"""
        return execute("register_template", {
            "template_id": template_id, "name": name, "format": format, "path": path})

    @mcp.tool()
    def compile_latex(tex_path: str = "", workdir: str = "") -> str:
        """LaTeX 编译链 + 视觉校验（lualatex，2 页硬要求）。"""
        return execute("compile_latex", {"tex_path": tex_path, "workdir": workdir})

    @mcp.tool()
    def portal_search(portal_name: str = "", query: str = "", portal_path: str = "") -> str:
        """职位门户搜索（可扩展适配器架构）。"""
        return execute("portal_search", {
            "portal_name": portal_name, "query": query, "portal_path": portal_path})

    # ═══════════════════════════════════════════════════════════
    # §3.116 ⭐ R3 MCP 三原语补全：resources + prompts
    # ═══════════════════════════════════════════════════════════

    @mcp.resource("resume-templates://list")
    def resume_templates_resource() -> str:
        """简历模板清单（read-only 资源）。"""
        return execute("list_templates", {})

    @mcp.resource("resume-role-packs://list")
    def resume_role_packs_resource() -> str:
        """角色包清单（read-only 资源）。"""
        return execute("list_role_packs", {})

    @mcp.prompt()
    def resume_build_workflow(target_role: str) -> str:
        """简历生成工作流模板（经历→事实校验→定向→三档→导出）。"""
        return (
            f"请按简历生成流程制作简历（目标岗位：{target_role}）：\n"
            "1. 经历拆解：原始经历 → 方法/工具/角色/交付物 → 可迁移能力\n"
            "2. 事实校验：未确认信息不升级、不编造（ClaimGate 12 项检查）\n"
            "3. JD 匹配：五维评分 + 匹配项/缺失项标注\n"
            "4. 定向表达：STAR 量化（S/T/A/R 分段 + 数据）\n"
            "5. 多版本：稳妥/专业/高竞争力三档横向对比\n"
            "6. 导出：Word/PDF/HTML（ATS 兼容校验）\n"
        )

    @mcp.prompt()
    def resume_ats_report(ats_json: str) -> str:
        """ATS 兼容性报告模板。"""
        return (
            "请根据 ATS 校验结果生成报告：\n"
            "1. 关键词覆盖率（命中/缺失清单）\n"
            "2. 阅读顺序（联系方式位置）\n"
            "3. 量化成果检查\n"
            "4. 改进建议（补关键词/补量化/调顺序）\n\n"
            f"ATS 数据：{ats_json}\n"
        )

    return mcp


def main():
    """CLI 入口：启动 MCP server（stdio）。"""
    if FastMCP is None:
        print("错误：fastmcp 未安装，请先 pip install 'resume-product[mcp]'",
              file=sys.stderr)
        sys.exit(1)
    server = build_server()
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
