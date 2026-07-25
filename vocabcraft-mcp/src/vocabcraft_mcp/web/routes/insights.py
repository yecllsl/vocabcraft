# src/vocabcraft_mcp/web/routes/insights.py
"""语种洞察路由 — N-05 复习统计可视化深化

按语种（de / zh_classical）展示遗忘曲线、薄弱词分布、掌握度分布。
"""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse

from vocabcraft_mcp.web.app import templates
from vocabcraft_mcp.web import services

router = APIRouter()

# 允许的语言参数；非法值回退到 de
_ALLOWED_LANGUAGES = {"de", "zh_classical"}
_DEFAULT_LANGUAGE = "de"


def _normalize_language(lang: str | None) -> str:
    """归一化语言参数，非法值回退默认"""
    if lang in _ALLOWED_LANGUAGES:
        return lang
    return _DEFAULT_LANGUAGE


@router.get("/insights", response_class=HTMLResponse)
async def insights_page(request: Request):
    """渲染语种洞察主页面（默认 de）"""
    summary = services.get_insights_summary(_DEFAULT_LANGUAGE)
    return templates.TemplateResponse(
        request,
        "partials/insights.html",
        {"summary": summary, "current_language": _DEFAULT_LANGUAGE},
    )


@router.get("/partials/insights", response_class=HTMLResponse)
async def insights_partial(request: Request, language: str = "de"):
    """返回语种洞察片段 HTML（HTMX 切换语种用）"""
    lang = _normalize_language(language)
    summary = services.get_insights_summary(lang)
    return templates.TemplateResponse(
        request,
        "partials/insights.html",
        {"summary": summary, "current_language": lang},
    )


@router.get("/api/insights")
async def insights_api(language: str = "de"):
    """返回语种洞察 JSON"""
    lang = _normalize_language(language)
    return services.get_insights_summary(lang)
