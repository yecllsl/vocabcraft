# src/vocabcraft_mcp/web/app.py
"""FastAPI 应用工厂与启动入口

创建 FastAPI 应用实例，挂载静态文件，注册路由。
提供 main() 作为 CLI 入口，绑定 127.0.0.1:8002 启动 uvicorn。

数据安全: 仅监听本机地址，数据不离开本地文件系统。
"""
import re
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from markupsafe import Markup, escape

from vocabcraft_mcp.tools.quiz import en_to_zh_pos

# web 模块根目录，用于定位 templates 和 static
_WEB_DIR = Path(__file__).parent
_TEMPLATES_DIR = _WEB_DIR / "templates"
_STATIC_DIR = _WEB_DIR / "static"

# 仅放行 <mark> / </mark> 标签；split 保留标签本身，便于对其他片段转义
_MARK_TAG_RE = re.compile(r"(</?mark>)", re.IGNORECASE)


def _safe_mark(value: str) -> Markup:
    """仅放行 <mark> / </mark> 标签，其他 HTML 仍转义。

    实现思路：用正则拆分出 mark 标签与文本片段，对文本片段做 HTML 转义，
    再拼回原始 mark 标签。无需占位符，避免与输入内容碰撞。
    """
    parts = _MARK_TAG_RE.split(str(value))
    escaped = [escape(part) if i % 2 == 0 else part for i, part in enumerate(parts)]
    return Markup("".join(escaped))


# 全局模板实例，供路由模块复用
templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))
templates.env.filters["safe_mark"] = _safe_mark
templates.env.filters["pos_to_zh"] = en_to_zh_pos


def create_app() -> FastAPI:
    """创建 FastAPI 应用实例

    配置 Jinja2 模板引擎、挂载静态文件目录、注册所有路由模块。
    绑定 127.0.0.1 保证仅本机访问，符合数据安全规则。
    """
    app = FastAPI(
        title="VocabCraft 可视化",
        description="词汇学习数据本地可视化应用",
        version="0.3.0",
    )

    # 挂载静态文件（JS库、CSS）
    app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")

    # 根路由：返回单页外壳
    from fastapi import Request
    from fastapi.responses import HTMLResponse

    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request):
        """返回单页外壳 base.html"""
        return templates.TemplateResponse(request, "base.html", {})

    # 注册路由模块
    from vocabcraft_mcp.web.routes import dashboard, stats, review, quiz, vocab, insights

    app.include_router(dashboard.router)
    app.include_router(stats.router)
    app.include_router(review.router)
    app.include_router(quiz.router)
    app.include_router(vocab.router)
    app.include_router(insights.router)

    return app


def main():
    """CLI 入口：启动 uvicorn 服务

    绑定 127.0.0.1:8002，仅本机访问。
    """
    import uvicorn

    uvicorn.run(
        "vocabcraft_mcp.web.app:create_app",
        factory=True,
        host="127.0.0.1",
        port=8002,
        reload=False,
    )


if __name__ == "__main__":
    main()
