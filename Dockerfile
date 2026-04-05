# EVDP Dockerfile
# 基于 playwright 官方镜像，内置 Python + Chromium
FROM mcr.microsoft.com/playwright/python:v1.49.0-noble

# 保持与代码中硬编码路径一致，避免大量修改
WORKDIR /home/EVDP

# 复制 requirements.txt（先复制，Docker 缓存优化）
COPY requirements.txt .

# 安装 Python 依赖（playwright 包自带 CLI）
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 安装 Chromium 浏览器（playwright 是 Python 包，必须用 python -m 调用）
RUN python -m playwright install --with-deps chromium

# 复制其余项目文件
COPY . .

EXPOSE 8501

# 启动脚本处理环境初始化，再启动 Streamlit
ENTRYPOINT ["bash", "entrypoint.sh"]
