# EVDP Docker 一键启动脚本（PowerShell / Windows）
# 用法: .\run.ps1

param(
    [string]$ImageName = "evdp:latest",
    [string]$ContainerName = "evdp",
    [int]$Port = 8501
)

$ErrorActionPreference = "Stop"
$ScriptDir = $PSScriptRoot

function Write-Info($msg)  { Write-Host "[INFO] $msg" -ForegroundColor Green }
function Write-Warn($msg)  { Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-Err($msg)   { Write-Host "[ERROR] $msg" -ForegroundColor Red }

# ── 检测 Docker 是否安装 ───────────────────────────────────
function Test-DockerInstalled {
    try {
        $null = Get-Command docker -ErrorAction Stop
    } catch {
        Write-Err "Docker 未安装，请先安装 Docker Desktop"
        Write-Host ""
        Write-Host "  官方下载: https://www.docker.com/products/docker-desktop/"
        exit 1
    }
}

function Test-DockerRunning {
    try {
        docker info 2>$null | Out-Null
    } catch {
        Write-Err "Docker 服务未启动，请先启动 Docker Desktop"
        exit 1
    }
}

# ── 构建镜像 ────────────────────────────────────────────────
function Build-Image {
    $existing = $(docker images -q $ImageName 2>$null)
    if ($existing) {
        Write-Info "镜像已存在，跳过构建（删除旧镜像请运行: docker rmi $ImageName）"
    } else {
        Write-Info "正在构建镜像（首次可能需要几分钟）..."
        docker build -t $ImageName $ScriptDir
        Write-Info "镜像构建完成"
    }
}

# ── 清理旧容器 ────────────────────────────────────────────
function Remove-OldContainer {
    $running = docker ps -a --format '{{.Names}}' | Where-Object { $_ -eq $ContainerName }
    if ($running) {
        Write-Warn "旧容器存在，正在停止并删除..."
        docker stop $ContainerName 2>$null | Out-Null
        docker rm $ContainerName 2>$null | Out-Null
    }
}

# ── 启动容器 ──────────────────────────────────────────────
function Start-EVDPContainer {
    Write-Info "正在启动容器..."

    $dataPath   = Join-Path $ScriptDir "data"
    $assetsPath = Join-Path $ScriptDir "assets"
    if (-not (Test-Path $dataPath))   { New-Item -ItemType Directory -Path $dataPath   | Out-Null }
    if (-not (Test-Path $assetsPath)) { New-Item -ItemType Directory -Path $assetsPath | Out-Null }

    docker run -d `
        --name $ContainerName `
        -p "${Port}:8501" `
        -v "${dataPath}:/home/EVDP/data" `
        -v "${assetsPath}:/home/EVDP/assets" `
        -e "TZ=Asia/Shanghai" `
        $ImageName

    Start-Sleep -Seconds 2

    $running = docker ps --format '{{.Names}}' | Where-Object { $_ -eq $ContainerName }
    if ($running) {
        Write-Info "EVDP 启动成功！"
        Write-Host ""
        Write-Host "  访问地址: http://localhost:${Port}"
        Write-Host "  查看日志: docker logs -f $ContainerName"
        Write-Host "  停止服务: docker stop $ContainerName"
        Write-Host ""
    } else {
        Write-Err "容器启动失败，请运行以下命令查看原因:"
        Write-Host "  docker logs $ContainerName"
        exit 1
    }
}

# ── 主流程 ─────────────────────────────────────────────────
Write-Host ""
Write-Host "  EVDP Docker 启动脚本"
Write-Host ""

Test-DockerInstalled
Test-DockerRunning
Remove-OldContainer
Build-Image
Start-EVDPContainer
