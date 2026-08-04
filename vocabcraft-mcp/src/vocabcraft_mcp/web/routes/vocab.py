# src/vocabcraft_mcp/web/routes/vocab.py
"""词汇管理路由

提供词汇列表、详情、编辑、删除与独立出题入口。
"""
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse

from vocabcraft_mcp.web.app import templates
from vocabcraft_mcp.web import services

router = APIRouter()


@router.get("/partials/vocab", response_class=HTMLResponse)
async def vocab_list_partial(
    request: Request,
    language: str = "",
    keyword: str = "",
    mastery: str = "",
):
    """返回词汇列表片段"""
    vocabs = services.list_vocabs_for_web(language=language, keyword=keyword, mastery=mastery)
    return templates.TemplateResponse(
        request,
        "partials/vocab_list.html",
        {
            "vocabs": vocabs,
            "language": language,
            "keyword": keyword,
            "mastery": mastery,
            "language_options": services.SUPPORTED_LANGUAGES,
            "mastery_options": services.MASTERY_OPTIONS,
        },
    )


@router.get("/partials/vocab/{vocab_id}", response_class=HTMLResponse)
async def vocab_detail_partial(request: Request, vocab_id: str):
    """返回词汇详情片段"""
    detail = services.get_vocab_detail(vocab_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="词汇不存在")
    return templates.TemplateResponse(
        request,
        "partials/vocab_detail.html",
        {"vocab": detail},
    )


@router.get("/partials/vocab/{vocab_id}/edit", response_class=HTMLResponse)
async def vocab_edit_partial(request: Request, vocab_id: str):
    """返回词汇编辑表单片段"""
    detail = services.get_vocab_detail(vocab_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="词汇不存在")
    return templates.TemplateResponse(
        request,
        "partials/vocab_edit.html",
        {
            "vocab": detail,
            "language_options": services.SUPPORTED_LANGUAGES,
        },
    )


@router.post("/api/vocab/{vocab_id}/update", response_class=HTMLResponse)
async def vocab_update_partial(request: Request, vocab_id: str):
    """提交编辑表单并返回更新后的详情片段"""
    form = await request.form()
    updated = services.update_vocab_from_web(vocab_id, dict(form))
    if updated is None:
        raise HTTPException(status_code=404, detail="词汇不存在")
    return templates.TemplateResponse(
        request,
        "partials/vocab_detail.html",
        {"vocab": updated},
    )


@router.delete("/api/vocab/{vocab_id}", response_class=HTMLResponse)
async def vocab_delete_partial(request: Request, vocab_id: str):
    """删除词汇并返回列表片段"""
    deleted = services.delete_vocab(vocab_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="词汇不存在")
    vocabs = services.list_vocabs_for_web()
    return templates.TemplateResponse(
        request,
        "partials/vocab_list.html",
        {
            "vocabs": vocabs,
            "language": "",
            "keyword": "",
            "language_options": services.SUPPORTED_LANGUAGES,
        },
    )
