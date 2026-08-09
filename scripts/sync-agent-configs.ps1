<#
.SYNOPSIS
    同步 .agents/ 配置到各平台目录。
.DESCRIPTION
    从 .agents/runtime/ 目录读取配置，生成 .trae/、.opencode/、.workbuddy/ 和 .hermes/ 配置。
    .agents/ 是 AAIF 标准的唯一配置源。
.PARAMETER SkipTrae
    跳过 Trae 配置生成。
.PARAMETER SkipOpencode
    跳过 opencode 配置生成。
.PARAMETER SkipWorkbuddy
    跳过 WorkBuddy 配置生成。
.PARAMETER SkipHermes
    跳过 Hermes Agent 配置生成。
#>
param(
    [switch]$SkipTrae,
    [switch]$SkipOpencode,
    [switch]$SkipWorkbuddy,
    [switch]$SkipHermes
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot

$AgentsDir = Join-Path $ProjectRoot ".agents"
$AgentsRuntime = Join-Path $AgentsDir "runtime"
$AgentsSkills = Join-Path $AgentsDir "skills"
$AgentsMd = Join-Path $AgentsDir "AGENTS.md"

if (-not (Test-Path $AgentsRuntime)) { Write-Error "AAIF 运行时配置目录不存在: $AgentsRuntime"; exit 1 }
if (-not (Test-Path $AgentsSkills)) { Write-Error "AAIF 技能目录不存在: $AgentsSkills"; exit 1 }
if (-not (Test-Path $AgentsMd)) { Write-Error "AGENTS.md 不存在: $AgentsMd"; exit 1 }

Write-Host "=== VocabCraft AAIF Config Sync ===" -ForegroundColor Cyan
Write-Host "项目根目录: $ProjectRoot"
Write-Host "配置源: .agents/ (AAIF 标准)"

function Sync-Skills {
    param([string]$TargetDir)
    $TargetSkills = Join-Path $TargetDir "skills"
    if (Test-Path $TargetSkills) { Remove-Item -Recurse -Force $TargetSkills }
    Write-Host "同步 Skills → $TargetSkills" -ForegroundColor Yellow
    Copy-Item -Recurse -Force $AgentsSkills $TargetSkills
    $SkillCount = (Get-ChildItem -Path $TargetSkills -Directory).Count
    Write-Host "  已同步 $SkillCount 个 Skills" -ForegroundColor Green
}

function Sync-AgentsMd {
    param([string]$TargetDir)
    $TargetAgentsMd = Join-Path $TargetDir "AGENTS.md"
    Write-Host "同步 AGENTS.md → $TargetAgentsMd" -ForegroundColor Yellow
    Copy-Item -Force $AgentsMd $TargetAgentsMd
    Write-Host "  已同步 AGENTS.md" -ForegroundColor Green
}

function New-TraeConfig {
    $TraeDir = Join-Path $ProjectRoot ".trae"
    if (-not (Test-Path $TraeDir)) { New-Item -ItemType Directory -Path $TraeDir -Force | Out-Null }
    $SourceConfig = Join-Path $AgentsRuntime "trae.json"
    if (Test-Path $SourceConfig) {
        Write-Host "复制 Trae 配置 → $TraeDir" -ForegroundColor Yellow
        Copy-Item -Force $SourceConfig (Join-Path $TraeDir "mcp.json")
        Write-Host "  已生成 Trae 配置" -ForegroundColor Green
    }
}

function New-OpencodeConfig {
    $OpencodeDir = Join-Path $ProjectRoot ".opencode"
    if (-not (Test-Path $OpencodeDir)) { New-Item -ItemType Directory -Path $OpencodeDir -Force | Out-Null }
    $SourceConfig = Join-Path $AgentsRuntime "opencode.json"
    if (Test-Path $SourceConfig) {
        Write-Host "复制 opencode 配置 → $OpencodeDir" -ForegroundColor Yellow
        Copy-Item -Force $SourceConfig (Join-Path $OpencodeDir "opencode.json")
        Write-Host "  已生成 opencode 配置" -ForegroundColor Green
    }
}

function New-WorkbuddyConfig {
    $WorkbuddyDir = Join-Path $ProjectRoot ".workbuddy"
    if (-not (Test-Path $WorkbuddyDir)) { New-Item -ItemType Directory -Path $WorkbuddyDir -Force | Out-Null }
    $SourceConfig = Join-Path $AgentsRuntime "workbuddy.json"
    if (Test-Path $SourceConfig) {
        Write-Host "复制 WorkBuddy 配置 → $WorkbuddyDir" -ForegroundColor Yellow
        Copy-Item -Force $SourceConfig (Join-Path $WorkbuddyDir "mcp.json")
        Write-Host "  已生成 WorkBuddy 配置" -ForegroundColor Green
    }
}

function New-HermesConfig {
    $HermesDir = Join-Path $ProjectRoot ".hermes"
    if (-not (Test-Path $HermesDir)) { New-Item -ItemType Directory -Path $HermesDir -Force | Out-Null }
    $SourceConfig = Join-Path $AgentsRuntime "hermes.yaml"
    if (Test-Path $SourceConfig) {
        Write-Host "复制 Hermes Agent 配置 → $HermesDir" -ForegroundColor Yellow
        Copy-Item -Force $SourceConfig (Join-Path $HermesDir "config.yaml")
        Write-Host "  已生成 Hermes Agent 配置" -ForegroundColor Green
    }
}

if (-not $SkipTrae) {
    Write-Host "`n--- Trae ---" -ForegroundColor Cyan
    Sync-Skills -TargetDir (Join-Path $ProjectRoot ".trae")
    Sync-AgentsMd -TargetDir $ProjectRoot
    New-TraeConfig
}
if (-not $SkipOpencode) {
    Write-Host "`n--- opencode ---" -ForegroundColor Cyan
    Sync-Skills -TargetDir (Join-Path $ProjectRoot ".opencode")
    Sync-AgentsMd -TargetDir (Join-Path $ProjectRoot ".opencode")
    New-OpencodeConfig
}
if (-not $SkipWorkbuddy) {
    Write-Host "`n--- WorkBuddy ---" -ForegroundColor Cyan
    Sync-Skills -TargetDir (Join-Path $ProjectRoot ".workbuddy")
    Sync-AgentsMd -TargetDir (Join-Path $ProjectRoot ".workbuddy")
    New-WorkbuddyConfig
}
if (-not $SkipHermes) {
    Write-Host "`n--- Hermes Agent ---" -ForegroundColor Cyan
    Sync-Skills -TargetDir (Join-Path $ProjectRoot ".hermes")
    Sync-AgentsMd -TargetDir (Join-Path $ProjectRoot ".hermes")
    New-HermesConfig
}
Write-Host "`n=== 同步完成 ===" -ForegroundColor Cyan