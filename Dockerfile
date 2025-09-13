# 使用官方Python 3.11镜像作为基础镜像
FROM registry-1.docker.io/library/python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安装uv包管理器
RUN pip install uv

# 先复制依赖文件
COPY pyproject.toml .
COPY requirements.txt* .

# 使用uv安装Python依赖
RUN uv pip install --system --no-cache -r pyproject.toml

# 复制项目文件
COPY src/ ./src/
COPY scripts/ ./scripts/
COPY config/ ./config/
COPY .env.template .

# 创建数据目录
RUN mkdir -p data/{keys,logs} && \
    chmod +x scripts/*.sh || true

# 创建默认查询文件（支持三种API密钥）
RUN echo '# 三种API密钥搜索查询' > data/queries.txt && \
    echo 'AIzaSy in:file' >> data/queries.txt && \
    echo '"https://openrouter.ai/api/v1" in:file' >> data/queries.txt && \
    echo '"https://api-inference.modelscope.cn/v1/" in:file' >> data/queries.txt && \
    echo '"openrouter.ai" AND "sk-or-v1-"' >> data/queries.txt && \
    echo '"api-inference.modelscope.cn" AND "ms-"' >> data/queries.txt

# 设置数据目录为卷
VOLUME ["/app/data"]

# 暴露端口（为未来的Web界面预留）
EXPOSE 8080

# 默认运行全面验证模式
CMD ["python", "-m", "src.main", "--mode", "compatible"]
