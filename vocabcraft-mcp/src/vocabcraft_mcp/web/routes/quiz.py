# src/vocabcraft_mcp/web/routes/quiz.py
"""出题与评分路由

提供生成 Web 考题、展示考题、提交评分、显示结果的路由。
"""
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse

from vocabcraft_mcp.web.app import templates
from vocabcraft_mcp.web import services

router = APIRouter()


@router.post("/api/quiz/{vocab_id}/generate", response_class=HTMLResponse)
async def generate_quiz_partial(request: Request, vocab_id: str, quiz_type: str = ""):
    """为词汇生成考题并返回考题片段"""
    result = services.generate_web_quiz(vocab_id, quiz_type)
    if result is None:
        raise HTTPException(status_code=404, detail="词汇不存在或无法生成考题")
    return templates.TemplateResponse(
        request,
        "partials/quiz.html",
        {"quiz": result["quiz"], "result": None},
    )


@router.get("/partials/quiz/{quiz_id}", response_class=HTMLResponse)
async def quiz_partial(request: Request, quiz_id: str):
    """返回指定考题的展示片段"""
    storage = services._get_storage()
    quiz = storage.load_quiz(quiz_id)
    if quiz is None:
        raise HTTPException(status_code=404, detail="考题不存在")
    quiz_dict = quiz.model_dump()
    vocab = storage.load_vocab(quiz.vocab_id)
    if vocab is not None:
        quiz_dict["language"] = vocab.structured.language
    return templates.TemplateResponse(
        request,
        "partials/quiz.html",
        {"quiz": quiz_dict, "result": None},
    )


@router.post("/api/quiz/{quiz_id}/grade", response_class=HTMLResponse)
async def grade_quiz_partial(request: Request, quiz_id: str):
    """提交答案并返回评分结果片段

    同时兼容 HTMX 表单提交（form data）与测试中的 query param。
    """
    storage = services._get_storage()
    quiz = storage.load_quiz(quiz_id)
    if quiz is None:
        raise HTTPException(status_code=404, detail="考题不存在")

    form = await request.form()
    pos = form.get("pos", "")
    definition = form.get("definition", "")
    if pos and definition:
        response = f"{pos}|{definition}"
    else:
        response = form.get("response", "")
        if not response:
            response = request.query_params.get("response", "")

    result = services.grade_web_quiz(quiz_id, response)
    return templates.TemplateResponse(
        request,
        "partials/quiz_result.html",
        {"quiz": quiz.model_dump(), "result": result},
    )


@router.get("/api/quiz/{quiz_id}/result", response_class=HTMLResponse)
async def quiz_result_partial(request: Request, quiz_id: str):
    """返回最近一次评分结果片段（用于重载）"""
    storage = services._get_storage()
    quiz = storage.load_quiz(quiz_id)
    if quiz is None:
        raise HTTPException(status_code=404, detail="考题不存在")
    return templates.TemplateResponse(
        request,
        "partials/quiz_result.html",
        {"quiz": quiz.model_dump(), "result": None},
    )
