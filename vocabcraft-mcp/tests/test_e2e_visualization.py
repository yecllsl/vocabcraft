# tests/test_e2e_visualization.py
"""Playwright E2E 测试 — VocabCraft 可视化 Web 应用

测试关键用户流程：页面加载、Tab 切换、图表渲染、复习出题、评分反馈。
"""
import socket
import threading
import time
from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio
from playwright.async_api import Page, async_playwright

# 尝试导入 uvicorn，如不可用则跳过 E2E 测试
try:
    import uvicorn
    HAS_UVICORN = True
except ImportError:
    HAS_UVICORN = False

from vocabcraft_mcp.models import Definition, ReviewState, StructuredVocab, VocabRecord
from vocabcraft_mcp.storage import Storage
from vocabcraft_mcp.tools import crud
from vocabcraft_mcp.web import services


def _find_free_port() -> int:
    """查找可用端口"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _seed_test_data(storage: Storage):
    """填充测试词汇数据"""
    today = datetime.now(UTC).date().isoformat()
    now = datetime.now(UTC)
    languages = ["en", "zh", "de"]

    for i in range(9):
        vocab = VocabRecord(
            id=f"vocab_e2e_{i:03d}",
            created_at=now - timedelta(days=i % 7),
            updated_at=now,
            structured=StructuredVocab(
                word=f"word{i}",
                phonetic="/wɜːd/",
                part_of_speech="n.",
                definitions=[Definition(
                    text=f"释义 {i}",
                    examples=[f"Example sentence for word {i}."],
                )],
                language=languages[i % 3],
            ),
            review_state=ReviewState(
                ease_factor=2.5,
                interval=1 if i % 3 == 0 else 0,
                repetitions=i % 6,
                next_review=today if i % 3 == 0 else "",
            ),
        )
        storage.save_vocab(vocab)


@pytest.fixture(scope="module")
def server_url(tmp_path_factory):
    """启动 FastAPI 服务器并返回 URL"""
    if not HAS_UVICORN:
        pytest.skip("uvicorn 不可用")

    # 创建临时数据目录
    data_dir = tmp_path_factory.mktemp("e2e_data")
    storage = Storage(base_dir=data_dir)
    _seed_test_data(storage)

    # monkeypatch services 与底层 crud 使用同一临时 storage，
    # 保证 generate_web_quiz / grade_quiz 等工具链读到测试数据
    original_get = services._get_storage
    services._get_storage = lambda: storage
    original_default_dir = crud._DEFAULT_DATA_DIR
    crud._DEFAULT_DATA_DIR = data_dir

    # 创建 FastAPI app
    from vocabcraft_mcp.web.app import create_app
    app = create_app()

    port = _find_free_port()
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error")
    server = uvicorn.Server(config)

    # 在后台线程启动服务器
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    # 等待服务器就绪
    url = f"http://127.0.0.1:{port}"
    for _ in range(30):
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                break
        except (TimeoutError, ConnectionRefusedError):
            time.sleep(0.2)

    yield url

    # 清理
    server.should_exit = True
    thread.join(timeout=5)
    services._get_storage = original_get
    crud._DEFAULT_DATA_DIR = original_default_dir


@pytest_asyncio.fixture
async def page(server_url):
    """创建 Playwright 页面"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        pg = await context.new_page()
        yield pg
        await context.close()
        await browser.close()


# 标记整个模块为 e2e 测试
pytestmark = pytest.mark.e2e


@pytest.mark.asyncio
async def test_page_loads(page: Page, server_url: str):
    """页面应正确加载"""
    await page.goto(server_url)
    await page.wait_for_selector(".navbar-brand")
    assert "VocabCraft" in await page.text_content(".navbar-brand")


@pytest.mark.asyncio
async def test_dashboard_loads(page: Page, server_url: str):
    """Dashboard 应加载并显示 KPI 卡片"""
    await page.goto(server_url)
    await page.wait_for_selector(".kpi-grid", timeout=10000)
    cards = await page.query_selector_all(".kpi-card")
    assert len(cards) == 4
    assert "词汇总量" in await cards[0].text_content()


@pytest.mark.asyncio
async def test_tab_switching(page: Page, server_url: str):
    """Tab 切换应加载对应内容"""
    await page.goto(server_url)
    await page.wait_for_selector(".kpi-grid", timeout=10000)

    await page.click('button[data-tab="stats"]')
    await page.wait_for_selector(".dimension-switcher", timeout=10000)

    await page.click('button[data-tab="review"]')
    await page.wait_for_selector(".review-calendar", timeout=10000)

    await page.click('button[data-tab="dashboard"]')
    await page.wait_for_selector(".kpi-grid", timeout=10000)


@pytest.mark.asyncio
async def test_stats_page_charts(page: Page, server_url: str):
    """统计页应显示图表容器"""
    await page.goto(server_url)
    await page.wait_for_selector(".kpi-grid", timeout=10000)

    await page.click('button[data-tab="stats"]')
    await page.wait_for_selector(".chart-grid", timeout=10000)

    charts = await page.query_selector_all(".chart-container")
    assert len(charts) >= 3


@pytest.mark.asyncio
async def test_review_page(page: Page, server_url: str):
    """复习页应显示待复习列表和日历"""
    await page.goto(server_url)
    await page.wait_for_selector(".kpi-grid", timeout=10000)

    await page.click('button[data-tab="review"]')
    await page.wait_for_selector(".review-calendar", timeout=10000)

    calendar_days = await page.query_selector_all(".calendar-day")
    assert len(calendar_days) > 0

    review_items = await page.query_selector_all(".review-item")
    empty_state = await page.query_selector(".review-list .empty-state")
    assert len(review_items) > 0 or empty_state is not None


@pytest.mark.asyncio
async def test_review_quiz_flow(page: Page, server_url: str):
    """复习出题与评分流程"""
    await page.goto(server_url)
    await page.wait_for_selector(".kpi-grid", timeout=10000)

    # 切换到复习 Tab
    await page.click('button[data-tab="review"]')
    await page.wait_for_selector(".review-calendar", timeout=10000)

    # 查找单个词汇的"开始"按钮（避免匹配"开始今日复习"）
    start_btn = await page.query_selector('.review-item button:has-text("开始")')
    if start_btn:
        await start_btn.click()
        # 等待考题渲染
        await page.wait_for_selector(".quiz-container", timeout=10000)
        assert "提交答案" in await page.text_content(".quiz-container")

        # 输入答案并提交
        input_field = await page.query_selector('.quiz-input')
        if input_field:
            await input_field.fill("word0")
            submit_btn = await page.query_selector('button:has-text("提交答案")')
            if submit_btn:
                await submit_btn.click()
                # 等待结果渲染
                await page.wait_for_selector(".quiz-result", timeout=10000)
                result_text = await page.text_content(".quiz-result")
                assert "评分" in result_text


@pytest.mark.asyncio
async def test_vocab_page(page: Page, server_url: str):
    """词汇页应展示列表与筛选"""
    await page.goto(server_url)
    await page.wait_for_selector(".kpi-grid", timeout=10000)

    # 切换到词汇 Tab
    await page.click('button[data-tab="vocab"]')
    await page.wait_for_selector(".vocab-list", timeout=10000)

    cards = await page.query_selector_all(".vocab-card")
    assert len(cards) > 0


@pytest.mark.asyncio
async def test_vocab_quiz_from_list(page: Page, server_url: str):
    """从词汇列表出题"""
    await page.goto(server_url)
    await page.wait_for_selector(".kpi-grid", timeout=10000)

    await page.click('button[data-tab="vocab"]')
    await page.wait_for_selector(".vocab-list", timeout=10000)

    # 点击第一个卡片的"出题"按钮
    quiz_btn = await page.query_selector('.vocab-card-actions button:has-text("出题")')
    assert quiz_btn is not None
    await quiz_btn.click()
    await page.wait_for_selector(".quiz-container", timeout=10000)
    assert "提交答案" in await page.text_content(".quiz-container")


@pytest.mark.asyncio
async def test_vocab_edit_flow(page: Page, server_url: str):
    """编辑词汇并保存"""
    await page.goto(server_url)
    await page.wait_for_selector(".kpi-grid", timeout=10000)

    await page.click('button[data-tab="vocab"]')
    await page.wait_for_selector(".vocab-list", timeout=10000)

    # 点击第一个卡片的"编辑"按钮
    edit_btn = await page.query_selector('.vocab-card-actions button:has-text("编辑")')
    assert edit_btn is not None
    await edit_btn.click()
    await page.wait_for_selector("form", timeout=10000)

    # 修改词形
    await page.fill('input[name="word"]', "word0-edited")
    # 修改语言为德语
    await page.select_option('select[name="language"]', "de")

    # 保存
    save_btn = await page.query_selector('button[type="submit"]')
    assert save_btn is not None
    await save_btn.click()

    # 等待详情页
    await page.wait_for_selector(".vocab-detail", timeout=10000)
    detail_text = await page.text_content(".vocab-detail")
    assert "word0-edited" in detail_text
    assert "de" in detail_text


@pytest.mark.asyncio
async def test_batch_review_flow(page: Page, server_url: str):
    """批量复习：今日到期词汇连续出题并完成汇总"""
    await page.goto(server_url)
    await page.wait_for_selector(".kpi-grid", timeout=10000)

    # 切换到复习 Tab
    await page.click('button[data-tab="review"]')
    await page.wait_for_selector(".review-calendar", timeout=10000)

    # 点击"开始今日复习"
    start_btn = await page.query_selector('button:has-text("开始今日复习")')
    assert start_btn is not None
    await start_btn.click()
    await page.wait_for_selector(".batch-review", timeout=10000)
    assert "今日批量复习" in await page.text_content(".batch-review")

    # 获取总题数
    batch_text = await page.text_content(".batch-review-meta")
    assert "共" in batch_text

    # 循环答题直到汇总页出现；测试数据最多 3 题，设置安全上限
    for _ in range(5):
        batch_item = await page.query_selector(".batch-item")
        if batch_item is None:
            break

        input_field = await page.query_selector('.batch-item .quiz-input')
        if input_field is None:
            break
        await input_field.fill("answer")

        submit_btn = await page.query_selector('.batch-item button[type="submit"]')
        assert submit_btn is not None
        await submit_btn.click()
        # 给 HTMX 短暂时间完成交换
        await page.wait_for_timeout(200)

    # 最终应显示汇总页
    await page.wait_for_selector(".batch-review .chart-title", timeout=10000)
    summary_text = await page.text_content(".batch-review")
    assert "复习完成" in summary_text
    assert "完成题数" in summary_text


@pytest.mark.asyncio
async def test_insights_page_render_and_switch(page: Page, server_url: str):
    """E2E: /insights 页面渲染 + 语种切换 + 遗忘曲线图表容器可见

    N-05 验收：通过 SPA 导航访问 /insights（HTMX 加载到 #content），
    验证 de（默认）渲染 KPI 卡片与遗忘曲线图表容器，
    再切换到 zh_classical（测试数据为空）触发空状态，
    确认 HTMX 局部交换工作正常。
    """
    # 1. 加载 base.html 外壳（含 htmx.js / echarts.js / 导航栏 / #content）
    await page.goto(server_url)
    await page.wait_for_selector(".navbar-tab", timeout=10000)

    # 2. 点击"语种洞察"导航 tab（HTMX 将 /insights 加载到 #content）
    await page.click('button[data-tab="insights"]')

    # 3. 验证 de 默认语种内容渲染：KPI"总数"卡片 + 遗忘曲线图表容器
    #    de 测试数据 3 词 → total > 0 → chart-grid 渲染
    await page.wait_for_selector("text=总数", timeout=10000)
    await page.wait_for_selector("[data-echart='renderForgettingCurve']", timeout=10000)

    # 4. 点击"文言文"切换语种（HTMX 触发 /partials/insights?language=zh_classical）
    #    用 predicate 形式匹配响应 URL（字符串形式对含 query string 的 URL 匹配不稳定）
    async with page.expect_response(
        lambda r: "/partials/insights" in r.url and "zh_classical" in r.url
    ):
        await page.click('.language-switcher button:has-text("文言文")')

    # 5. 验证切换成功：zh_classical 测试数据为 0 → 显示空状态
    #    空状态仅在 total==0 时渲染，是切换生效的强证据
    await page.wait_for_selector("text=该语种暂无词汇", timeout=10000)
    # 标题仍存在（确认 HTMX outerHTML 替换 #insights-body 成功）
    await page.wait_for_selector("h2:has-text('语种洞察')")
