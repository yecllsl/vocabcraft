#!/bin/sh
# scripts/check-config-drift.sh — 检查三平台生成目录是否与 vocabcraft.plugin 真相源一致
#
# 用途：CI config-drift job 与本地巡检。与 pre-commit 钩子互为补充：
#   - pre-commit 钩子查「暂存区」，拦截提交那一刻的违规
#   - 本脚本查「工作区」，作为无本地钩子时的 CI 兜底（例如绕过钩子 push）
#
# 检查范围（与 pre-commit 一致）：三平台的 skills/** 与 AGENTS.md 必须与其
# vocabcraft.plugin/ 源逐字节一致；非纯复制产物（mcp.json / config.yaml / .ignore 等）豁免。
# 以 vocabcraft.plugin 为权威遍历，因此同时覆盖「直改平台副本」与「改源忘同步（缺同步）」两类漂移。

set -eu

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

tmp=".git/check-drift.$$"
trap 'rm -f "$tmp"' EXIT

violations=0

# 比较生成文件与源；不一致则计数并报告
check_pair() {  # $1=生成文件, $2=源
    if ! cmp -s "$1" "$2"; then
        echo "漂移: $1 与真相源 $2 不一致" >&2
        violations=$((violations + 1))
    fi
}

# 根 AGENTS.md：Trae 读取的是这一份（由 sync 从真相源拷到项目根），必须与源一致
check_pair "AGENTS.md" "vocabcraft.plugin/AGENTS.md"

# 平台内 AGENTS.md：.trae 不放，故「有则必须与源一致」
for p in .trae .opencode; do
    if [ -f "$p/AGENTS.md" ]; then
        check_pair "$p/AGENTS.md" "vocabcraft.plugin/AGENTS.md"
    fi
done

# skills/**：以 vocabcraft.plugin/skills 为权威，检查三平台副本存在且一致
find vocabcraft.plugin/skills -type f > "$tmp"
while IFS= read -r f || [ -n "$f" ]; do
    if [ -z "$f" ]; then
        continue
    fi
    for p in .trae .opencode; do
        copy="$p${f#vocabcraft.plugin}"    # .vocabcraft.plugin/skills/x → $p/skills/x（POSIX 前缀剔除，兼容 dash）
        if [ ! -f "$copy" ]; then
            echo "漂移: $p 缺少同步文件 $copy（源 $f 未同步到 $p）" >&2
            violations=$((violations + 1))
        else
            check_pair "$copy" "$f"
        fi
    done
done < "$tmp"

# 插件清单可移植性：分发的清单里不得出现本机绝对路径（正/反斜杠的盘符路径、用户主目录、跨目录引用）
MANIFESTS="vocabcraft.plugin/plugin.json vocabcraft.plugin/mcp.json vocabcraft.plugin/.mcp.json vocabcraft.plugin/.codebuddy-plugin/plugin.json .codebuddy-plugin/marketplace.json"
for m in $MANIFESTS; do
    if [ ! -f "$m" ]; then
        echo "漂移: 缺少插件清单 $m" >&2
        violations=$((violations + 1))
        continue
    fi
    if grep -Eq '"[A-Za-z]:[\\/]|\\\\[Uu]sers|/[Uu]sers/|\.\./' "$m"; then
        echo "漂移: $m 含本机绝对路径或跨目录引用，分发后会失效" >&2
        violations=$((violations + 1))
    fi
done

if [ "$violations" -gt 0 ]; then
    echo "配置漂移: $violations 处不一致。请运行 scripts/sync-agent-configs.sh（或 .ps1）同步后重新检查。" >&2
    exit 1
fi

echo "config-drift: 三平台配置与 vocabcraft.plugin 真相源一致，插件清单无本机路径"
exit 0