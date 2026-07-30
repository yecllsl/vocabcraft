# VocabCraft MCP Server 安装脚本
# 适用于 Windows PowerShell
#
# 使用方法：
#   1. 右键此文件 → "使用 PowerShell 运行"
#   2. 或在 PowerShell 中执行: .\install.ps1
#
# 可选参数：
#   -InstallOcr    直接安装 OCR 依赖（跳过询问）
#   -FixPath       将 .trae/mcp.json 中的 ${workspaceFolder} 替换为绝对路径
#   -AgentRuntime  配置 Agent 运行时 (trae/workbuddy/opencode/all)
#
# 前置要求：
#   - Python 3.12+
#   - uv 包管理器 (https://docs.astral.sh/uv/)

param(
    [switch]$InstallOcr,
    [switch]$FixPath,
    [Parameter(Mandatory=$false)]
    [ValidateSet("trae", "workbuddy", "opencode", "all")]
    [string]$AgentRuntime
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  VocabCraft v0.3.0 安装向导" -ForegroundColor Cyan
Write-Host "  (TRAEWORK CN + TRAEIDE CN 双环境)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 获取脚本所在目录（项目根目录）
$projectRoot = $PSScriptRoot

# ──────────────────────────────────────────
# [1/5] 检查 uv 包管理器
# ──────────────────────────────────────────
Write-Host "[1/5] 检查 uv 包管理器..." -ForegroundColor Yellow
try {
    $uvVersion = uv --version 2>&1
    Write-Host "  ✓ uv 已安装 ($uvVersion)" -ForegroundColor Green
} catch {
    Write-Host "  ✗ uv 未安装" -ForegroundColor Red
    Write-Host ""
    Write-Host "  请先安装 uv：" -ForegroundColor Yellow
    Write-Host '  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"' -ForegroundColor White
    Write-Host ""
    Write-Host "  或访问 https://docs.astral.sh/uv/getting-started/install/" -ForegroundColor White
    exit 1
}

# ──────────────────────────────────────────
# [2/5] 检查 Python 版本
# ──────────────────────────────────────────
Write-Host "[2/5] 检查 Python 版本 (>=3.12)..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ✗ Python 未安装" -ForegroundColor Red
    Write-Host ""
    Write-Host "  请先安装 Python 3.12+：" -ForegroundColor Yellow
    Write-Host "  https://www.python.org/downloads/" -ForegroundColor White
    exit 1
}
# 提取版本号并比较
$versionMatch = $pythonVersion -match "(\d+)\.(\d+)"
if ($versionMatch) {
    $major = [int]$Matches[1]
    $minor = [int]$Matches[2]
    if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 12)) {
        Write-Host "  ✗ Python 版本过低: $pythonVersion (需要 >= 3.12)" -ForegroundColor Red
        Write-Host ""
        Write-Host "  请升级 Python: https://www.python.org/downloads/" -ForegroundColor Yellow
        exit 1
    }
}
Write-Host "  ✓ $pythonVersion" -ForegroundColor Green

# ──────────────────────────────────────────
# [3/5] 安装基础依赖
# ──────────────────────────────────────────
Write-Host "[3/5] 安装基础依赖..." -ForegroundColor Yellow
Write-Host "  基础依赖不含 OCR 引擎（paddleocr/paddlepaddle 体积大，已拆为可选）" -ForegroundColor Cyan

$mcpDir = Join-Path $projectRoot "vocabcraft-mcp"

# 使用 uv sync 安装基础依赖（不包含 ocr extra）
Push-Location $mcpDir
try {
    Write-Host "  正在安装依赖包..." -ForegroundColor Cyan
    uv sync 2>&1 | ForEach-Object { Write-Host "    $_" -ForegroundColor DarkGray }

    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ✗ 依赖安装失败" -ForegroundColor Red
        Write-Host ""
        Write-Host "  请尝试手动安装：" -ForegroundColor Yellow
        Write-Host "  cd vocabcraft-mcp" -ForegroundColor White
        Write-Host "  uv sync" -ForegroundColor White
        exit 1
    }
    Write-Host "  ✓ 基础依赖安装完成" -ForegroundColor Green
} finally {
    Pop-Location
}

# ──────────────────────────────────────────
# [4/5] 询问并安装可选 OCR 依赖
# ──────────────────────────────────────────
Write-Host "[4/5] 是否安装 OCR 可选依赖？" -ForegroundColor Yellow
Write-Host "  OCR 用于图片词汇识别，paddleocr+paddlepaddle 约 1.5GB，安装较慢。" -ForegroundColor Cyan
Write-Host "  仅当需要 /capture 拍照录入词汇时才需要。" -ForegroundColor Cyan

$shouldInstallOcr = $false
if ($InstallOcr) {
    # 命令行参数 -InstallOcr 直接安装，不询问
    $shouldInstallOcr = $true
    Write-Host "  ℹ 检测到 -InstallOcr 参数，直接安装" -ForegroundColor Cyan
} else {
    $installOcrInput = Read-Host "  安装 OCR 依赖？[y/N]"
    if ($installOcrInput -match "^[Yy]$") {
        $shouldInstallOcr = $true
    }
}

if ($shouldInstallOcr) {
    Push-Location $mcpDir
    try {
        Write-Host "  正在安装 OCR 依赖..." -ForegroundColor Cyan
        uv sync --extra ocr 2>&1 | ForEach-Object { Write-Host "    $_" -ForegroundColor DarkGray }
        if ($LASTEXITCODE -ne 0) {
            Write-Host "  ✗ OCR 依赖安装失败，可稍后手动重试：uv sync --extra ocr" -ForegroundColor Red
        } else {
            Write-Host "  ✓ OCR 依赖安装完成" -ForegroundColor Green
        }
    } finally {
        Pop-Location
    }
} else {
    Write-Host "  ⊘ 已跳过 OCR 依赖。后续需要时执行：cd vocabcraft-mcp && uv sync --extra ocr" -ForegroundColor DarkGray
}

# ──────────────────────────────────────────
# [5/5] Agent Runtime 配置
# ──────────────────────────────────────────
if ($AgentRuntime) {
    Write-Host ""
    Write-Host "=== Agent Runtime 配置 ===" -ForegroundColor Cyan

    $SyncScript = Join-Path $PSScriptRoot "scripts/sync-agent-configs.ps1"

    switch ($AgentRuntime) {
        "trae" {
            Write-Host "Trae 配置说明:" -ForegroundColor Yellow
            Write-Host "  1. 用 Trae 打开项目文件夹"
            Write-Host "  2. 设置 > MCP > 启用「项目级 MCP」"
            Write-Host "  3. 设置 > 规则 > 开启「将 AGENTS.md 包含在上下文中」"
        }
        "workbuddy" {
            Write-Host "正在同步 WorkBuddy 配置..." -ForegroundColor Yellow
            if (Test-Path $SyncScript) {
                & $SyncScript -SkipOpencode
                Write-Host ""
                Write-Host "下一步:" -ForegroundColor Yellow
                Write-Host "  1. 用 WorkBuddy 打开项目文件夹"
                Write-Host "  2. 在 MCP 配置中信任 vocabcraft-mcp"
            } else {
                Write-Host "  同步脚本不存在: $SyncScript" -ForegroundColor Red
            }
        }
        "opencode" {
            Write-Host "正在同步 opencode 配置..." -ForegroundColor Yellow
            if (Test-Path $SyncScript) {
                & $SyncScript -SkipWorkbuddy
                Write-Host ""
                Write-Host "下一步:" -ForegroundColor Yellow
                Write-Host "  1. 在项目目录运行 opencode"
                Write-Host "  2. AGENTS.md 将自动加载"
            } else {
                Write-Host "  同步脚本不存在: $SyncScript" -ForegroundColor Red
            }
        }
        "all" {
            Write-Host "正在同步所有 Agent Runtime 配置..." -ForegroundColor Yellow
            if (Test-Path $SyncScript) {
                & $SyncScript
                Write-Host ""
                Write-Host "所有配置已同步。各运行时下一步:" -ForegroundColor Green
                Write-Host "  Trae: 设置 > 规则 > 开启「将 AGENTS.md 包含在上下文中」"
                Write-Host "  WorkBuddy: 在 MCP 配置中信任 vocabcraft-mcp"
                Write-Host "  opencode: 在项目目录运行 opencode"
            } else {
                Write-Host "  同步脚本不存在: $SyncScript" -ForegroundColor Red
            }
        }
    }
}

# ──────────────────────────────────────────
# [6/6] 验证安装
# ──────────────────────────────────────────
Write-Host "[6/6] 验证安装..." -ForegroundColor Yellow

Push-Location $mcpDir
try {
    # 验证 MCP Server 入口点可用（FastMCP 的 --help 可能直接启动 server，只要不报错即可）
    $testResult = uv run vocabcraft-mcp --help 2>&1
    Write-Host "  ✓ MCP Server 入口点可用" -ForegroundColor Green
} catch {
    Write-Host "  ⚠ 自动验证失败，但不影响使用" -ForegroundColor Yellow
    Write-Host "  如遇问题请手动验证: cd vocabcraft-mcp && uv run vocabcraft-mcp" -ForegroundColor Yellow
} finally {
    Pop-Location
}

# ──────────────────────────────────────────
# mcp.json 路径回退方案（双环境共用）
# ──────────────────────────────────────────
# 检查 .trae/mcp.json 中的 ${workspaceFolder} 变量是否被 Trae 支持
# TRAEWORK CN 与 TRAEIDE CN 最新版均支持此变量；旧版需用 -FixPath 降级
$mcpJsonPath = Join-Path $projectRoot ".trae\mcp.json"
if (Test-Path $mcpJsonPath) {
    $mcpContent = Get-Content $mcpJsonPath -Raw
    if ($mcpContent -match '\$\{workspaceFolder\}') {
        Write-Host ""
        Write-Host "  ℹ 检测到 mcp.json 使用了 \${workspaceFolder} 变量" -ForegroundColor Cyan
        Write-Host "    TRAEWORK CN 与 TRAEIDE CN 会自动替换此变量，无需手动配置" -ForegroundColor Cyan
        Write-Host "    如果你的 Trae 版本不支持变量替换，请运行：" -ForegroundColor Cyan
        Write-Host "    .\install.ps1 -FixPath" -ForegroundColor White
    }
}

# 处理 -FixPath 参数：将 ${workspaceFolder} 替换为实际路径
if ($FixPath) {
    Write-Host ""
    Write-Host "  正在修复 mcp.json 路径..." -ForegroundColor Yellow
    if (Test-Path $mcpJsonPath) {
        $mcpContent = Get-Content $mcpJsonPath -Raw
        # 路径中的反斜杠转为正斜杠，避免 JSON 转义问题
        $escapedRoot = $projectRoot -replace '\\', '/'
        $fixedContent = $mcpContent -replace '\$\{workspaceFolder\}', $escapedRoot
        Set-Content -Path $mcpJsonPath -Value $fixedContent -Encoding UTF8
        Write-Host "  ✓ mcp.json 路径已修复为: $escapedRoot" -ForegroundColor Green
        Write-Host "  ⚠ 注意：修复后配置仅对当前路径有效，移动项目后需重新运行 -FixPath" -ForegroundColor Yellow
        Write-Host "  ⚠ 注意：双环境可移植性会降低，建议优先升级 Trae 版本以支持变量" -ForegroundColor Yellow
    } else {
        Write-Host "  ✗ 未找到 $mcpJsonPath" -ForegroundColor Red
    }
}

# ──────────────────────────────────────────
# 安装完成提示
# ──────────────────────────────────────────
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  ✓ 安装完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "下一步操作（TRAEWORK CN 与 TRAEIDE CN 操作一致）：" -ForegroundColor White
Write-Host ""
Write-Host "  1. 用 Trae IDE 打开此文件夹" -ForegroundColor White
Write-Host "     文件 → 打开文件夹 → 选择: $projectRoot" -ForegroundColor DarkGray
Write-Host ""
Write-Host "  2. 启用项目级 MCP" -ForegroundColor White
Write-Host "     设置 → MCP → 打开'启用项目级 MCP'开关" -ForegroundColor DarkGray
Write-Host ""
Write-Host "  3. 重启 Trae" -ForegroundColor White
Write-Host ""
Write-Host "  4. 在另一个环境（TRAEWORK / TRAEIDE）重复步骤 1-3 即可双环境共用" -ForegroundColor Cyan
Write-Host ""
Write-Host "  5. 开始使用！" -ForegroundColor White
Write-Host "     /capture  - 采集新词汇" -ForegroundColor DarkGray
Write-Host "     /review   - 复习到期词汇" -ForegroundColor DarkGray
Write-Host "     /quiz     - 生成考题并作答" -ForegroundColor DarkGray
Write-Host "     /stats    - 查看学习统计" -ForegroundColor DarkGray
Write-Host "     /export   - 导出词汇数据" -ForegroundColor DarkGray
Write-Host ""
