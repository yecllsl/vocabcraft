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

VERSION="${1:-0.5.1}"

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
mkdir -p "$STAGING_DIR/.trae/skills"
mkdir -p "$STAGING_DIR/vocabcraft-mcp/src"
mkdir -p "$STAGING_DIR/vocabcraft-mcp/tests"
mkdir -p "$STAGING_DIR/vocabcraft-mcp/data/vocabs"
mkdir -p "$STAGING_DIR/vocabcraft-mcp/data/reviews"
mkdir -p "$STAGING_DIR/vocabcraft-mcp/data/quizzes"
mkdir -p "$STAGING_DIR/vocabcraft-mcp/data/exports"
mkdir -p "$STAGING_DIR/vocabcraft-mcp/data/images"
log_ok "directories created"

# ──────────────────────────────────────────
# [3/6] 复制 .trae 配置（白名单，仅 vocabcraft-* 业务文件）
# ──────────────────────────────────────────
log_step "[3/6] Copy .trae config..."

# .trae 顶层文件
[ -f "$PROJECT_ROOT/.trae/hooks.json" ] && \
    cp "$PROJECT_ROOT/.trae/hooks.json" "$STAGING_DIR/.trae/hooks.json"

# 写入发布版 mcp.json（使用 ${workspaceFolder} 变量，解压到任意位置均可工作）
# 多运行时（TRAEWORK CN + TRAEIDE CN）共用此配置
cat > "$STAGING_DIR/.trae/mcp.json" <<'EOF'
{
  "mcpServers": {
    "vocabcraft-mcp": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "${workspaceFolder}/vocabcraft-mcp",
        "vocabcraft-mcp"
      ]
    }
  }
}
EOF

# 辅助函数：复制目录下所有 vocabcraft-* 前缀的文件（非递归）
# 与 BMAD 共存策略：只打包业务文件，不打包 BMAD 文件
copy_vocabcraft_files() {
    local src_dir="$1"
    local dst_dir="$2"
    [ -d "$src_dir" ] || return 0
    for f in "$src_dir"/vocabcraft-*; do
        [ -f "$f" ] || continue
        cp "$f" "$dst_dir/$(basename "$f")"
    done
}

# 辅助函数：复制目录下所有 vocabcraft-* 前缀的子目录（递归，排除 __pycache__）
copy_vocabcraft_dirs() {
    local src_dir="$1"
    local dst_dir="$2"
    [ -d "$src_dir" ] || return 0
    for d in "$src_dir"/vocabcraft-*/; do
        [ -d "$d" ] || continue
        local name="$(basename "$d")"
        local skill_dst="$dst_dir/$name"
        mkdir -p "$skill_dst"
        if command -v rsync >/dev/null 2>&1; then
            rsync -a --exclude='__pycache__' --exclude='.pytest_cache' --exclude='*.pyc' \
                "$d" "$skill_dst/"
        else
            (
                cd "$d"
                find . -type f \
                    ! -path '*/__pycache__/*' \
                    ! -path '*/.pytest_cache/*' \
                    ! -name '*.pyc' -print0
            ) | while IFS= read -r -d '' rel; do
                rel="${rel#./}"
                local dst="$skill_dst/$rel"
                mkdir -p "$(dirname "$dst")"
                cp "$d$rel" "$dst"
            done
        fi
    done
}

# .trae/skills/ 只复制 vocabcraft-* 前缀的 skill 目录
copy_vocabcraft_dirs "$PROJECT_ROOT/.trae/skills" "$STAGING_DIR/.trae/skills"

log_ok ".trae config copied (skills only, rules/agents/commands migrated to AGENTS.md)"

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
for f in install.ps1 install.sh README.md DEPLOY.md QUICKSTART.md LICENSE AGENTS.md; do
    [ -f "$PROJECT_ROOT/$f" ] && cp "$PROJECT_ROOT/$f" "$STAGING_DIR/$f"
done
log_ok "docs copied"

# ──────────────────────────────────────────
# [6/6] 验证关键文件 + 打包
# ──────────────────────────────────────────
log_step "[6/6] Verify and pack..."

# 验证关键文件存在
required=(
    ".trae/mcp.json"
    "vocabcraft-mcp/pyproject.toml"
    "vocabcraft-mcp/src/vocabcraft_mcp/server.py"
    "install.ps1"
    "install.sh"
    "README.md"
)
missing=()
for rf in "${required[@]}"; do
    [ -f "$STAGING_DIR/$rf" ] || missing+=("$rf")
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
echo "  User steps (TRAEWORK CN / TRAEIDE CN 均适用):"
echo "  1. Extract VocabCraft-v$VERSION.{zip|tar.zst|tar.gz}"
echo "  2. Run install.ps1 (or install.sh on Linux/macOS)"
echo "  3. Open folder in Trae, enable project-level MCP"
echo "  4. Repeat step 3 in the other Trae env for dual-env setup"
echo ""
