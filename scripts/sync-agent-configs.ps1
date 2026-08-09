<#
.SYNOPSIS
    同步 Trae 配置到 opencode、WorkBuddy 和 Hermes Agent。
.DESCRIPTION
    从 .trae/ 目录读取 Skills 和 MCP 配置，生成 .opencode/、.workbuddy/ 和 .hermes/ 配置。
.PARAMETER SkipOpencode
    跳过 opencode 配置生成。
.PARAMETER SkipWorkbuddy
    跳过 WorkBuddy 配置生成。
.PARAMETER SkipHermes
    跳过 Hermes Agent 配置生成。
#>
param(
    [switch]$SkipOpencode,
    [switch]$SkipWorkbuddy,
    [switch]$SkipHermes
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot

$TraeSkills = Join-Path $ProjectRoot ".trae/skills"
$TraeMcp = Join-Path $ProjectRoot ".trae/mcp.json"
$AgentsMd = Join-Path $ProjectRoot "AGENTS.md"

if (-not (Test-Path $TraeSkills)) { Write-Error "源目录不存在: $TraeSkills"; exit 1 }
if (-not (Test-Path $TraeMcp)) { Write-Error "MCP 配置不存在: $TraeMcp"; exit 1 }
if (-not (Test-Path $AgentsMd)) { Write-Error "AGENTS.md 不存在: $AgentsMd"; exit 1 }

Write-Host "=== VocabCraft Agent Config Sync ===" -ForegroundColor Cyan
Write-Host "项目根目录: $ProjectRoot"

function Sync-Skills {
    param([string]$TargetDir)
    $TargetSkills = Join-Path $TargetDir "skills"
    if (Test-Path $TargetSkills) { Remove-Item -Recurse -Force $TargetSkills }
    Write-Host "同步 Skills → $TargetSkills" -ForegroundColor Yellow
    Copy-Item -Recurse -Force $TraeSkills $TargetSkills
    $SkillCount = (Get-ChildItem -Path $TargetSkills -Directory).Count
    Write-Host "  已同步 $SkillCount 个 Skills" -ForegroundColor Green
}

function New-OpencodeConfig {
    $OpencodeDir = Join-Path $ProjectRoot ".opencode"
    if (-not (Test-Path $OpencodeDir)) { New-Item -ItemType Directory -Path $OpencodeDir -Force | Out-Null }
    $McpContent = Get-Content $TraeMcp -Raw | ConvertFrom-Json
    $OpencodeConfig = @{ '$schema' = "https://opencode.ai/config.json"; mcp = @{}; instructions = @("AGENTS.md") }
    foreach ($ServerName in $McpContent.mcpServers.PSObject.Properties.Name) {
        $Server = $McpContent.mcpServers.$ServerName
        # Extract cwd from --directory arg, build command without it
        $cwd = $null
        $cmdArgs = @()
        $skipNext = $false
        foreach ($arg in $Server.args) {
            if ($skipNext) { $skipNext = $false; $cwd = ($arg -replace '\$\{workspaceFolder\}/', '' -replace '\\', '/'); continue }
            if ($arg -eq '--directory') { $skipNext = $true; continue }
            $cmdArgs += $arg
        }
        $mcpEntry = @{ type = "local"; command = @($Server.command) + $cmdArgs }
        if ($cwd) { $mcpEntry['cwd'] = $cwd }
        $OpencodeConfig.mcp[$ServerName] = $mcpEntry
    }
    $OpencodeConfig | ConvertTo-Json -Depth 10 | Set-Content -Path (Join-Path $OpencodeDir "opencode.json") -Encoding UTF8
    Write-Host "已生成 opencode 配置" -ForegroundColor Green
}

function New-WorkbuddyMcp {
    $WorkbuddyDir = Join-Path $ProjectRoot ".workbuddy"
    if (-not (Test-Path $WorkbuddyDir)) { New-Item -ItemType Directory -Path $WorkbuddyDir -Force | Out-Null }
    $McpContent = Get-Content $TraeMcp -Raw | ConvertFrom-Json
    $UvPath = (Get-Command uv -ErrorAction SilentlyContinue).Source
    if (-not $UvPath) { $UvPath = "$env:USERPROFILE\.local\bin\uv.exe"; if (-not (Test-Path $UvPath)) { $UvPath = "uv" } }
    $WorkbuddyMcp = @{ mcpServers = @{} }
    foreach ($ServerName in $McpContent.mcpServers.PSObject.Properties.Name) {
        $Server = $McpContent.mcpServers.$ServerName
        $Args = $Server.args | ForEach-Object { $_ -replace '\$\{workspaceFolder\}', ($ProjectRoot -replace '\\', '/') }
        $WorkbuddyMcp.mcpServers[$ServerName] = @{ command = $UvPath; args = $Args }
    }
    $WorkbuddyMcp | ConvertTo-Json -Depth 10 | Set-Content -Path (Join-Path $WorkbuddyDir "mcp.json") -Encoding UTF8
    Write-Host "已生成 WorkBuddy MCP 配置" -ForegroundColor Green
}

function New-HermesConfig {
    $HermesDir = Join-Path $ProjectRoot ".hermes"
    if (-not (Test-Path $HermesDir)) { New-Item -ItemType Directory -Path $HermesDir -Force | Out-Null }
    $McpContent = Get-Content $TraeMcp -Raw | ConvertFrom-Json
    $HermesConfig = @{ mcp_servers = @{}; instructions = @("AGENTS.md") }
    foreach ($ServerName in $McpContent.mcpServers.PSObject.Properties.Name) {
        $Server = $McpContent.mcpServers.$ServerName
        $cwd = $null
        $cmdArgs = @()
        $skipNext = $false
        foreach ($arg in $Server.args) {
            if ($skipNext) { $skipNext = $false; $cwd = ($arg -replace '\$\{workspaceFolder\}/', '' -replace '\\', '/'); continue }
            if ($arg -eq '--directory') { $skipNext = $true; continue }
            $cmdArgs += $arg
        }
        $mcpEntry = @{ command = $Server.command; args = $cmdArgs }
        if ($cwd) { $mcpEntry['cwd'] = $cwd }
        $HermesConfig.mcp_servers[$ServerName] = $mcpEntry
    }
    $HermesConfig | ConvertTo-Json -Depth 10 | Set-Content -Path (Join-Path $HermesDir "config.yaml") -Encoding UTF8
    Write-Host "已生成 Hermes Agent 配置" -ForegroundColor Green
}

if (-not $SkipOpencode) {
    Write-Host "`n--- opencode ---" -ForegroundColor Cyan
    Sync-Skills -TargetDir (Join-Path $ProjectRoot ".opencode")
    New-OpencodeConfig
}
if (-not $SkipWorkbuddy) {
    Write-Host "`n--- WorkBuddy ---" -ForegroundColor Cyan
    Sync-Skills -TargetDir (Join-Path $ProjectRoot ".workbuddy")
    New-WorkbuddyMcp
}
if (-not $SkipHermes) {
    Write-Host "`n--- Hermes Agent ---" -ForegroundColor Cyan
    Sync-Skills -TargetDir (Join-Path $ProjectRoot ".hermes")
    New-HermesConfig
}
Write-Host "`n=== 同步完成 ===" -ForegroundColor Cyan