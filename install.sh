#!/bin/bash
# VocabCraft MCP Server 安装脚本
# 适用于 Linux / macOS
#
# 使用方法：
#   chmod +x install.sh
#   ./install.sh
#
# 可选参数：
#   --install-ocr    直接安装 OCR 依赖（跳过询问）
#   --fix-path       将 .trae/mcp.json 中的 ${workspaceFolder} 替换为绝对路径
#
# 前置要求：
#   - Python 3.12+
#   - uv 包管理器 (https://docs.astral.sh/uv/)

set -e

# 解析命令行参数
INSTALL_OCR=0
FIX_PATH=0
for arg in "$@"; do
    case "$arg" in
        --install-ocr) INSTALL_OCR=1 ;;
        --fix-path)    FIX_PATH=1 ;;
        *)
            echo "未知参数: $arg"
            echo "可用参数：--install-ocr, --fix-path"
            exit 1
            ;;
    esac
done

echo ""
echo "========================================"
echo "  VocabCraft v0.3.0 安装向导"
echo "  (TRAEWORK CN + TRAEIDE CN 双环境)"
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
echo "  基础依赖不含 OCR 引擎（paddleocr/paddlepaddle 体积大，已拆为可选）"

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
# [4/5] 询问并安装可选 OCR 依赖
# ──────────────────────────────────────────
echo "[4/5] 是否安装 OCR 可选依赖？"
echo "  OCR 用于图片词汇识别，paddleocr+paddlepaddle 约 1.5GB，安装较慢。"
echo "  仅当需要 /capture 拍照录入词汇时才需要。"

SHOULD_INSTALL_OCR=0
if [ "$INSTALL_OCR" -eq 1 ]; then
    # 命令行参数 --install-ocr 直接安装，不询问
    SHOULD_INSTALL_OCR=1
    echo "  ℹ 检测到 --install-ocr 参数，直接安装"
else
    read -p "  安装 OCR 依赖？[y/N] " INSTALL_OCR_INPUT
    if [[ "$INSTALL_OCR_INPUT" =~ ^[Yy]$ ]]; then
        SHOULD_INSTALL_OCR=1
    fi
fi

if [ "$SHOULD_INSTALL_OCR" -eq 1 ]; then
    echo "  正在安装 OCR 依赖..."
    if uv sync --extra ocr 2>&1; then
        echo "  ✓ OCR 依赖安装完成"
    else
        echo "  ✗ OCR 依赖安装失败，可稍后手动重试：uv sync --extra ocr"
    fi
else
    echo "  ⊘ 已跳过 OCR 依赖。后续需要时执行：cd vocabcraft-mcp && uv sync --extra ocr"
fi

# ──────────────────────────────────────────
# [5/5] 验证安装
# ──────────────────────────────────────────
echo "[5/5] 验证安装..."

# 验证 MCP Server 入口点可用
if uv run vocabcraft-mcp --help &> /dev/null; then
    echo "  ✓ MCP Server 入口点可用"
else
    echo "  ⚠ MCP Server 验证跳过（入口点可能需要交互模式）"
fi

# ──────────────────────────────────────────
# mcp.json 路径回退方案（双环境共用）
# ──────────────────────────────────────────
MCP_JSON_PATH="$PROJECT_ROOT/.trae/mcp.json"
if [ -f "$MCP_JSON_PATH" ]; then
    if grep -q '${workspaceFolder}' "$MCP_JSON_PATH" 2>/dev/null; then
        echo ""
        echo "  ℹ 检测到 mcp.json 使用了 \${workspaceFolder} 变量"
        echo "    TRAEWORK CN 与 TRAEIDE CN 会自动替换此变量，无需手动配置"
        echo "    如果你的 Trae 版本不支持变量替换，请运行："
        echo "    ./install.sh --fix-path"
    fi
fi

# 处理 --fix-path 参数：将 ${workspaceFolder} 替换为实际路径
if [ "$FIX_PATH" -eq 1 ]; then
    echo ""
    echo "  正在修复 mcp.json 路径..."
    if [ -f "$MCP_JSON_PATH" ]; then
        # 路径中的 / 转义为 \/ 以适配 sed
        ESCAPED_ROOT="${PROJECT_ROOT//\//\\/}"
        sed -i.bak "s/\${workspaceFolder}/$ESCAPED_ROOT/g" "$MCP_JSON_PATH"
        rm -f "$MCP_JSON_PATH.bak"
        echo "  ✓ mcp.json 路径已修复为: $PROJECT_ROOT"
        echo "  ⚠ 注意：修复后配置仅对当前路径有效，移动项目后需重新运行 --fix-path"
        echo "  ⚠ 注意：双环境可移植性会降低，建议优先升级 Trae 版本以支持变量"
    else
        echo "  ✗ 未找到 $MCP_JSON_PATH"
    fi
fi

# ──────────────────────────────────────────
# 安装完成提示
# ──────────────────────────────────────────
echo ""
echo "========================================"
echo "  ✓ 安装完成！"
echo "========================================"
echo ""
echo "下一步操作（TRAEWORK CN 与 TRAEIDE CN 操作一致）："
echo ""
echo "  1. 用 Trae IDE 打开此文件夹"
echo "     文件 → 打开文件夹 → 选择: $PROJECT_ROOT"
echo ""
echo "  2. 启用项目级 MCP"
echo "     设置 → MCP → 打开'启用项目级 MCP'开关"
echo ""
echo "  3. 重启 Trae"
echo ""
echo "  4. 在另一个环境（TRAEWORK / TRAEIDE）重复步骤 1-3 即可双环境共用"
echo ""
echo "  5. 开始使用！"
echo "     /capture  - 采集新词汇"
echo "     /review   - 复习到期词汇"
echo "     /quiz     - 生成考题并作答"
echo "     /stats    - 查看学习统计"
echo "     /export   - 导出词汇数据"
echo ""
