# VocabCraft 发布包构建脚本
# 从源码生成可分发的 zip 包（白名单复制策略，避免误打包 .venv）
#
# 使用方法：
#   pwsh .\scripts\build-release.ps1 [-Version "0.6.2"]
#
# 输出：
#   dist\VocabCraft-v0.6.2.zip

param(
    [string]$Version
)

$ErrorActionPreference = "Stop"

# ──────────────────────────────────────────
# 路径定义
# ──────────────────────────────────────────
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

# 版本默认从真相源 pyproject.toml 读取，避免硬编码漂移（check_version.py 的同一真相源）
if (-not $Version) {
    $pyProject = Join-Path $projectRoot "vocabcraft.plugin/vocabcraft-mcp/pyproject.toml"
    $m = Get-Content $pyProject -Raw | Select-String -Pattern '^version\s*=\s*"([^"]+)"'
    if ($m) { $Version = $m.Matches.Groups[1].Value }
    else { Write-Error "无法从 pyproject.toml 读取版本号"; exit 1 }
}

$distDir = Join-Path $projectRoot "dist"
$packageName = "VocabCraft-v$Version"
$tempDir = Join-Path $distDir $packageName
$zipPath = Join-Path $distDir "$packageName.zip"
$gzPath = Join-Path $distDir "$packageName.tar.gz"

# 基线运行时平台（AAIF 4 运行时：Trae IDE CN / Trae Work CN / CodeBuddy / OpenCode / Goose）
# vocabcraft.plugin/ 为 AAIF 真相源：Skills 与 AGENTS.md 同步自 vocabcraft.plugin/，平台配置生成自 vocabcraft.plugin/runtime/*.json
$agentsDir = Join-Path $projectRoot "vocabcraft.plugin"
$agentsRuntime = Join-Path $agentsDir "runtime"
$agentsSkills = Join-Path $agentsDir "skills"
$agentsMd = Join-Path $agentsDir "AGENTS.md"
# 每个平台：目录名 / 运行时配置源(json) / 配置输出文件名 / AGENTS.md 是否放进平台目录（Trae 放根目录）
$platforms = @(
    [PSCustomObject]@{ Dir = ".trae";      ConfigSrc = "trae.json";      ConfigDst = "mcp.json";      AgentsMdInPlatform = $false },
    [PSCustomObject]@{ Dir = ".opencode";  ConfigSrc = "opencode.json";  ConfigDst = "opencode.json"; AgentsMdInPlatform = $true },
    [PSCustomObject]@{ Dir = ".codebuddy"; ConfigSrc = "codebuddy.json"; ConfigDst = "mcp.json";      AgentsMdInPlatform = $true },
    [PSCustomObject]@{ Dir = ".goose";     ConfigSrc = "goose.json";     ConfigDst = "config.yaml";   AgentsMdInPlatform = $true }
)


function Write-Step([string]$msg) {
    Write-Host "[build] $msg" -ForegroundColor Yellow
}
function Write-Ok([string]$msg) {
    Write-Host "[ok]    $msg" -ForegroundColor Green
}
function Write-Err([string]$msg) {
    Write-Host "[err]   $msg" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  VocabCraft v$Version release build" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# ──────────────────────────────────────────
# [1/6] 清理旧构建（使用 .NET API 处理长路径）
# ──────────────────────────────────────────
Write-Step "[1/6] Clean previous build..."
if (Test-Path $distDir) {
    # 使用 .NET API 直接删除，可处理部分长路径；失败则用 robocopy MIR 清空
    try {
        [System.IO.Directory]::Delete($distDir, $true)
    } catch {
        $emptyTmp = Join-Path $env:TEMP "vc_empty_$(Get-Random)"
        New-Item -ItemType Directory -Path $emptyTmp -Force | Out-Null
        robocopy $emptyTmp $distDir /MIR /R:0 /W:0 /NFL /NDL /NJH /NJS /NP | Out-Null
        [System.IO.Directory]::Delete($distDir, $true)
        Remove-Item -Recurse -Force $emptyTmp -ErrorAction SilentlyContinue
    }
}
New-Item -ItemType Directory -Path $distDir | Out-Null
Write-Ok "cleaned"

# ──────────────────────────────────────────
# [2/6] 创建目标目录结构
# ──────────────────────────────────────────
Write-Step "[2/6] Create directory structure..."
# 顶层目录
New-Item -ItemType Directory -Path $tempDir -Force | Out-Null
# AAIF 真相源子目录（opencode 的 instructions 引用 vocabcraft.plugin/AGENTS.md）
New-Item -ItemType Directory -Path (Join-Path $tempDir "vocabcraft.plugin") -Force | Out-Null
# 四个运行时平台目录（Trae IDE CN / Trae Work CN / CodeBuddy / OpenCode / Goose）
# 基线约定：每个平台目录都有 skills/ 与 AGENTS.md（Trae 例外：AGENTS.md 放根目录）
foreach ($p in $platforms) {
    New-Item -ItemType Directory -Path (Join-Path $tempDir $p.Dir "skills") -Force | Out-Null
}
# vocabcraft.plugin/vocabcraft-mcp 子目录
New-Item -ItemType Directory -Path (Join-Path $tempDir "vocabcraft.plugin/vocabcraft-mcp\src") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $tempDir "vocabcraft.plugin/vocabcraft-mcp\data\vocabs") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $tempDir "vocabcraft.plugin/vocabcraft-mcp\data\reviews") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $tempDir "vocabcraft.plugin/vocabcraft-mcp\data\quizzes") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $tempDir "vocabcraft.plugin/vocabcraft-mcp\data\exports") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $tempDir "vocabcraft.plugin/vocabcraft-mcp\data\images") -Force | Out-Null
Write-Ok "directories created"

# ──────────────────────────────────────────
# [3/6] 复制 AAIF 多平台配置（.trae / .opencode / .codebuddy / .goose）
# ──────────────────────────────────────────
Write-Step "[3/6] Copy AAIF platform configs (.trae/.opencode/.codebuddy/.goose)..."

# opencode 的 instructions 引用 vocabcraft.plugin/AGENTS.md，发布包需包含该文件
Copy-Item -Force $agentsMd (Join-Path $tempDir "vocabcraft.plugin\AGENTS.md")

function New-GooseReleaseConfig {
    param(
        [string]$SrcJson,
        [string]$DstDir
    )
    # 发布包使用相对 --directory（解压到任意位置均可工作），故 --no-resolve-dir
    & python (Join-Path $PSScriptRoot "generate-goose-config.py") --runtime-json $SrcJson --out-dir $DstDir --no-resolve-dir
    if ($LASTEXITCODE -ne 0) {
        Write-Err "goose config generation failed (exit $LASTEXITCODE)"
        exit 1
    }
}

foreach ($p in $platforms) {
    $platDir = Join-Path $tempDir $p.Dir

    # Skills：整目录同步（与 sync-agent-configs 一致，不再做 vocabcraft-* 前缀过滤）
    $rc = robocopy $agentsSkills (Join-Path $platDir "skills") /E /XD __pycache__ .pytest_cache /XF *.pyc /NFL /NDL /NJH /NJS /NP
    if ($LASTEXITCODE -ge 8) {
        Write-Err "robocopy skills failed for $($p.Dir) (exit $LASTEXITCODE)"
        exit 1
    }

    # AGENTS.md（Trae 放根目录，其余平台放进各自目录）
    if ($p.AgentsMdInPlatform) {
        Copy-Item -Force $agentsMd (Join-Path $platDir "AGENTS.md")
    }

    # 平台配置：来自 AAIF 运行时真相源 vocabcraft.plugin/runtime/<ConfigSrc>
    $cfgSrc = Join-Path $agentsRuntime $p.ConfigSrc
    $cfgDst = Join-Path $platDir $p.ConfigDst
    if ($p.ConfigDst -eq "config.yaml") {
        New-GooseReleaseConfig -SrcJson $cfgSrc -DstDir $platDir
    } else {
        Copy-Item -Force $cfgSrc $cfgDst
    }
}

Write-Ok "AAIF platform configs copied (.trae/.opencode/.codebuddy/.goose)"

# ──────────────────────────────────────────
# [4/6] 复制 vocabcraft.plugin/vocabcraft-mcp 源码（白名单）
# ──────────────────────────────────────────
Write-Step "[4/6] Copy vocabcraft.plugin/vocabcraft-mcp source..."

$mcpSrc = Join-Path $projectRoot "vocabcraft.plugin/vocabcraft-mcp"
$mcpDst = Join-Path $tempDir "vocabcraft.plugin/vocabcraft-mcp"

# 4a. 顶层配置文件
$mcpTopFiles = @("pyproject.toml", "uv.lock", ".python-version")
foreach ($f in $mcpTopFiles) {
    $src = Join-Path $mcpSrc $f
    if (Test-Path $src) {
        Copy-Item $src (Join-Path $mcpDst $f) -Force
    }
}

# 4b. src/ 目录递归复制（用 robocopy 排除 __pycache__ 和 .pytest_cache）
$srcDir = Join-Path $mcpSrc "src"
$srcDst = Join-Path $mcpDst "src"
if (Test-Path $srcDir) {
    # robocopy 对单个目录的 /XD 排除很可靠（直接给目录名）
    $rc = robocopy $srcDir $srcDst /E /XD __pycache__ .pytest_cache /XF *.pyc /NFL /NDL /NJH /NJS /NP
    # robocopy exit code < 8 表示成功
    if ($LASTEXITCODE -ge 8) {
        Write-Err "robocopy failed with exit code $LASTEXITCODE"
        exit 1
    }
}

# 4c. tests/ 目录递归复制（排除 __pycache__）
$testsDir = Join-Path $mcpSrc "tests"
$testsDst = Join-Path $mcpDst "tests"
if (Test-Path $testsDir) {
    $rc = robocopy $testsDir $testsDst /E /XD __pycache__ .pytest_cache /XF *.pyc /NFL /NDL /NJH /NJS /NP
    if ($LASTEXITCODE -ge 8) {
        Write-Err "robocopy failed for tests with exit code $LASTEXITCODE"
        exit 1
    }
}

# 4d. data/ 目录：只创建 .gitkeep 占位文件（不复制用户数据）
$dataKeepFiles = @(
    "vocabs\.gitkeep",
    "reviews\.gitkeep",
    "quizzes\.gitkeep",
    "exports\.gitkeep",
    "images\.gitkeep"
)
foreach ($kf in $dataKeepFiles) {
    $srcKeep = Join-Path $mcpSrc "data\$kf"
    $dstKeep = Join-Path $mcpDst "data\$kf"
    if (Test-Path $srcKeep) {
        Copy-Item $srcKeep $dstKeep -Force
    } else {
        # 源没有 .gitkeep 也创建一个空占位
        New-Item -ItemType File -Path $dstKeep -Force | Out-Null
    }
}
Write-Ok "source copied"

# ──────────────────────────────────────────
# [5/6] 复制顶层文档和安装脚本
# ──────────────────────────────────────────
Write-Step "[5/6] Copy docs and install scripts..."
$topFiles = @("install.ps1", "install.sh", "README.md", "DEPLOY.md", "QUICKSTART.md", "LICENSE", "AGENTS.md", ".workbuddy/README.md", ".hermes/README.md")
# AGENTS.md 的真相源是 vocabcraft.plugin/AGENTS.md（同步生成根目录 AGENTS.md，供 Trae 使用）
foreach ($f in $topFiles) {
    $srcName = if ($f -eq "AGENTS.md") { "vocabcraft.plugin\AGENTS.md" } else { $f }
    $src = Join-Path $projectRoot $srcName
    if (Test-Path $src) {
        $dst = Join-Path $tempDir $f
        $parent = Split-Path $dst -Parent
        if (-not (Test-Path $parent)) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
        Copy-Item $src $dst -Force
    }
}
Write-Ok "docs copied"

# ──────────────────────────────────────────
# [6/6] 验证关键文件 + 打包
# ──────────────────────────────────────────
Write-Step "[6/6] Verify and pack..."

# 验证关键文件存在（四个平台配置均来自 AAIF 真相源，需全部齐备）
$requiredFiles = @(
    "AGENTS.md",
    "vocabcraft.plugin\AGENTS.md",
    ".trae\mcp.json",
    ".opencode\opencode.json",
    ".codebuddy\mcp.json",
    ".goose\config.yaml",
    ".trae\skills",
    ".opencode\skills",
    ".codebuddy\skills",
    ".goose\skills",
    "vocabcraft.plugin/vocabcraft-mcp\pyproject.toml",
    "vocabcraft.plugin/vocabcraft-mcp\src\vocabcraft_mcp\server.py",
    "install.ps1",
    "install.sh",
    "README.md"
)

$missing = @()
foreach ($rf in $requiredFiles) {
    $fullPath = Join-Path $tempDir $rf
    if (!(Test-Path $fullPath)) {
        $missing += $rf
    }
}

if ($missing.Count -gt 0) {
    Write-Err "Missing required files:"
    $missing | ForEach-Object { Write-Err "  $_" }
    exit 1
}

# 验证没有误包含 .venv
$venvCheck = Join-Path $tempDir "vocabcraft.plugin/vocabcraft-mcp\.venv"
if (Test-Path $venvCheck) {
    Write-Err ".venv was accidentally included! Aborting."
    exit 1
}

# 统计文件数
$fileCount = (Get-ChildItem $tempDir -Recurse -File | Measure-Object).Count
Write-Ok "verified ($fileCount files, no .venv)"

# 打包为 zip（Windows 通用，Compress-Archive）
if (Test-Path $zipPath) { Remove-Item $zipPath -Force }
Compress-Archive -Path $tempDir -DestinationPath $zipPath -Force

$zipItem = Get-Item $zipPath
$zipSizeMB = [math]::Round($zipItem.Length / 1MB, 2)
Write-Ok "packed: $zipPath ($zipSizeMB MB)"

# 打包为 tar.gz（Windows 10+ 内置 bsdtar，兼容性最好）
if (Test-Path $gzPath) { Remove-Item $gzPath -Force }
& tar -C $distDir -czf $gzPath $packageName
if ($LASTEXITCODE -eq 0) {
    $gzItem = Get-Item $gzPath
    $gzSizeMB = [math]::Round($gzItem.Length / 1MB, 2)
    Write-Ok "packed: $gzPath ($gzSizeMB MB)"
} else {
    Write-Err "tar.gz packing failed (tar exit $LASTEXITCODE)"
}



# ──────────────────────────────────────────
# 清理临时目录
# ──────────────────────────────────────────
try {
    [System.IO.Directory]::Delete($tempDir, $true)
} catch {
    # 长路径兜底
    $emptyTmp2 = Join-Path $env:TEMP "vc_empty2_$(Get-Random)"
    New-Item -ItemType Directory -Path $emptyTmp2 -Force | Out-Null
    robocopy $emptyTmp2 $tempDir /MIR /R:0 /W:0 /NFL /NDL /NJH /NJS /NP | Out-Null
    [System.IO.Directory]::Delete($tempDir, $true)
    Remove-Item -Recurse -Force $emptyTmp2 -ErrorAction SilentlyContinue
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Build complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Artifacts:" -ForegroundColor Cyan
Write-Host "    $zipPath ($zipSizeMB MB)" -ForegroundColor Cyan
if (Test-Path $gzPath) { Write-Host "    $gzPath" -ForegroundColor Cyan }
Write-Host "  Files:    $fileCount" -ForegroundColor Cyan
Write-Host ""
Write-Host "  User steps (支持的运行时: Trae IDE CN / Trae Work CN / CodeBuddy / OpenCode / Goose):" -ForegroundColor White
Write-Host "  1. Extract VocabCraft-v$Version.zip" -ForegroundColor DarkGray
Write-Host "  2. Run install.ps1 (或 Linux/macOS 下 install.sh)" -ForegroundColor DarkGray
Write-Host "  3. 在所用 IDE 中打开该文件夹，启用项目级 MCP 即可" -ForegroundColor DarkGray
Write-Host ""
