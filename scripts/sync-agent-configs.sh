#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

TRAE_SKILLS="$PROJECT_ROOT/.trae/skills"
TRAE_MCP="$PROJECT_ROOT/.trae/mcp.json"
AGENTS_MD="$PROJECT_ROOT/AGENTS.md"

export PROJECT_ROOT TRAE_MCP

[ -d "$TRAE_SKILLS" ] || { echo "错误: 源目录不存在: $TRAE_SKILLS"; exit 1; }
[ -f "$TRAE_MCP" ] || { echo "错误: MCP 配置不存在: $TRAE_MCP"; exit 1; }
[ -f "$AGENTS_MD" ] || { echo "错误: AGENTS.md 不存在: $AGENTS_MD"; exit 1; }

# ──────────────────────────────────────────
# 颜色输出（与 PowerShell 版风格一致）
# ──────────────────────────────────────────
if [ -t 1 ]; then
    GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
else
    GREEN=''; YELLOW=''; CYAN=''; NC=''
fi

echo -e "${CYAN}=== VocabCraft Agent Config Sync ===${NC}"
echo "项目根目录: $PROJECT_ROOT"

SKIP_OPENCODE=false
SKIP_WORKBUDDY=false
SKIP_HERMES=false
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-opencode) SKIP_OPENCODE=true; shift ;;
        --skip-workbuddy) SKIP_WORKBUDDY=true; shift ;;
        --skip-hermes) SKIP_HERMES=true; shift ;;
        *) echo "未知参数: $1"; exit 1 ;;
    esac
done

sync_skills() {
    local target_dir="$1"
    local target_skills="$target_dir/skills"
    rm -rf "$target_skills"
    echo -e "${YELLOW}同步 Skills → $target_skills${NC}"
    cp -r "$TRAE_SKILLS" "$target_skills"
    local skill_count
    skill_count=$(find "$target_skills" -mindepth 1 -maxdepth 1 -type d | wc -l)
    echo -e "${GREEN}  已同步 $skill_count 个 Skills${NC}"
}

generate_opencode_config() {
    local opencode_dir="$PROJECT_ROOT/.opencode"
    mkdir -p "$opencode_dir"
    python3 -c "
import json, os
from pathlib import Path
project_root = Path(os.environ['PROJECT_ROOT'])
opencode_dir = project_root / '.opencode'
opencode_dir.mkdir(exist_ok=True)
with open(os.environ['TRAE_MCP']) as f:
    trae_mcp = json.load(f)
config = {'\$schema': 'https://opencode.ai/config.json', 'mcp': {}, 'instructions': ['AGENTS.md']}
for name, server in trae_mcp.get('mcpServers', {}).items():
    args = server.get('args', [])
    cwd = None
    cmd_args = []
    skip_next = False
    for arg in args:
        if skip_next:
            skip_next = False
            cwd = arg.replace('\${workspaceFolder}/', '').replace(chr(92), '/')
            continue
        if arg == '--directory':
            skip_next = True
            continue
        cmd_args.append(arg)
    entry = {'type': 'local', 'command': [server['command']] + cmd_args}
    if cwd:
        entry['cwd'] = cwd
    config['mcp'][name] = entry
with open(opencode_dir / 'opencode.json', 'w', encoding='utf-8') as f:
    json.dump(config, f, indent=2, ensure_ascii=False)
"
    echo -e "${GREEN}已生成 opencode 配置${NC}"
}

generate_workbuddy_mcp() {
    local workbuddy_dir="$PROJECT_ROOT/.workbuddy"
    mkdir -p "$workbuddy_dir"
    python3 -c "
import json, os
from pathlib import Path
project_root = Path(os.environ['PROJECT_ROOT'])
workbuddy_dir = project_root / '.workbuddy'
workbuddy_dir.mkdir(exist_ok=True)
uv_path = 'uv'
for p in [os.path.expanduser('~/.local/bin/uv'), '/usr/local/bin/uv']:
    if os.path.isfile(p):
        uv_path = p; break
with open(os.environ['TRAE_MCP']) as f:
    trae_mcp = json.load(f)
mcp = {'mcpServers': {}}
for name, server in trae_mcp.get('mcpServers', {}).items():
    args = [a.replace('\${workspaceFolder}', str(project_root).replace(chr(92), '/')) for a in server.get('args', [])]
    mcp['mcpServers'][name] = {'command': uv_path, 'args': args}
with open(workbuddy_dir / 'mcp.json', 'w', encoding='utf-8') as f:
    json.dump(mcp, f, indent=2, ensure_ascii=False)
"
    echo -e "${GREEN}已生成 WorkBuddy MCP 配置${NC}"
}

generate_hermes_config() {
    local hermes_dir="$PROJECT_ROOT/.hermes"
    mkdir -p "$hermes_dir"
    python3 -c "
import json, os
from pathlib import Path
project_root = Path(os.environ['PROJECT_ROOT'])
hermes_dir = project_root / '.hermes'
hermes_dir.mkdir(exist_ok=True)
with open(os.environ['TRAE_MCP']) as f:
    trae_mcp = json.load(f)
yaml_content = 'mcp_servers:\n'
for name, server in trae_mcp.get('mcpServers', {}).items():
    args = server.get('args', [])
    cwd = None
    cmd_args = []
    skip_next = False
    for arg in args:
        if skip_next:
            skip_next = False
            cwd = arg.replace('\${workspaceFolder}/', '').replace(chr(92), '/')
            continue
        if arg == '--directory':
            skip_next = True
            continue
        cmd_args.append(arg)
    yaml_content += f'  {name}:\n'
    yaml_content += f'    command: \"{server[\"command\"]}\"\n'
    yaml_content += '    args:\n'
    for cmd_arg in cmd_args:
        yaml_content += f'      - \"{cmd_arg}\"\n'
    if cwd:
        yaml_content += f'    cwd: \"{cwd}\"\n'
yaml_content += '\ninstructions:\n'
yaml_content += '  - \"AGENTS.md\"\n'
with open(hermes_dir / 'config.yaml', 'w', encoding='utf-8') as f:
    f.write(yaml_content)
"
    echo -e "${GREEN}已生成 Hermes Agent 配置${NC}"
}

if [ "$SKIP_OPENCODE" = false ]; then
    echo -e "\n${CYAN}--- opencode ---${NC}"
    sync_skills "$PROJECT_ROOT/.opencode"
    generate_opencode_config
fi
if [ "$SKIP_WORKBUDDY" = false ]; then
    echo -e "\n${CYAN}--- WorkBuddy ---${NC}"
    sync_skills "$PROJECT_ROOT/.workbuddy"
    generate_workbuddy_mcp
fi
if [ "$SKIP_HERMES" = false ]; then
    echo -e "\n${CYAN}--- Hermes Agent ---${NC}"
    sync_skills "$PROJECT_ROOT/.hermes"
    generate_hermes_config
fi
echo -e "\n${CYAN}=== 同步完成 ===${NC}"