# OpenWrt编译器后端Dockerfile
FROM debian:12-slim

# 设置环境变量
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    # Python环境
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    # 编译工具链
    build-essential \
    libncurses5-dev \
    libncursesw5-dev \
    zlib1g-dev \
    gawk \
    git \
    gettext \
    libssl-dev \
    xsltproc \
    rsync \
    wget \
    unzip \
    subversion \
    mercurial \
    bzr \
    ecj \
    fastjar \
    file \
    g++ \
    java-propose-classpath \
    libelf-dev \
    python3-distutils \
    python3-setuptools \
    swig \
    aria2 \
    libtinfo5 \
    libgmp3-dev \
    libmpc-dev \
    libmpfr-dev \
    libgmp-dev \
    libusb-1.0-0-dev \
    libusb-dev \
    liblzma-dev \
    libsnmp-dev \
    libevent-dev \
    libavahi-client-dev \
    libsqlite3-dev \
    libpcre2-dev \
    # 其他工具
    curl \
    vim \
    htop \
    procps \
    && rm -rf /var/lib/apt/lists/*

# 创建非root用户
RUN useradd -m -u 1000 -s /bin/bash openwrt && \
    usermod -aG sudo openwrt && \
    echo "openwrt ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# 复制requirements文件
COPY requirements.txt .

# 安装Python依赖
RUN pip3 install --no-cache-dir -r requirements.txt

# 复制后端代码
COPY backend/ ./backend/
COPY workspace/ ./workspace/

# 设置权限
RUN chown -R openwrt:openwrt /app && \
    chmod +x backend/app.py

# 创建必要的目录
RUN mkdir -p /app/workspace/users /app/logs && \
    chown -R openwrt:openwrt /app/workspace /app/logs

# 切换到非root用户
USER openwrt

# 暴露端口
EXPOSE 5000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

# 启动命令
CMD ["python3", "backend/app.py", "--host", "0.0.0.0", "--port", "5000"]
