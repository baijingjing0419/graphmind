# GraphMind API - 后端镜像
#
# 构建: docker compose build api
# 运行: docker compose up

FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    ENVIRONMENT=production

WORKDIR /app

# 配置 pip 镜像源（国内加速）
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip config set global.trusted-host pypi.tuna.tsinghua.edu.cn

# 安装系统依赖
RUN apt-get update && \
    apt-get install -y --no-install-recommends --fix-missing \
        git \
        libjpeg-dev \
        zlib1g-dev \
        libreoffice \
        libreoffice-writer \
    && rm -rf /var/lib/apt/lists/*

# 复制并安装 PaddleOCR（可选，不存在则跳过）
COPY vendor/ ./vendor/
COPY requirements.txt .

RUN if [ -f "./vendor/PaddleOCR/setup.py" ] || [ -f "./vendor/PaddleOCR/pyproject.toml" ]; then \
        echo "安装 PaddleOCR..."; \
        pip install -e ./vendor/PaddleOCR; \
    else \
        echo "PaddleOCR 未找到，跳过安装（OCR 功能不可用）"; \
    fi && \
    pip install -r requirements.txt

# 复制应用代码
COPY agents/ ./agents/
COPY chunking/ ./chunking/
COPY database/ ./database/
COPY embedding/ ./embedding/
COPY middleware/ ./middleware/
COPY models/ ./models/
COPY parsers/ ./parsers/
COPY retrieval/ ./retrieval/
COPY routers/ ./routers/
COPY services/ ./services/
COPY utils/ ./utils/
COPY main.py ./

# 运行时目录
RUN mkdir -p /app/uploads /app/conversation_uploads /app/logs && \
    chmod -R 755 /app/uploads /app/conversation_uploads /app/logs

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health/liveness').read()" || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
