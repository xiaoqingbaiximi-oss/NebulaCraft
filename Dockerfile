# NebulaCraft v7.0 - 增强版 Dockerfile
# 多阶段构建，减小镜像体积

# ===== 构建阶段 =====
FROM python:3.12-slim AS builder

WORKDIR /app

# 安装构建依赖
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# 复制依赖文件并安装
COPY requirements.txt ./
RUN pip install --no-cache-dir --user -r requirements.txt

# ===== 运行阶段 =====
FROM python:3.12-slim

# 添加非 root 用户
RUN groupadd -r nebulacraft && useradd -r -g nebulacraft -m -s /bin/bash nebulacraft

WORKDIR /app

# 从构建阶段复制 Python 包
COPY --from=builder /root/.local /home/nebulacraft/.local

# 安装运行时依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 复制应用代码
COPY --chown=nebulacraft:nebulacraft server/ ./server/
COPY --chown=nebulacraft:nebulacraft css/ ./css/
COPY --chown=nebulacraft:nebulacraft js/ ./js/
COPY --chown=nebulacraft:nebulacraft locales/ ./locales/
COPY --chown=nebulacraft:nebulacraft static/ ./static/
COPY --chown=nebulacraft:nebulacraft index.html sw.js manifest.json ./

# 创建数据目录
RUN mkdir -p data/output data/shares data/notes data/more \
    && chown -R nebulacraft:nebulacraft data/

# 设置环境变量
ENV PATH="/home/nebulacraft/.local/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8889 \
    MODEL=qwen2.5:1.5b

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8889/health || exit 1

# 切换到非 root 用户
USER nebulacraft

EXPOSE 8889

# 启动
CMD ["python", "-m", "server.main"]