# src/vocabcraft_mcp/web/routes/stats.py
"""统计图表路由

提供统计图表页面片段和多维度统计数据 API。
"""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from vocabcraft_mcp.tools.statistics import get_statistics
from vocabcraft_mcp.web import services
from vocabcraft_mcp.web.app import templates

router = APIRouter()


@router.get("/partials/stats", response_class=HTMLResponse)
async def stats_partial(request: Request):
    """返回统计图表页片段"""
    multi_dim = services.get_multi_dim_stats()
    return templates.TemplateResponse(
        request,
        "partials/stats.html",
        {"stats": multi_dim},
    )


@router.get("/api/stats")
async def stats_api(group_by: str = "language"):
    """返回按维度分组的统计数据"""
    return get_statistics(group_by=group_by)


@router.get("/api/stats/multi-dim")
async def multi_dim_stats_api():
    """返回多维度统计数据（分布、趋势等）"""
    return services.get_multi_dim_stats()
