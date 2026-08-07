# src/vocabcraft_mcp/web/routes/dashboard.py
"""Dashboard 路由 — 概览页

提供概览页面片段和概览数据 API。
"""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from vocabcraft_mcp.web import services
from vocabcraft_mcp.web.app import templates

router = APIRouter()


@router.get("/partials/dashboard", response_class=HTMLResponse)
async def dashboard_partial(request: Request):
    """返回 Dashboard 片段 HTML"""
    summary = services.get_dashboard_summary()
    upcoming = services.get_upcoming_reviews()
    return templates.TemplateResponse(
        request,
        "partials/dashboard.html",
        {"summary": summary, "upcoming": upcoming},
    )


@router.get("/api/dashboard/summary")
async def dashboard_summary_api():
    """返回 Dashboard 概览 JSON（图表用）"""
    return services.get_dashboard_summary()
