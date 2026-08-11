<#
.SYNOPSIS
    同步 .agents/ 配置到各平台目录。
.DESCRIPTION
    从 .agents/runtime/ 目录读取配置，生成 .trae/、.opencode/、.codebuddy/ 配置。
    .agents/ 是 AAIF 标准的唯一配置源。
.PARAMETER SkipTrae
    跳过 Trae 配置生成。
.PARAMETER SkipOpencode
    跳过 opencode 配置生成。
.PARAMETER SkipCodebuddy
    跳过 CodeBuddy 配置生成。
#>
param(
    [switch]$SkipTrae,
    [switch]$SkipOpencode,
    [switch]$SkipCodebuddy
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
    $null = New-Item -ItemType Directory -Path $TargetDir -Force
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

function New-CodebuddyConfig {
    $CodebuddyDir = Join-Path $ProjectRoot ".codebuddy"
    if (-not (Test-Path $CodebuddyDir)) { New-Item -ItemType Directory -Path $CodebuddyDir -Force | Out-Null }
    $SourceConfig = Join-Path $AgentsRuntime "codebuddy.json"
    if (Test-Path $SourceConfig) {
        Write-Host "复制 CodeBuddy 配置 → $CodebuddyDir" -ForegroundColor Yellow
        Copy-Item -Force $SourceConfig (Join-Path $CodebuddyDir "mcp.json")
        Write-Host "  已生成 CodeBuddy 配置" -ForegroundColor Green
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
if (-not $SkipCodebuddy) {
    Write-Host "`n--- CodeBuddy ---" -ForegroundColor Cyan
    Sync-Skills -TargetDir (Join-Path $ProjectRoot ".codebuddy")
    Sync-AgentsMd -TargetDir (Join-Path $ProjectRoot ".codebuddy")
    New-CodebuddyConfig
}
Write-Host "`n=== 同步完成 ===" -ForegroundColor Cyan
