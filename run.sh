#!/bin/bash
# EVDP Docker 一键启动脚本（Linux / macOS / WSL）
# 用法: bash run.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE_NAME="evdp:latest"
CONTAINER_NAME="evdp"
PORT=8501

# ── 颜色输出 ────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# ── 检测 Docker 是否安装 ───────────────────────────────────
check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装，请先安装 Docker"
        echo ""
        echo "  官方安装指南:https://docs.docker.com/get-docker/"
        echo "  Windows 用户:安装 Docker Desktop（需要 WSL2）"
        echo "  Linux 用户：  sudo apt install docker.io"
        exit 1
    fi
    if ! docker info &> /dev/null; then
        log_error "Docker 服务未启动，请先启动 Docker Desktop"
        exit 1
    fi
}

# ── 构建镜像 ────────────────────────────────────────────────
build_image() {
    if docker images "$IMAGE_NAME" -q | grep -q .; then
        log_info "镜像已存在，跳过构建（删除旧镜像请运行: docker rmi $IMAGE_NAME）"
    else
        log_info "正在构建镜像（首次可能需要几分钟）..."
        docker build -t "$IMAGE_NAME" "$SCRIPT_DIR"
        log_info "镜像构建完成"
    fi
}

# ── 停止并删除旧容器 ────────────────────────────────────────
cleanup_container() {
    if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        log_warn "旧容器存在，正在停止并删除..."
        docker stop "$CONTAINER_NAME" &> /dev/null || true
        docker rm "$CONTAINER_NAME" &> /dev/null || true
    fi
}

# ── 启动容器 ────────────────────────────────────────────────
start_container() {
    log_info "正在启动容器..."
    docker run -d \
        --name "$CONTAINER_NAME" \
        -p "${PORT}:8501" \
        -v "${SCRIPT_DIR}/data:/home/EVDP/data" \
        -v "${SCRIPT_DIR}/assets:/home/EVDP/assets" \
        -e "TZ=Asia/Shanghai" \
        "$IMAGE_NAME"

    sleep 2

    if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        log_info " EVDP 启动成功！"
        echo ""
        echo "  访问地址: http://localhost:${PORT}"
        echo "  查看日志: docker logs -f $CONTAINER_NAME"
        echo "  停止服务: docker stop $CONTAINER_NAME"
        echo ""
    else
        log_error "容器启动失败，请运行以下命令查看原因:"
        echo "  docker logs $CONTAINER_NAME"
        exit 1
    fi
} 

# ── 主流程 ─────────────────────────────────────────────────
main() {
    echo ""
    echo " ╔══════════════════════════════════════╗"
    echo " ║       EVDP Docker 启动脚本            ║"
    echo " ╚══════════════════════════════════════╝"
    echo ""

    check_docker
    cleanup_container
    build_image
    start_container
}

main "$@"
