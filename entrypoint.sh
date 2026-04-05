#!/bin/bash
# EVDP 容器启动脚本（entrypoint.sh）
# 在容器启动时自动初始化字体缓存，解决 matplotlib 中文字体问题

set -e

FONT_DIR="/home/EVDP/assets/fonts"
FONT_CACHE_DIR="/root/.cache/matplotlib"

# 如果有字体目录，刷新 matplotlib 字体缓存
if [ -d "$FONT_DIR" ]; then
    echo "[EVDP] 刷新 matplotlib 字体缓存..."
    rm -rf "$FONT_CACHE_DIR"
fi

echo "[EVDP] 启动 Streamlit 服务..."
exec streamlit run app.py \
    --server.port 8501 \
    --server.address 0.0.0.0 \
    --server.headless true
