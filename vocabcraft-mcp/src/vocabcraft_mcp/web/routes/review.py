# src/vocabcraft_mcp/web/routes/review.py
"""复习追踪路由

提供复习追踪页面片段、待复习列表 API 和标记复习完成 API。
"""
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse

from vocabcraft_mcp.web.app import templates
from vocabcraft_mcp.web import services

router = APIRouter()


@router.get("/partials/review", response_class=HTMLResponse)
async def review_partial(request: Request):
    """返回复习追踪页片段"""
    upcoming = services.get_upcoming_reviews()
    calendar = services.get_review_calendar()
    progress = services.get_language_progress()
    forgetting_curve = services.get_forgetting_curve()

    return templates.TemplateResponse(
        request,
        "partials/review.html",
        {
            "upcoming": upcoming,
            "calendar_days": calendar["calendar_days"],
            "current_month": calendar["current_month"],
            "language_progress": progress,
            "forgetting_curve": forgetting_curve,
        },
    )


@router.get("/api/review/upcoming")
async def upcoming_reviews_api():
    """返回待复习列表 JSON"""
    return {"items": services.get_upcoming_reviews()}


# ──────────────────────────────────────────
# 批量复习路由
# ──────────────────────────────────────────

@router.post("/api/review/batch/start", response_class=HTMLResponse)
async def start_batch_review_partial(request: Request):
    """开始今日批量复习，返回批量复习页面"""
    batch = services.start_batch_review()
    if batch is None:
        # 无到期词汇：返回复习页并提示
        upcoming = services.get_upcoming_reviews()
        calendar = services.get_review_calendar()
        progress = services.get_language_progress()
        forgetting_curve = services.get_forgetting_curve()
        return templates.TemplateResponse(
            request,
            "partials/review.html",
            {
                "upcoming": upcoming,
                "calendar_days": calendar["calendar_days"],
                "current_month": calendar["current_month"],
                "language_progress": progress,
                "forgetting_curve": forgetting_curve,
                "batch_error": "今天没有需要复习的单词",
            },
        )

    item = services.get_batch_review_item(batch["batch_id"], 0)
    return templates.TemplateResponse(
        request,
        "partials/batch_review.html",
        {"batch": batch, "item": item},
    )


@router.get("/api/review/batch/{batch_id}/item/{index}", response_class=HTMLResponse)
async def batch_review_item_partial(request: Request, batch_id: str, index: int):
    """返回批量复习中的指定题目"""
    item = services.get_batch_review_item(batch_id, index)
    if item is None:
        raise HTTPException(status_code=404, detail="题目不存在")
    return templates.TemplateResponse(
        request,
        "partials/batch_review_item.html",
        {"item": item, "prev_result": None},
    )


@router.post("/api/review/batch/{batch_id}/item/{index}/grade", response_class=HTMLResponse)
async def grade_batch_review_item_partial(request: Request, batch_id: str, index: int):
    """提交批量复习当前题答案，返回下一题或汇总

    同时兼容 HTMX 表单提交（form data）与测试中的 query param。
    优先读取 pos + definition 字段并拼接为 "pos|definition"。
    """
    form = await request.form()
    pos = form.get("pos", "")
    definition = form.get("definition", "")
    if pos and definition:
        response = f"{pos}|{definition}"
    else:
        response = form.get("response", "")
        if not response:
            response = request.query_params.get("response", "")

    graded = services.grade_batch_review_item(batch_id, index, response)
    if graded is None:
        raise HTTPException(status_code=404, detail="题目不存在")

    if graded["is_last"]:
        summary = services.get_batch_review_summary(batch_id)
        if summary is None:
            raise HTTPException(status_code=404, detail="批次不存在")
        return templates.TemplateResponse(
            request,
            "partials/batch_review_summary.html",
            {"summary": summary},
        )

    next_item = services.get_batch_review_item(batch_id, graded["next_index"])
    if next_item is None:
        raise HTTPException(status_code=404, detail="下一题不存在")
    return templates.TemplateResponse(
        request,
        "partials/batch_review_item.html",
        {"item": next_item, "prev_result": graded["result"]},
    )


@router.get("/api/review/batch/{batch_id}/summary", response_class=HTMLResponse)
async def batch_review_summary_partial(request: Request, batch_id: str):
    """返回批量复习汇总"""
    summary = services.get_batch_review_summary(batch_id)
    if summary is None:
        raise HTTPException(status_code=404, detail="批次不存在")
    return templates.TemplateResponse(
        request,
        "partials/batch_review_summary.html",
        {"summary": summary},
    )
