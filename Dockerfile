FROM mcr.microsoft.com/playwright/python:v1.49.0-noble

WORKDIR /app

# 复制所有文件
COPY . .

# 升级 pip 并安装依赖
# 使用 --use-pep517 增加安装成功率
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

EXPOSE 8501

# 启动
CMD ["streamlit", "run", "app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]