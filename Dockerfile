# ============================================
# 阶段一：构建前端
# ============================================
FROM node:22-alpine AS frontend-builder
WORKDIR /app/frontend

# 安装依赖
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci --registry=https://registry.npmmirror.com

# 构建
COPY frontend/ ./
RUN npm run build -- --emptyOutDir

# ============================================
# 阶段二：构建后端运行镜像
# ============================================
FROM python:3.13-alpine AS backend
WORKDIR /app

# 安装系统依赖
RUN apk add --no-cache tzdata && \
    cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && \
    echo "Asia/Shanghai" > /etc/timezone

# 安装 Python 依赖
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

# 复制后端代码
COPY backend/ ./

# 复制前端构建产物到 Flask 的静态文件目录
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# 创建数据目录
RUN mkdir -p /app/data/logs

# 暴露端口
EXPOSE 5000

# 健康检查
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')" || exit 1

# 使用 waitress 作为生产 WSGI 服务器
CMD ["waitress-serve", "--host=0.0.0.0", "--port=5000", "--threads=4", "app:create_app()"]
