# EVDP 本地开发环境安装脚本（PowerShell / Windows）
# 自动创建虚拟环境并安装所有依赖
# 用法: .\setup.ps1

param(
    [string]$VenvDir = "$PSScriptRoot\venv"
)

$ErrorActionPreference = "Stop"

function Write-Info($msg)  { Write-Host "[INFO] $msg" -ForegroundColor Green }
function Write-Warn($msg)  { Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-Err($msg)   { Write-Host "[ERROR] $msg" -ForegroundColor Red }

# ── 检测 Python ─────────────────────────────────────────────
function Test-PythonInstalled {
    try {
        $version = python --version 2>$null
        if (-not $version) { $version = python3 --version 2>$null }
        if (-not $version) { throw }
        Write-Info "检测到 $version"
    } catch {
        Write-Err "未找到 Python，请先安装 Python 3.9+"
        Write-Host "  下载地址: https://www.python.org/downloads/"
        exit 1
    }
}

# ── 安装 playwright 系统依赖（Windows 通过 Chocolatey 或手动）──
function Install-PlaywrightDeps {
    Write-Info "检查 Chromium 浏览器..."
    try {
        playwright install chromium 2>$null
        Write-Info "Chromium 安装完成"
    } catch {
        Write-Warn "playwright install 失败，请确保 playwright 已正确安装"
    }
}

# ── 创建虚拟环境 ────────────────────────────────────────────
function New-LocalVenv {
    if (Test-Path $VenvDir) {
        Write-Warn "虚拟环境已存在，跳过创建"
    } else {
        Write-Info "创建虚拟环境..."
        python -m venv $VenvDir
        Write-Info "虚拟环境创建完成: $VenvDir"
    }
}

# ── 安装 Python 依赖 ───────────────────────────────────────
function Install-Dependencies {
    $pip = Join-Path $VenvDir "Scripts\pip.exe"
    if (-not (Test-Path $pip)) {
        Write-Err "虚拟环境 pip 未找到，请检查虚拟环境是否创建成功"
        exit 1
    }

    Write-Info "升级 pip..."
    & $pip install --quiet --upgrade pip

    Write-Info "安装项目依赖（可能需要几分钟）..."
    & $pip install --quiet -r "$PSScriptRoot\requirements.txt"

    Install-PlaywrightDeps

    Write-Info "依赖安装完成"
}

# ── 检查 assets 目录 ───────────────────────────────────────
function Test-AssetsDirectory {
    $assetsDir = Join-Path $PSScriptRoot "assets"
    if (-not (Test-Path "$assetsDir\fonts")) {
        Write-Warn "assets/fonts 目录不存在，请确保字体文件已放置"
    }
    if (-not (Test-Path "$assetsDir\sensitive_words")) {
        Write-Warn "敏感词库目录 assets/sensitive_words 不存在，请检查资源文件"
    }
}

# ── 主流程 ─────────────────────────────────────────────────
Write-Host ""
Write-Host "  EVDP 本地开发环境安装脚本"
Write-Host ""

Test-PythonInstalled
New-LocalVenv
Install-Dependencies
Test-AssetsDirectory

Write-Host ""
Write-Host "  安装完成！"
Write-Host ""
Write-Host "  启动方式:"
Write-Host "    1. 激活虚拟环境: $VenvDir\Scripts\Activate.ps1"
Write-Host "    2. 启动 EVDP:    streamlit run app.py"
Write-Host ""
Write-Host "  或一键启动:"
Write-Host "    $VenvDir\Scripts\streamlit.exe run app.py"
Write-Host ""
