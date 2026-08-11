#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

AGENTS_DIR="$PROJECT_ROOT/.agents"
AGENTS_RUNTIME="$AGENTS_DIR/runtime"
AGENTS_SKILLS="$AGENTS_DIR/skills"
AGENTS_MD="$AGENTS_DIR/AGENTS.md"

export PROJECT_ROOT AGENTS_RUNTIME

[ -d "$AGENTS_RUNTIME" ] || { echo "错误: AAIF 运行时配置目录不存在: $AGENTS_RUNTIME"; exit 1; }
[ -d "$AGENTS_SKILLS" ] || { echo "错误: AAIF 技能目录不存在: $AGENTS_SKILLS"; exit 1; }
[ -f "$AGENTS_MD" ] || { echo "错误: AGENTS.md 不存在: $AGENTS_MD"; exit 1; }

# ──────────────────────────────────────────
# 颜色输出（与 PowerShell 版风格一致）
# ──────────────────────────────────────────
if [ -t 1 ]; then
    GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
else
    GREEN=''; YELLOW=''; CYAN=''; NC=''
fi

echo -e "${CYAN}=== VocabCraft AAIF Config Sync ===${NC}"
echo "项目根目录: $PROJECT_ROOT"
echo "配置源: .agents/ (AAIF 标准)"

SKIP_TRAE=false
SKIP_OPENCODE=false
SKIP_WORKBUDDY=false
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-trae) SKIP_TRAE=true; shift ;;
        --skip-opencode) SKIP_OPENCODE=true; shift ;;
        --skip-workbuddy) SKIP_WORKBUDDY=true; shift ;;
        *) echo "未知参数: $1"; exit 1 ;;
    esac
done

sync_skills() {
    local target_dir="$1"
    local target_skills="$target_dir/skills"
    rm -rf "$target_skills"
    echo -e "${YELLOW}同步 Skills → $target_skills${NC}"
    cp -r "$AGENTS_SKILLS" "$target_skills"
    local skill_count
    skill_count=$(find "$target_skills" -mindepth 1 -maxdepth 1 -type d | wc -l)
    echo -e "${GREEN}  已同步 $skill_count 个 Skills${NC}"
}

sync_agents_md() {
    local target_dir="$1"
    local target_agents_md="$target_dir/AGENTS.md"
    echo -e "${YELLOW}同步 AGENTS.md → $target_agents_md${NC}"
    cp -f "$AGENTS_MD" "$target_agents_md"
    echo -e "${GREEN}  已同步 AGENTS.md${NC}"
}

generate_trae_config() {
    local trae_dir="$PROJECT_ROOT/.trae"
    mkdir -p "$trae_dir"
    local source_config="$AGENTS_RUNTIME/trae.json"
    if [ -f "$source_config" ]; then
        echo -e "${YELLOW}复制 Trae 配置 → $trae_dir${NC}"
        cp -f "$source_config" "$trae_dir/mcp.json"
        echo -e "${GREEN}  已生成 Trae 配置${NC}"
    fi
}

generate_opencode_config() {
    local opencode_dir="$PROJECT_ROOT/.opencode"
    mkdir -p "$opencode_dir"
    local source_config="$AGENTS_RUNTIME/opencode.json"
    if [ -f "$source_config" ]; then
        echo -e "${YELLOW}复制 opencode 配置 → $opencode_dir${NC}"
        cp -f "$source_config" "$opencode_dir/opencode.json"
        echo -e "${GREEN}  已生成 opencode 配置${NC}"
    fi
}

generate_workbuddy_config() {
    local workbuddy_dir="$PROJECT_ROOT/.workbuddy"
    mkdir -p "$workbuddy_dir"
    local source_config="$AGENTS_RUNTIME/workbuddy.json"
    if [ -f "$source_config" ]; then
        echo -e "${YELLOW}复制 WorkBuddy 配置 → $workbuddy_dir${NC}"
        cp -f "$source_config" "$workbuddy_dir/mcp.json"
        echo -e "${GREEN}  已生成 WorkBuddy 配置${NC}"
    fi
}

if [ "$SKIP_TRAE" = false ]; then
    echo -e "\n${CYAN}--- Trae ---${NC}"
    sync_skills "$PROJECT_ROOT/.trae"
    sync_agents_md "$PROJECT_ROOT"
    generate_trae_config
fi
if [ "$SKIP_OPENCODE" = false ]; then
    echo -e "\n${CYAN}--- opencode ---${NC}"
    sync_skills "$PROJECT_ROOT/.opencode"
    sync_agents_md "$PROJECT_ROOT/.opencode"
    generate_opencode_config
fi
if [ "$SKIP_WORKBUDDY" = false ]; then
    echo -e "\n${CYAN}--- WorkBuddy ---${NC}"
    sync_skills "$PROJECT_ROOT/.workbuddy"
    sync_agents_md "$PROJECT_ROOT/.workbuddy"
    generate_workbuddy_config
fi
echo -e "\n${CYAN}=== 同步完成 ===${NC}"
