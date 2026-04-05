#!/bin/bash
# EVDP 本地开发环境安装脚本（Linux / macOS / WSL）
# 自动创建虚拟环境并安装所有依赖
# 用法: bash setup.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"

# ── 颜色输出 ────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log_info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# ── 检测 Python ─────────────────────────────────────────────
check_python() {
    if ! command -v python3 &> /dev/null; then
        log_error "未找到 python3，请先安装 Python 3.9+"
        echo "  Ubuntu/Debian: sudo apt install python3 python3-venv python3-pip"
        echo "  macOS:         brew install python"
        exit 1
    fi
    PY_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    log_info "检测到 Python $PY_VERSION"
}

# ── 安装系统依赖（Linux）─────────────────────────────────────
install_system_deps() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if command -v apt-get &> /dev/null; then
            log_info "安装系统依赖（chromium-browser 等）..."
            sudo apt-get update -qq
            sudo apt-get install -y -qq \
                chromium chromium-driver \
                libglib2.0-0 libnss3 libnspr4 libdbus-1-3 \
                libatk1.0-0 libatk-bridge2.0-0 libcups2 \
                libdrm2 libxkbcommon0 libxcomposite1 \
                libxdamage1 libxfixes3 libxrandr2 \
                libgbm1 libasound2 libpango-1.0-0 libcairo2 2>/dev/null || true
        fi
    fi
}

# ── 创建虚拟环境 ────────────────────────────────────────────
setup_venv() {
    if [ -d "$VENV_DIR" ]; then
        log_warn "虚拟环境已存在，跳过创建"
    else
        log_info "创建虚拟环境..."
        python3 -m venv "$VENV_DIR"
        log_info "虚拟环境创建完成: $VENV_DIR"
    fi
}

# ── 安装 Python 依赖 ────────────────────────────────────────
install_deps() {
    log_info "激活虚拟环境..."
    source "$VENV_DIR/bin/activate"

    log_info "升级 pip..."
    pip install --quiet --upgrade pip

    log_info "安装项目依赖（可能需要几分钟）..."
    pip install --quiet -r "$SCRIPT_DIR/requirements.txt"

    # 安装 playwright 浏览器（必须）
    log_info "安装 Chromium 浏览器..."
    playwright install --with-deps chromium 2>/dev/null || playwright install chromium || true

    log_info "依赖安装完成"
}

# ── 初始化 assets 目录 ─────────────────────────────────────
init_assets() {
    ASSETS_DIR="$SCRIPT_DIR/assets"
    if [ ! -d "$ASSETS_DIR/fonts" ]; then
        log_warn "assets/fonts 目录不存在，请确保字体文件已放置在 assets/fonts/ 下"
    fi
    if [ ! -d "$ASSETS_DIR/sensitive_words" ]; then
        log_warn "敏感词库目录 assets/sensitive_words 不存在，请检查资源文件"
    fi
}

# ── 主流程 ─────────────────────────────────────────────────
main() {
    echo ""
    echo " ╔════════════════════════════════════════╗"
    echo " ║    EVDP 本地开发环境安装脚本             ║"
    echo " ╚════════════════════════════════════════╝"
    echo ""

    check_python
    install_system_deps
    setup_venv
    install_deps
    init_assets

    echo ""
    echo " ╔════════════════════════════════════════╗"
    echo " ║           安装完成!                     ║"
    echo " ╚════════════════════════════════════════╝"
    echo ""
    echo "  启动方式:"
    echo "    1. 激活虚拟环境: source $VENV_DIR/bin/activate"
    echo "    2. 启动 EVDP:    streamlit run app.py"
    echo ""
    echo "  或一键启动:"
    echo "    $VENV_DIR/bin/streamlit run app.py"
    echo ""
}

main "$@"
