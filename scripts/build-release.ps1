# VocabCraft 发布包构建脚本
# 从源码生成可分发的 zip 包（白名单复制策略，避免误打包 .venv）
#
# 使用方法：
#   pwsh .\scripts\build-release.ps1 [-Version "0.3.0"]
#
# 输出：
#   dist\VocabCraft-v0.3.0.zip

param(
    [string]$Version = "0.3.0"
)

$ErrorActionPreference = "Stop"

# ──────────────────────────────────────────
# 路径定义
# ──────────────────────────────────────────
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$distDir = Join-Path $projectRoot "dist"
$packageName = "VocabCraft-v$Version"
$tempDir = Join-Path $distDir $packageName
$zipPath = Join-Path $distDir "$packageName.zip"
$gzPath = Join-Path $distDir "$packageName.tar.gz"
$zstPath = Join-Path $distDir "$packageName.tar.zst"

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
# .trae 子目录（与 BMAD 共存：agents/commands/skills/rules）
New-Item -ItemType Directory -Path (Join-Path $tempDir ".trae\rules") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $tempDir ".trae\skills") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $tempDir ".trae\agents") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $tempDir ".trae\commands") -Force | Out-Null
# vocabcraft-mcp 子目录
New-Item -ItemType Directory -Path (Join-Path $tempDir "vocabcraft-mcp\src") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $tempDir "vocabcraft-mcp\data\vocabs") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $tempDir "vocabcraft-mcp\data\reviews") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $tempDir "vocabcraft-mcp\data\quizzes") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $tempDir "vocabcraft-mcp\data\exports") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $tempDir "vocabcraft-mcp\data\images") -Force | Out-Null
Write-Ok "directories created"

# ──────────────────────────────────────────
# [3/6] 复制 .trae 配置（白名单，仅 vocabcraft-* 业务文件 + 顶层配置）
# ──────────────────────────────────────────
Write-Step "[3/6] Copy .trae config..."

# .trae 顶层文件
# 注意：源 .trae/mcp.json 受 Trae 保护，可能包含硬编码的绝对路径 cwd。
# 发布包必须使用 ${workspaceFolder} 变量版本，因此在构建时覆盖写入正确内容。
$traeTopFiles = @("hooks.json")
foreach ($f in $traeTopFiles) {
    $src = Join-Path $projectRoot ".trae\$f"
    if (Test-Path $src) {
        Copy-Item $src (Join-Path $tempDir ".trae\$f") -Force
    }
}

# 写入发布版 mcp.json（使用 ${workspaceFolder} 变量，解压到任意位置均可工作）
# 双环境（TRAEWORK CN + TRAEIDE CN）共用此配置
$releaseMcpJson = @'
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
'@
$releaseMcpJson | Set-Content -Path (Join-Path $tempDir ".trae\mcp.json") -Encoding UTF8 -NoNewline

# 辅助函数：复制目录下所有以 vocabcraft- 前缀开头的子项（文件或目录）
# 与 BMAD 共存策略：只打包业务文件，不打包 BMAD 文件
function Copy-VocabcraftPrefixedItems {
    param(
        [string]$srcDir,
        [string]$dstDir,
        [bool]$isDirectory
    )
    if (!(Test-Path $srcDir)) { return }
    Get-ChildItem $srcDir | Where-Object {
        $_.Name -like "vocabcraft-*" -and (($isDirectory -and $_.PSIsContainer) -or (-not $isDirectory -and -not $_.PSIsContainer))
    } | ForEach-Object {
        if ($isDirectory) {
            # 目录递归复制（排除 __pycache__ / .pytest_cache）
            $childDst = Join-Path $dstDir $_.Name
            New-Item -ItemType Directory -Path $childDst -Force | Out-Null
            $rc = robocopy $_.FullName $childDst /E /XD __pycache__ .pytest_cache /XF *.pyc /NFL /NDL /NJH /NJS /NP
            if ($LASTEXITCODE -ge 8) {
                Write-Err "robocopy failed for $($_.FullName) with exit code $LASTEXITCODE"
                exit 1
            }
        } else {
            Copy-Item $_.FullName (Join-Path $dstDir $_.Name) -Force
        }
    }
}

# .trae/skills/ 只复制 vocabcraft-* 前缀的 skill 目录
Copy-VocabcraftPrefixedItems -srcDir (Join-Path $projectRoot ".trae\skills") -dstDir (Join-Path $tempDir ".trae\skills") -isDirectory $true

Write-Ok ".trae config copied (skills only, rules/agents/commands migrated to AGENTS.md)"

# ──────────────────────────────────────────
# [4/6] 复制 vocabcraft-mcp 源码（白名单）
# ──────────────────────────────────────────
Write-Step "[4/6] Copy vocabcraft-mcp source..."

$mcpSrc = Join-Path $projectRoot "vocabcraft-mcp"
$mcpDst = Join-Path $tempDir "vocabcraft-mcp"

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
$topFiles = @("install.ps1", "install.sh", "README.md", "DEPLOY.md", "QUICKSTART.md", "LICENSE", "AGENTS.md")
foreach ($f in $topFiles) {
    $src = Join-Path $projectRoot $f
    if (Test-Path $src) {
        Copy-Item $src (Join-Path $tempDir $f) -Force
    }
}
Write-Ok "docs copied"

# ──────────────────────────────────────────
# [6/6] 验证关键文件 + 打包
# ──────────────────────────────────────────
Write-Step "[6/6] Verify and pack..."

# 验证关键文件存在（关键 .trae 文件可能因前缀过滤而不存在，故只验必备项）
$requiredFiles = @(
    ".trae\mcp.json",
    "vocabcraft-mcp\pyproject.toml",
    "vocabcraft-mcp\src\vocabcraft_mcp\server.py",
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
$venvCheck = Join-Path $tempDir "vocabcraft-mcp\.venv"
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

# 打包为 tar.zst（推荐，体积最小；需 zstd 可用，不可用时跳过，CI 会在 Linux 上产出）
if (Get-Command zstd -ErrorAction SilentlyContinue) {
    if (Test-Path $zstPath) { Remove-Item $zstPath -Force }
    # 先打 tar 再用 zstd 压缩（避免 PowerShell 管道传字节的编码问题）
    $tempTar = Join-Path $env:TEMP "vc_build_$(Get-Random).tar"
    & tar -C $distDir -cf $tempTar $packageName
    if ($LASTEXITCODE -eq 0) {
        & zstd -3 -q -f $tempTar -o $zstPath
        if ($LASTEXITCODE -eq 0) {
            $zstItem = Get-Item $zstPath
            $zstSizeMB = [math]::Round($zstItem.Length / 1MB, 2)
            Write-Ok "packed: $zstPath ($zstSizeMB MB)"
        } else {
            Write-Err "tar.zst packing failed (zstd exit $LASTEXITCODE)"
        }
    } else {
        Write-Err "tar.zst: tar step failed (exit $LASTEXITCODE)"
    }
    Remove-Item $tempTar -Force -ErrorAction SilentlyContinue
} else {
    Write-Host "[skip]  zstd not found, skipping tar.zst (CI produces it on Linux)" -ForegroundColor DarkGray
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
if (Test-Path $zstPath) { Write-Host "    $zstPath" -ForegroundColor Cyan }
Write-Host "  Files:    $fileCount" -ForegroundColor Cyan
Write-Host ""
Write-Host "  User steps (TRAEWORK CN / TRAEIDE CN 均适用):" -ForegroundColor White
Write-Host "  1. Extract VocabCraft-v$Version.zip" -ForegroundColor DarkGray
Write-Host "  2. Run install.ps1" -ForegroundColor DarkGray
Write-Host "  3. Open folder in Trae, enable project-level MCP" -ForegroundColor DarkGray
Write-Host "  4. Repeat step 3 in the other Trae env for dual-env setup" -ForegroundColor DarkGray
Write-Host ""
