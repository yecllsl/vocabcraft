# src/vocabcraft_mcp/web/app.py
"""FastAPI 应用工厂与启动入口

创建 FastAPI 应用实例，挂载静态文件，注册路由。
提供 main() 作为 CLI 入口，启动 uvicorn。

绑定地址通过 VOCABCRAFT_WEB_HOST 配置（默认 0.0.0.0，允许局域网访问）；
如需仅本机访问可设 VOCABCRAFT_WEB_HOST=127.0.0.1。
数据始终仅存储于本地文件系统，不离开本机。
"""
import os
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
    return Markup("".join(escaped))  # noqa: B704  # 输入已逐片段 escape，仅放行 <mark> 标签


# 全局模板实例，供路由模块复用
templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))
templates.env.filters["safe_mark"] = _safe_mark
templates.env.filters["pos_to_zh"] = en_to_zh_pos


def create_app() -> FastAPI:
    """创建 FastAPI 应用实例

    配置 Jinja2 模板引擎、挂载静态文件目录、注册所有路由模块。
    实际监听地址由 main() 中的 VOCABCRAFT_WEB_HOST 决定（默认 0.0.0.0）。
    """
    app = FastAPI(
        title="VocabCraft 可视化",
        description="词汇学习数据本地可视化应用",
        version="0.6.2",
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
    from vocabcraft_mcp.web.routes import dashboard, insights, quiz, review, stats, vocab

    app.include_router(dashboard.router)
    app.include_router(stats.router)
    app.include_router(review.router)
    app.include_router(quiz.router)
    app.include_router(vocab.router)
    app.include_router(insights.router)

    return app


def main():
    """CLI 入口：启动 uvicorn 服务

    绑定地址由 VOCABCRAFT_WEB_HOST 控制，默认 0.0.0.0（允许局域网访问）；
    端口由 VOCABCRAFT_WEB_PORT 控制，默认 8002。
    """
    import uvicorn

    host = os.environ.get("VOCABCRAFT_WEB_HOST", "0.0.0.0")  # nosec B104  # 本地工具，绑定地址可由环境变量覆盖，非公网暴露
    port = int(os.environ.get("VOCABCRAFT_WEB_PORT", "8002"))

    uvicorn.run(
        "vocabcraft_mcp.web.app:create_app",
        factory=True,
        host=host,
        port=port,
        reload=False,
    )


if __name__ == "__main__":
    main()
