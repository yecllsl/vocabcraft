#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

TRAE_SKILLS="$PROJECT_ROOT/.trae/skills"
TRAE_MCP="$PROJECT_ROOT/.trae/mcp.json"
AGENTS_MD="$PROJECT_ROOT/AGENTS.md"

[ -d "$TRAE_SKILLS" ] || { echo "错误: 源目录不存在: $TRAE_SKILLS"; exit 1; }
[ -f "$TRAE_MCP" ] || { echo "错误: MCP 配置不存在: $TRAE_MCP"; exit 1; }
[ -f "$AGENTS_MD" ] || { echo "错误: AGENTS.md 不存在: $AGENTS_MD"; exit 1; }

echo "=== VocabCraft Agent Config Sync ==="
echo "项目根目录: $PROJECT_ROOT"

SKIP_OPENCODE=false
SKIP_WORKBUDDY=false
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-opencode) SKIP_OPENCODE=true; shift ;;
        --skip-workbuddy) SKIP_WORKBUDDY=true; shift ;;
        *) echo "未知参数: $1"; exit 1 ;;
    esac
done

sync_skills() {
    local target_dir="$1"
    local target_skills="$target_dir/skills"
    rm -rf "$target_skills"
    echo "同步 Skills → $target_skills"
    cp -r "$TRAE_SKILLS" "$target_skills"
    local skill_count
    skill_count=$(find "$target_skills" -mindepth 1 -maxdepth 1 -type d | wc -l)
    echo "  已同步 $skill_count 个 Skills"
}

generate_opencode_config() {
    local opencode_dir="$PROJECT_ROOT/.opencode"
    mkdir -p "$opencode_dir"
    python3 -c "
import json
with open('$TRAE_MCP') as f:
    trae_mcp = json.load(f)
config = {'\$schema': 'https://opencode.ai/config.json', 'mcp': {}, 'instructions': ['AGENTS.md']}
for name, server in trae_mcp.get('mcpServers', {}).items():
    config['mcp'][name] = {'type': 'local', 'command': [server['command']] + server.get('args', [])}
with open('$opencode_dir/opencode.json', 'w', encoding='utf-8') as f:
    json.dump(config, f, indent=2, ensure_ascii=False)
"
    echo "已生成 opencode 配置"
}

generate_workbuddy_mcp() {
    local workbuddy_dir="$PROJECT_ROOT/.workbuddy"
    mkdir -p "$workbuddy_dir"
    python3 -c "
import json, os
project_root = '$PROJECT_ROOT'
uv_path = 'uv'
for p in [os.path.expanduser('~/.local/bin/uv'), '/usr/local/bin/uv']:
    if os.path.isfile(p):
        uv_path = p; break
with open('$TRAE_MCP') as f:
    trae_mcp = json.load(f)
mcp = {'mcpServers': {}}
for name, server in trae_mcp.get('mcpServers', {}).items():
    args = [a.replace('\${workspaceFolder}', project_root.replace(chr(92), '/')) for a in server.get('args', [])]
    mcp['mcpServers'][name] = {'command': uv_path, 'args': args}
with open('$workbuddy_dir/mcp.json', 'w', encoding='utf-8') as f:
    json.dump(mcp, f, indent=2, ensure_ascii=False)
"
    echo "已生成 WorkBuddy MCP 配置"
}

if [ "$SKIP_OPENCODE" = false ]; then
    echo ""; echo "--- opencode ---"
    sync_skills "$PROJECT_ROOT/.opencode"
    generate_opencode_config
fi
if [ "$SKIP_WORKBUDDY" = false ]; then
    echo ""; echo "--- WorkBuddy ---"
    sync_skills "$PROJECT_ROOT/.workbuddy"
    generate_workbuddy_mcp
fi
echo ""; echo "=== 同步完成 ==="