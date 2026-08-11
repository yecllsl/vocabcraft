#!/usr/bin/env bash
# VocabCraft 发布包构建脚本（bash 版）
# 与 scripts/build-release.ps1 逻辑对齐，供 GitHub Actions 和 Linux/macOS 用户使用
#
# 使用方法：
#   ./scripts/build-release.sh [VERSION]
#
# 输出：
#   dist/VocabCraft-v${VERSION}.zip
#   dist/VocabCraft-v${VERSION}.tar.zst
#   dist/VocabCraft-v${VERSION}.tar.gz

set -euo pipefail

VERSION="${1:-0.5.4}"

# ──────────────────────────────────────────
# 路径定义
# ──────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DIST_DIR="$PROJECT_ROOT/dist"
PACKAGE_NAME="VocabCraft-v$VERSION"
STAGING_DIR="$DIST_DIR/$PACKAGE_NAME"
ZIP_PATH="$DIST_DIR/$PACKAGE_NAME.zip"
ZST_PATH="$DIST_DIR/$PACKAGE_NAME.tar.zst"
GZ_PATH="$DIST_DIR/$PACKAGE_NAME.tar.gz"

# 基线运行时平台（AAIF 4 运行时：Trae IDE CN / Trae Work CN / CodeBuddy / OpenCode / Goose）
# .agents/ 为 AAIF 真相源：Skills 与 AGENTS.md 同步自 .agents/，平台配置生成自 .agents/runtime/*.json
PYTHON_BIN="$(command -v python3 || command -v python || echo python3)"
AGENTS_DIR="$PROJECT_ROOT/.agents"
AGENTS_RUNTIME="$AGENTS_DIR/runtime"
AGENTS_SKILLS="$AGENTS_DIR/skills"
AGENTS_MD="$AGENTS_DIR/AGENTS.md"
declare -A CFG_SRC=( [trae]=trae.json [opencode]=opencode.json [codebuddy]=codebuddy.json [goose]=goose.json )
declare -A CFG_DST=( [trae]=mcp.json [opencode]=opencode.json [codebuddy]=mcp.json [goose]=config.yaml )
declare -A AGENTS_IN_PLATFORM=( [trae]=0 [opencode]=1 [codebuddy]=1 [goose]=1 )
PLATFORMS=( trae opencode codebuddy goose )

# ──────────────────────────────────────────
# 颜色输出（与 PowerShell 版风格一致）
# ──────────────────────────────────────────
if [ -t 1 ]; then
    GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; CYAN='\033[0;36m'; NC='\033[0m'
else
    GREEN=''; YELLOW=''; RED=''; CYAN=''; NC=''
fi
log_step() { echo -e "${YELLOW}[build]${NC} $1"; }
log_ok()   { echo -e "${GREEN}[ok]${NC}    $1"; }
log_err()  { echo -e "${RED}[err]${NC}   $1" >&2; }

echo ""
echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}  VocabCraft v$VERSION release build${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

# ──────────────────────────────────────────
# [1/6] 清理旧构建
# ──────────────────────────────────────────
log_step "[1/6] Clean previous build..."
rm -rf "$DIST_DIR"
mkdir -p "$DIST_DIR"
log_ok "cleaned"

# ──────────────────────────────────────────
# [2/6] 创建目标目录结构
# ──────────────────────────────────────────
log_step "[2/6] Create directory structure..."
mkdir -p "$STAGING_DIR/.agents"
for p in "${PLATFORMS[@]}"; do
    mkdir -p "$STAGING_DIR/$p/skills"
done
mkdir -p "$STAGING_DIR/vocabcraft-mcp/src"
mkdir -p "$STAGING_DIR/vocabcraft-mcp/tests"
mkdir -p "$STAGING_DIR/vocabcraft-mcp/data/vocabs"
mkdir -p "$STAGING_DIR/vocabcraft-mcp/data/reviews"
mkdir -p "$STAGING_DIR/vocabcraft-mcp/data/quizzes"
mkdir -p "$STAGING_DIR/vocabcraft-mcp/data/exports"
mkdir -p "$STAGING_DIR/vocabcraft-mcp/data/images"
log_ok "directories created"

# ──────────────────────────────────────────
# [3/6] 复制 AAIF 多平台配置（.trae / .opencode / .codebuddy / .goose）
# ──────────────────────────────────────────
log_step "[3/6] Copy AAIF platform configs (.trae/.opencode/.codebuddy/.goose)..."

# opencode 的 instructions 引用 .agents/AGENTS.md，发布包需包含该文件
cp "$AGENTS_MD" "$STAGING_DIR/.agents/AGENTS.md"

# 辅助函数：递归复制一个目录（排除 __pycache__ / .pytest_cache / *.pyc）
copy_dir_filtered() {
    local src_dir="$1" dst_dir="$2"
    [ -d "$src_dir" ] || return 0
    mkdir -p "$dst_dir"
    if command -v rsync >/dev/null 2>&1; then
        rsync -a --exclude='__pycache__' --exclude='.pytest_cache' --exclude='*.pyc' \
            "$src_dir/" "$dst_dir/"
    else
        (
            cd "$src_dir"
            find . -type f \
                ! -path '*/__pycache__/*' \
                ! -path '*/.pytest_cache/*' \
                ! -name '*.pyc' -print0
        ) | while IFS= read -r -d '' rel; do
            rel="${rel#./}"
            dst="$dst_dir/$rel"
            mkdir -p "$(dirname "$dst")"
            cp "$src_dir/$rel" "$dst"
        done
    fi
}

for p in "${PLATFORMS[@]}"; do
    pd="$STAGING_DIR/$p"
    mkdir -p "$pd/skills"
    # Skills：整目录同步（与 sync-agent-configs 一致，不再做 vocabcraft-* 前缀过滤）
    copy_dir_filtered "$AGENTS_SKILLS" "$pd/skills"
    # AGENTS.md（Trae 放根目录，其余平台放进各自目录）
    if [ "${AGENTS_IN_PLATFORM[$p]}" = "1" ]; then
        cp "$AGENTS_MD" "$pd/AGENTS.md"
    fi
    # 平台配置：来自 AAIF 运行时真相源 .agents/runtime/<ConfigSrc>
    if [ "${CFG_DST[$p]}" = "config.yaml" ]; then
        "$PYTHON_BIN" "$SCRIPT_DIR/generate-goose-config.py" \
            --runtime-json "$AGENTS_RUNTIME/${CFG_SRC[$p]}" \
            --out-dir "$pd" --no-resolve-dir
    else
        cp "$AGENTS_RUNTIME/${CFG_SRC[$p]}" "$pd/${CFG_DST[$p]}"
    fi
done

log_ok "AAIF platform configs copied (.trae/.opencode/.codebuddy/.goose)"

# ──────────────────────────────────────────
# [4/6] 复制 vocabcraft-mcp 源码（白名单）
# ──────────────────────────────────────────
log_step "[4/6] Copy vocabcraft-mcp source..."

MCP_SRC="$PROJECT_ROOT/vocabcraft-mcp"
MCP_DST="$STAGING_DIR/vocabcraft-mcp"

# 4a. 顶层文件
for f in pyproject.toml uv.lock .python-version; do
    [ -f "$MCP_SRC/$f" ] && cp "$MCP_SRC/$f" "$MCP_DST/$f"
done

# 4b. src/ 递归复制（排除 __pycache__、.pytest_cache、*.pyc）
# 优先用 rsync；不可用时用 find + cp 兜底
if command -v rsync >/dev/null 2>&1; then
    rsync -a --exclude='__pycache__' --exclude='.pytest_cache' --exclude='*.pyc' \
        "$MCP_SRC/src/" "$MCP_DST/src/"
else
    mkdir -p "$MCP_DST/src"
    (
        cd "$MCP_SRC/src"
        find . -type f \
            ! -path '*/__pycache__/*' \
            ! -path '*/.pytest_cache/*' \
            ! -name '*.pyc' -print0
    ) | while IFS= read -r -d '' rel; do
        rel="${rel#./}"
        dst="$MCP_DST/src/$rel"
        mkdir -p "$(dirname "$dst")"
        cp "$MCP_SRC/src/$rel" "$dst"
    done
fi

# 4c. tests/ 递归复制（排除 __pycache__、.pytest_cache）
if [ -d "$MCP_SRC/tests" ]; then
    if command -v rsync >/dev/null 2>&1; then
        rsync -a --exclude='__pycache__' --exclude='.pytest_cache' --exclude='*.pyc' \
            "$MCP_SRC/tests/" "$MCP_DST/tests/"
    else
        (
            cd "$MCP_SRC/tests"
            find . -type f \
                ! -path '*/__pycache__/*' \
                ! -path '*/.pytest_cache/*' \
                ! -name '*.pyc' -print0
        ) | while IFS= read -r -d '' rel; do
            rel="${rel#./}"
            dst="$MCP_DST/tests/$rel"
            mkdir -p "$(dirname "$dst")"
            cp "$MCP_SRC/tests/$rel" "$dst"
        done
    fi
fi

# 4d. data/ 创建 .gitkeep 占位（不复制用户数据）
for sub in vocabs reviews quizzes exports images; do
    touch "$MCP_DST/data/$sub/.gitkeep"
done
log_ok "source copied"

# ──────────────────────────────────────────
# [5/6] 复制顶层文档和安装脚本
# ──────────────────────────────────────────
log_step "[5/6] Copy docs and install scripts..."
for f in install.ps1 install.sh README.md DEPLOY.md QUICKSTART.md LICENSE AGENTS.md .workbuddy/README.md .hermes/README.md; do
    # AGENTS.md 的真相源是 .agents/AGENTS.md（同步生成根目录 AGENTS.md）
    src_f="$PROJECT_ROOT/$f"
    [ "$f" = "AGENTS.md" ] && src_f="$PROJECT_ROOT/.agents/AGENTS.md"
    if [ -f "$src_f" ]; then
        mkdir -p "$(dirname "$STAGING_DIR/$f")"
        cp "$src_f" "$STAGING_DIR/$f"
    fi
done
log_ok "docs copied"

# ──────────────────────────────────────────
# [6/6] 验证关键文件 + 打包
# ──────────────────────────────────────────
log_step "[6/6] Verify and pack..."

# 验证关键文件存在（四个平台配置均来自 AAIF 真相源，需全部齐备）
required=(
    "AGENTS.md"
    ".agents/AGENTS.md"
    ".trae/mcp.json"
    ".opencode/opencode.json"
    ".codebuddy/mcp.json"
    ".goose/config.yaml"
    ".trae/skills"
    ".opencode/skills"
    ".codebuddy/skills"
    ".goose/skills"
    "vocabcraft-mcp/pyproject.toml"
    "vocabcraft-mcp/src/vocabcraft_mcp/server.py"
    "install.ps1"
    "install.sh"
    "README.md"
)
missing=()
for rf in "${required[@]}"; do
    [ -e "$STAGING_DIR/$rf" ] || missing+=("$rf")
done
if [ ${#missing[@]} -gt 0 ]; then
    log_err "Missing required files:"
    for m in "${missing[@]}"; do log_err "  $m"; done
    exit 1
fi

# 验证没有误包含 .venv
if [ -d "$STAGING_DIR/vocabcraft-mcp/.venv" ]; then
    log_err ".venv was accidentally included! Aborting."
    exit 1
fi

file_count=$(find "$STAGING_DIR" -type f | wc -l)
log_ok "verified ($file_count files, no .venv)"

# 打包为 zip（与 PowerShell 版产物一致）
log_step "Packing zip..."
if ! command -v zip >/dev/null 2>&1; then
    log_err "zip not found."
    log_err "  Linux/Debian: apt-get install -y zip"
    log_err "  macOS:        brew install zip"
    log_err "  Windows:      use scripts/build-release.ps1 (uses Compress-Archive)"
    exit 1
fi
(cd "$DIST_DIR" && zip -qr "$ZIP_PATH" "$PACKAGE_NAME")

# 打包为 tar.zst（现代 Linux/macOS 推荐，体积最小、速度最快）
log_step "Packing tar.zst..."
if ! command -v zstd >/dev/null 2>&1; then
    log_err "zstd not found."
    log_err "  Linux/Debian: apt-get install -y zstd"
    log_err "  macOS:        brew install zstd"
    exit 1
fi
tar -C "$DIST_DIR" -cf - --exclude='__pycache__' --exclude='.pytest_cache' --exclude='*.pyc' \
    "$PACKAGE_NAME" | zstd -3 -q -o "$ZST_PATH"

# 打包为 tar.gz（兼容性最好）
log_step "Packing tar.gz..."
if ! command -v gzip >/dev/null 2>&1; then
    log_err "gzip not found."
    exit 1
fi
tar -C "$DIST_DIR" -czf "$GZ_PATH" "$PACKAGE_NAME"

# 清理临时目录
rm -rf "$STAGING_DIR"

# 报告
echo ""
log_ok "packed:"
for f in "$ZIP_PATH" "$ZST_PATH" "$GZ_PATH"; do
    size=$(du -h "$f" | cut -f1)
    echo -e "  ${CYAN}$f${NC} ($size)"
done

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Build complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "  Package: ${CYAN}$PACKAGE_NAME${NC}"
echo -e "  Files:   ${CYAN}$file_count${NC}"
echo ""
echo "  User steps (支持的运行时: Trae IDE CN / Trae Work CN / CodeBuddy / OpenCode / Goose):"
echo "  1. Extract VocabCraft-v$VERSION.{zip|tar.zst|tar.gz}"
echo "  2. Run install.ps1 (或 Linux/macOS 下 install.sh)"
echo "  3. 在所用 IDE 中打开该文件夹，启用项目级 MCP 即可"
echo ""
