#!/bin/bash
# VocabCraft MCP Server 安装脚本
# 适用于 Linux / macOS
#
# 使用方法：
#   chmod +x install.sh
#   ./install.sh
#
# 可选参数：
#   --fix-path       将 .trae/mcp.json 中的 ${workspaceFolder} 替换为绝对路径
#   --agent-runtime  配置 Agent 运行时 (trae/workbuddy/opencode/all)
#
# 前置要求：
#   - Python 3.12+
#   - uv 包管理器 (https://docs.astral.sh/uv/)

set -e

# 解析命令行参数
FIX_PATH=0
AGENT_RUNTIME=""
while [[ $# -gt 0 ]]; do
    case $1 in
        --fix-path)     FIX_PATH=1; shift ;;
        --agent-runtime) AGENT_RUNTIME="$2"; shift 2 ;;
        *)
            echo "未知参数: $1"
            echo "可用参数：--fix-path, --agent-runtime <trae|workbuddy|opencode|all>"
            exit 1
            ;;
    esac
done

echo ""
echo "========================================"
echo "  VocabCraft v0.5.1 安装向导"
echo "  (Trae IDE CN + Trae Work CN + WorkBuddy + opencode)"
echo "========================================"
echo ""

# 获取脚本所在目录（项目根目录）
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ──────────────────────────────────────────
# [1/5] 检查 uv 包管理器
# ──────────────────────────────────────────
echo "[1/5] 检查 uv 包管理器..."
if ! command -v uv &> /dev/null; then
    echo "  ✗ uv 未安装"
    echo ""
    echo "  请先安装 uv："
    echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo "  或访问 https://docs.astral.sh/uv/getting-started/install/"
    exit 1
fi
echo "  ✓ uv 已安装 ($(uv --version))"

# ──────────────────────────────────────────
# [2/5] 检查 Python 版本
# ──────────────────────────────────────────
echo "[2/5] 检查 Python 版本 (>=3.12)..."
if ! command -v python3 &> /dev/null; then
    echo "  ✗ Python 未安装"
    echo ""
    echo "  请先安装 Python 3.12+："
    echo "  https://www.python.org/downloads/"
    exit 1
fi
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)
if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 12 ]); then
    echo "  ✗ Python 版本过低: $PYTHON_VERSION (需要 >= 3.12)"
    echo ""
    echo "  请升级 Python: https://www.python.org/downloads/"
    exit 1
fi
echo "  ✓ Python $PYTHON_VERSION"

# ──────────────────────────────────────────
# [3/5] 安装基础依赖
# ──────────────────────────────────────────
echo "[3/5] 安装基础依赖..."
echo "  图片采集由宿主 LLM 多模态直接解析，无需安装 OCR 引擎。"

cd "$PROJECT_ROOT/vocabcraft-mcp"

echo "  正在安装依赖包..."
if ! uv sync 2>&1; then
    echo "  ✗ 依赖安装失败"
    echo ""
    echo "  请尝试手动安装："
    echo "  cd vocabcraft-mcp"
    echo "  uv sync"
    exit 1
fi
echo "  ✓ 基础依赖安装完成"

# ──────────────────────────────────────────
# [4/5] Agent Runtime 配置
# ──────────────────────────────────────────
if [ -n "$AGENT_RUNTIME" ]; then
    echo ""
    echo "=== Agent Runtime 配置 ==="

    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    SYNC_SCRIPT="$SCRIPT_DIR/scripts/sync-agent-configs.sh"

    case $AGENT_RUNTIME in
        trae)
            echo "Trae 配置说明:"
            echo "  1. 用 Trae 打开项目文件夹"
            echo "  2. 设置 > MCP > 启用「项目级 MCP」"
            echo "  3. 设置 > 规则 > 开启「将 AGENTS.md 包含在上下文中」"
            ;;
        workbuddy)
            echo "正在同步 WorkBuddy 配置..."
            if [ -f "$SYNC_SCRIPT" ]; then
                bash "$SYNC_SCRIPT" --skip-opencode
                echo ""
                echo "下一步:"
                echo "  1. 用 WorkBuddy 打开项目文件夹"
                echo "  2. 在 MCP 配置中信任 vocabcraft-mcp"
            else
                echo "  同步脚本不存在: $SYNC_SCRIPT"
            fi
            ;;
        opencode)
            echo "正在同步 opencode 配置..."
            if [ -f "$SYNC_SCRIPT" ]; then
                bash "$SYNC_SCRIPT" --skip-workbuddy
                echo ""
                echo "下一步:"
                echo "  1. 在项目目录运行 opencode"
                echo "  2. AGENTS.md 将自动加载"
            else
                echo "  同步脚本不存在: $SYNC_SCRIPT"
            fi
            ;;
        all)
            echo "正在同步所有 Agent Runtime 配置..."
            if [ -f "$SYNC_SCRIPT" ]; then
                bash "$SYNC_SCRIPT"
                echo ""
                echo "所有配置已同步。各运行时下一步:"
                echo "  Trae: 设置 > 规则 > 开启「将 AGENTS.md 包含在上下文中」"
                echo "  WorkBuddy: 在 MCP 配置中信任 vocabcraft-mcp"
                echo "  opencode: 在项目目录运行 opencode"
            else
                echo "  同步脚本不存在: $SYNC_SCRIPT"
            fi
            ;;
        *)
            echo "未知 Agent Runtime: $AGENT_RUNTIME"
            echo "支持的值: trae, workbuddy, opencode, all"
            exit 1
            ;;
    esac
fi

# ──────────────────────────────────────────
# [5/5] 验证安装
# ──────────────────────────────────────────
echo "[5/5] 验证安装..."

if uv run python -c "from vocabcraft_mcp.server import main; print('OK')" &> /dev/null; then
    echo "  ✓ MCP Server 入口点可用"
else
    echo "  ⚠ MCP Server 验证跳过（入口点可能需要交互模式）"
fi

# ──────────────────────────────────────────
# mcp.json 路径回退方案（多运行时共用）
# ──────────────────────────────────────────
MCP_JSON_PATH="$PROJECT_ROOT/.trae/mcp.json"
if [ -f "$MCP_JSON_PATH" ]; then
    if grep -q '${workspaceFolder}' "$MCP_JSON_PATH" 2>/dev/null; then
        echo ""
        echo "  ℹ 检测到 mcp.json 使用了 \${workspaceFolder} 变量"
        echo "    Trae / WorkBuddy / opencode 会自动替换此变量，无需手动配置"
        echo "    如果你的环境不支持变量替换，请运行："
        echo "    ./install.sh --fix-path"
    fi
fi

if [ "$FIX_PATH" -eq 1 ]; then
    echo ""
    echo "  正在修复 mcp.json 路径..."
    if [ -f "$MCP_JSON_PATH" ]; then
        ESCAPED_ROOT="${PROJECT_ROOT//\//\\/}"
        sed -i.bak "s/\${workspaceFolder}/$ESCAPED_ROOT/g" "$MCP_JSON_PATH"
        rm -f "$MCP_JSON_PATH.bak"
        echo "  ✓ mcp.json 路径已修复为: $PROJECT_ROOT"
        echo "  ⚠ 注意：修复后配置仅对当前路径有效，移动项目后需重新运行 --fix-path"
        echo "  ⚠ 注意：多运行时可移植性会降低，建议优先升级运行时版本以支持变量"
    else
        echo "  ✗ 未找到 $MCP_JSON_PATH"
    fi
fi

# ──────────────────────────────────────────
# [6/5] 安装 git pre-commit 钩子（配置同步机械防线）
# ──────────────────────────────────────────
echo "[6/5] 安装 git pre-commit 钩子..."
HOOK_SRC="$PROJECT_ROOT/scripts/pre-commit"
HOOK_DST="$PROJECT_ROOT/.git/hooks/pre-commit"
if [ -f "$HOOK_SRC" ]; then
    cp "$HOOK_SRC" "$HOOK_DST"
    chmod +x "$HOOK_DST"
    echo "  ✓ 已安装 pre-commit 钩子（拦截直接修改 .opencode/.workbuddy 的违规提交）"
    echo "    若需手动安装：cp scripts/pre-commit .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit"
else
    echo "  ⚠ 未找到 $HOOK_SRC，跳过钩子安装"
fi

# ──────────────────────────────────────────
# 安装完成提示
# ──────────────────────────────────────────
echo ""
echo "========================================"
echo "  ✓ 安装完成！"
echo "========================================"
echo ""
echo "下一步操作（Trae / WorkBuddy / opencode 操作一致）："
echo ""
echo "  1. 用对应运行时打开此文件夹"
echo "     文件 → 打开文件夹 → 选择: $PROJECT_ROOT"
echo ""
echo "  2. 启用项目级 MCP（Trae: 设置 → MCP；WorkBuddy: 信任 vocabcraft-mcp）"
echo ""
echo "  3. 重启运行时"
echo ""
echo "  4. 开始使用！"
echo "     /capture  - 采集新词汇（宿主 LLM 多模态读图 / 文本）"
echo "     /review   - 复习到期词汇"
echo "     /quiz     - 生成考题并作答"
echo "     /stats    - 查看学习统计"
echo "     /export   - 导出词汇数据"
echo ""
