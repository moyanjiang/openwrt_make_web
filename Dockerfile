# OpenWrt编译器 - 优化版Docker镜像
FROM ubuntu:22.04

# 设置环境变量
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Asia/Shanghai
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PORT=8000
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

# 设置工作目录
WORKDIR /app

# 设置时区
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 安装系统依赖 - 分层优化
RUN apt-get update && apt-get install -y \
    # Python环境
    python3 python3-pip python3-venv python3-dev python3-setuptools python3-wheel \
    # 基础构建工具
    build-essential gcc g++ make cmake autoconf automake libtool \
    # 版本控制
    git subversion mercurial bzr \
    # 网络工具
    curl wget rsync aria2 \
    # 压缩工具
    unzip zip gzip bzip2 xz-utils \
    # 系统工具
    vim nano htop tree iputils-ping netcat-openbsd tzdata ca-certificates \
    # 监控工具
    supervisor \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# 安装OpenWrt编译专用依赖
RUN apt-get update && apt-get install -y \
    # OpenWrt核心依赖
    libncurses5-dev libncursesw5-dev zlib1g-dev gawk gettext libssl-dev \
    xsltproc fastjar file java-propose-classpath libelf-dev \
    # 编译工具
    swig ecj libtinfo5 \
    # 数学库
    libgmp3-dev libmpc-dev libmpfr-dev libgmp-dev \
    # USB支持
    libusb-1.0-0-dev libusb-dev \
    # 其他库
    liblzma-dev libsnmp-dev libevent-dev libavahi-client-dev \
    libsqlite3-dev libpcre2-dev \
    # ccache编译加速
    ccache \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# 创建应用用户和组
RUN groupadd -r openwrt && \
    useradd -r -g openwrt -u 1000 -m -s /bin/bash openwrt && \
    usermod -aG sudo openwrt && \
    echo "openwrt ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# 配置ccache
RUN mkdir -p /app/ccache && \
    ccache --set-config=cache_dir=/app/ccache && \
    ccache --set-config=max_size=10G && \
    ccache --set-config=compression=true && \
    chown -R openwrt:openwrt /app/ccache

# 复制requirements文件并安装Python依赖
COPY requirements.txt /app/
RUN python3 -m pip install --upgrade pip setuptools wheel && \
    python3 -m pip install --no-cache-dir -r requirements.txt

# 创建目录结构
RUN mkdir -p \
    /app/workspace/users \
    /app/workspace/shared/cache \
    /app/workspace/shared/downloads \
    /app/workspace/shared/ccache \
    /app/logs/compile \
    /app/logs/system \
    /app/logs/access \
    /app/data/configs \
    /app/data/firmware \
    /app/data/uploads \
    /app/tmp \
    /app/cache \
    /app/downloads \
    /etc/openwrt-compiler

# 复制应用代码
COPY backend/ /app/backend/
COPY frontend/ /app/frontend/
COPY config/ /app/config/
COPY scripts/ /app/scripts/

# 复制Docker配置文件
COPY docker/ /app/docker/

# 创建启动脚本
RUN echo '#!/bin/bash' > /app/entrypoint.sh && \
    echo 'set -e' >> /app/entrypoint.sh && \
    echo '' >> /app/entrypoint.sh && \
    echo '# 初始化日志' >> /app/entrypoint.sh && \
    echo 'mkdir -p /app/logs/system' >> /app/entrypoint.sh && \
    echo 'echo "$(date): Starting OpenWrt Compiler..." >> /app/logs/system/startup.log' >> /app/entrypoint.sh && \
    echo '' >> /app/entrypoint.sh && \
    echo '# 设置权限' >> /app/entrypoint.sh && \
    echo 'chown -R openwrt:openwrt /app/workspace /app/logs /app/data /app/tmp 2>/dev/null || true' >> /app/entrypoint.sh && \
    echo '' >> /app/entrypoint.sh && \
    echo '# 初始化ccache' >> /app/entrypoint.sh && \
    echo 'export CCACHE_DIR=/app/ccache' >> /app/entrypoint.sh && \
    echo 'export PATH="/usr/lib/ccache:$PATH"' >> /app/entrypoint.sh && \
    echo '' >> /app/entrypoint.sh && \
    echo '# 启动应用' >> /app/entrypoint.sh && \
    echo 'if [ "$1" = "python3" ]; then' >> /app/entrypoint.sh && \
    echo '    exec "$@"' >> /app/entrypoint.sh && \
    echo 'else' >> /app/entrypoint.sh && \
    echo '    exec python3 /app/backend/app.py --host 0.0.0.0 --port ${PORT:-8000}' >> /app/entrypoint.sh && \
    echo 'fi' >> /app/entrypoint.sh

# 设置权限
RUN chmod +x /app/entrypoint.sh && \
    chown -R openwrt:openwrt /app && \
    chmod 755 /app/workspace /app/logs /app/data && \
    chmod 777 /app/tmp

# 创建健康检查脚本
RUN echo '#!/bin/bash\ncurl -f http://localhost:${PORT:-8000}/health || exit 1' > /healthcheck.sh && \
    chmod +x /healthcheck.sh

# 暴露端口
EXPOSE $PORT

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD /healthcheck.sh

# 数据卷
VOLUME ["/app/workspace", "/app/logs", "/app/data", "/app/ccache"]

# 切换到应用用户
USER openwrt

# 设置环境变量
ENV PATH="/usr/lib/ccache:$PATH"
ENV CCACHE_DIR="/app/ccache"

# 启动命令
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["python3", "/app/backend/app.py", "--host", "0.0.0.0", "--port", "8000"]
