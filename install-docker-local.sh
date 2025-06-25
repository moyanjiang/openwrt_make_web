#!/bin/bash

# OpenWrt编译器Docker本地部署脚本
# 自动拉取项目并使用Docker本地构建部署

set -e

# 脚本版本
SCRIPT_VERSION="2.0.0-docker-local"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m'

# 默认配置
DEFAULT_PORT=9963
DEFAULT_REPO="https://github.com/moyanjiang/openwrt_make_web"
INSTALL_DIR="/opt/openwrt-compiler"
LOG_FILE="/tmp/openwrt-docker-install.log"

# 日志函数
log_info() {
    local msg="$1"
    echo -e "${BLUE}[INFO]${NC} $msg"
    echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] $msg" >> "$LOG_FILE"
}

log_success() {
    local msg="$1"
    echo -e "${GREEN}[SUCCESS]${NC} $msg"
    echo "$(date '+%Y-%m-%d %H:%M:%S') [SUCCESS] $msg" >> "$LOG_FILE"
}

log_warning() {
    local msg="$1"
    echo -e "${YELLOW}[WARNING]${NC} $msg"
    echo "$(date '+%Y-%m-%d %H:%M:%S') [WARNING] $msg" >> "$LOG_FILE"
}

log_error() {
    local msg="$1"
    echo -e "${RED}[ERROR]${NC} $msg"
    echo "$(date '+%Y-%m-%d %H:%M:%S') [ERROR] $msg" >> "$LOG_FILE"
}

log_step() {
    local msg="$1"
    echo -e "${PURPLE}[STEP]${NC} $msg"
    echo "$(date '+%Y-%m-%d %H:%M:%S') [STEP] $msg" >> "$LOG_FILE"
}

# 显示横幅
show_banner() {
    clear
    echo -e "${CYAN}"
    cat << 'EOF'
 ██████╗  ██████╗  ██████╗██╗  ██╗███████╗██████╗ 
 ██╔══██╗██╔═══██╗██╔════╝██║ ██╔╝██╔════╝██╔══██╗
 ██║  ██║██║   ██║██║     █████╔╝ █████╗  ██████╔╝
 ██║  ██║██║   ██║██║     ██╔═██╗ ██╔══╝  ██╔══██╗
 ██████╔╝╚██████╔╝╚██████╗██║  ██╗███████╗██║  ██║
 ╚═════╝  ╚═════╝  ╚═════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝
                                                   
        Docker本地部署脚本 v${SCRIPT_VERSION}
EOF
    echo -e "${NC}"
    echo -e "${GREEN}🚀 OpenWrt固件在线编译系统 - Docker本地模式${NC}"
    echo -e "${BLUE}📦 仓库地址: ${DEFAULT_REPO}${NC}"
    echo -e "${WHITE}📝 安装日志: ${LOG_FILE}${NC}"
    echo ""
}

# 显示帮助信息
show_help() {
    cat << EOF
${WHITE}OpenWrt编译器Docker本地部署脚本 v${SCRIPT_VERSION}${NC}

${CYAN}用法:${NC}
    $0 [选项]

${CYAN}选项:${NC}
    ${GREEN}-p, --port PORT${NC}         设置服务端口 (默认: $DEFAULT_PORT)
    ${GREEN}-d, --dir DIR${NC}          设置安装目录 (默认: $INSTALL_DIR)
    ${GREEN}-r, --repo URL${NC}         设置Git仓库地址 (默认: $DEFAULT_REPO)
    ${GREEN}--no-start${NC}             安装后不自动启动服务
    ${GREEN}--force${NC}                强制安装，跳过确认
    ${GREEN}--debug${NC}                启用调试模式
    ${GREEN}-h, --help${NC}             显示帮助信息

${CYAN}Docker本地模式特性:${NC}
    ${YELLOW}✅ 自动拉取项目代码${NC}
    ${YELLOW}✅ 本地构建Docker镜像${NC}
    ${YELLOW}✅ 不依赖外部Docker仓库${NC}
    ${YELLOW}✅ 完整的容器化部署${NC}
    ${YELLOW}✅ 服务编排和管理${NC}

${CYAN}示例:${NC}
    $0                          # 使用默认配置安装
    $0 -p 8080                  # 使用端口8080安装
    $0 -d /home/openwrt         # 安装到指定目录
    $0 --force                  # 强制安装

${CYAN}环境要求:${NC}
    • 系统: Debian 10+, Ubuntu 18.04+
    • 内存: 最低 4GB，推荐 8GB+
    • 磁盘: 最低 50GB，推荐 100GB+
    • Docker: 20.10+
    • Docker Compose: 2.0+

EOF
}

# 检查Docker环境
check_docker_environment() {
    log_step "检查Docker环境..."
    
    # 检查Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装，请先安装Docker"
        log_info "安装命令: curl -fsSL https://get.docker.com | sh"
        exit 1
    fi
    
    local docker_version=$(docker --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')
    log_info "Docker版本: $docker_version ✓"
    
    # 检查Docker服务
    if ! docker info &> /dev/null; then
        log_error "Docker服务未运行，请启动Docker服务"
        log_info "启动命令: sudo systemctl start docker"
        exit 1
    fi
    
    log_info "Docker服务: 运行中 ✓"
    
    # 检查Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose未安装，请先安装Docker Compose"
        log_info "安装命令: sudo curl -L \"https://github.com/docker/compose/releases/latest/download/docker-compose-\$(uname -s)-\$(uname -m)\" -o /usr/local/bin/docker-compose && sudo chmod +x /usr/local/bin/docker-compose"
        exit 1
    fi
    
    local compose_version=$(docker-compose --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')
    log_info "Docker Compose版本: $compose_version ✓"
    
    # 检查Docker权限
    if ! docker ps &> /dev/null; then
        log_warning "当前用户无Docker权限，尝试添加到docker组..."
        sudo usermod -aG docker $USER
        log_warning "请重新登录或运行: newgrp docker"
    fi
    
    log_success "Docker环境检查完成"
}

# 拉取项目代码
pull_project_code() {
    log_step "拉取项目代码..."
    
    # 处理现有安装
    if [[ -d "$INSTALL_DIR" ]]; then
        log_warning "目录 $INSTALL_DIR 已存在"
        if [[ "${FORCE:-false}" != "true" ]]; then
            read -p "是否删除并重新安装? (y/N): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                log_error "安装取消"
                exit 1
            fi
        fi
        
        # 备份现有安装
        local backup_dir="/opt/openwrt-compiler-backup-$(date +%Y%m%d-%H%M%S)"
        log_info "备份现有安装到: $backup_dir"
        sudo mv "$INSTALL_DIR" "$backup_dir"
    fi
    
    # 创建安装目录
    log_info "创建安装目录: $INSTALL_DIR"
    sudo mkdir -p "$INSTALL_DIR"
    
    # 克隆项目
    log_info "从 $REPO_URL 克隆项目..."
    if ! sudo git clone "$REPO_URL" "$INSTALL_DIR"; then
        log_error "项目克隆失败"
        exit 1
    fi
    
    # 设置权限
    sudo chown -R $USER:$USER "$INSTALL_DIR"
    
    log_success "项目代码拉取完成"
}

# 创建Docker配置文件
create_docker_files() {
    log_step "创建Docker配置文件..."
    
    cd "$INSTALL_DIR"
    
    # 创建Dockerfile
    cat > Dockerfile << 'EOF'
# OpenWrt编译器Docker镜像 - 本地构建版本
FROM ubuntu:22.04

# 设置环境变量
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Asia/Shanghai
ENV LANG=zh_CN.UTF-8
ENV LC_ALL=zh_CN.UTF-8
ENV PYTHONIOENCODING=utf-8
ENV PYTHONUNBUFFERED=1

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    # 基础工具
    curl wget git unzip vim htop tree \
    # Python环境
    python3 python3-pip python3-venv python3-dev \
    # 编译工具
    build-essential gcc g++ make cmake \
    # OpenWrt编译依赖
    libncurses5-dev libncursesw5-dev zlib1g-dev gawk \
    gettext libssl-dev xsltproc rsync subversion \
    mercurial bzr ecj fastjar file java-propose-classpath \
    libelf-dev python3-distutils swig aria2 libtinfo5 \
    libgmp3-dev libmpc-dev libmpfr-dev libusb-1.0-0-dev \
    libusb-dev liblzma-dev libsnmp-dev libevent-dev \
    libavahi-client-dev libsqlite3-dev libpcre2-dev \
    ccache \
    # 字符编码支持
    locales language-pack-zh-hans \
    && locale-gen zh_CN.UTF-8 \
    && update-locale LANG=zh_CN.UTF-8 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# 设置时区
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 复制项目文件
COPY . /app/

# 安装Python依赖
RUN pip3 install --no-cache-dir -r requirements.txt

# 创建必要目录
RUN mkdir -p workspace/users workspace/shared logs data tmp

# 创建应用用户
RUN groupadd -r openwrt && useradd -r -g openwrt -u 1000 -m -s /bin/bash openwrt
RUN chown -R openwrt:openwrt /app

# 暴露端口
EXPOSE 9963

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:9963/api/health || exit 1

# 切换到应用用户
USER openwrt

# 启动命令
CMD ["python3", "backend/app.py", "--host", "0.0.0.0", "--port", "9963"]
EOF
    
    log_success "Dockerfile创建完成"

    # 创建docker-compose.yml
    cat > docker-compose.yml << EOF
version: '3.8'

services:
  # OpenWrt编译器主服务
  openwrt-compiler:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: openwrt-compiler
    hostname: openwrt-compiler
    restart: unless-stopped

    environment:
      - PORT=$PORT
      - TZ=Asia/Shanghai
      - LANG=zh_CN.UTF-8
      - LC_ALL=zh_CN.UTF-8
      - PYTHONIOENCODING=utf-8
      - PYTHONUNBUFFERED=1

      # 编译配置
      - DEFAULT_THREADS=\$(nproc)
      - ENABLE_CCACHE=true
      - CCACHE_SIZE=10G
      - ENABLE_ISTORE=true

    ports:
      - "$PORT:9963"
      - "8000:8000"

    volumes:
      - ./workspace:/app/workspace
      - ./logs:/app/logs
      - ./data:/app/data
      - ./config:/app/config
      - ./tmp:/app/tmp

    networks:
      - openwrt-network

    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9963/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '2.0'
        reservations:
          memory: 1G
          cpus: '0.5'

  # Nginx代理服务（可选）
  nginx-proxy:
    image: nginx:alpine
    container_name: openwrt-nginx
    hostname: nginx-proxy
    restart: unless-stopped

    ports:
      - "80:80"
      - "443:443"

    volumes:
      - ./config/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./logs/nginx:/var/log/nginx
      - ./frontend:/usr/share/nginx/html:ro

    environment:
      - TZ=Asia/Shanghai

    depends_on:
      openwrt-compiler:
        condition: service_healthy

    networks:
      - openwrt-network

    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Redis缓存服务
  redis-cache:
    image: redis:7-alpine
    container_name: openwrt-redis
    hostname: redis-cache
    restart: unless-stopped

    ports:
      - "127.0.0.1:6379:6379"

    volumes:
      - redis_data:/data
      - ./config/redis.conf:/usr/local/etc/redis/redis.conf:ro

    command: redis-server /usr/local/etc/redis/redis.conf --appendonly yes

    environment:
      - TZ=Asia/Shanghai

    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3

    networks:
      - openwrt-network

    deploy:
      resources:
        limits:
          memory: 256M
          cpus: '0.5'
        reservations:
          memory: 64M
          cpus: '0.1'

# 数据卷定义
volumes:
  redis_data:
    driver: local

# 网络配置
networks:
  openwrt-network:
    driver: bridge
    ipam:
      driver: default
      config:
        - subnet: 172.20.0.0/16
          gateway: 172.20.0.1
EOF

    log_success "docker-compose.yml创建完成"
}

# 创建配置文件
create_config_files() {
    log_step "创建配置文件..."

    cd "$INSTALL_DIR"

    # 创建配置目录
    mkdir -p config

    # 创建环境配置文件
    cat > .env << EOF
# OpenWrt编译器配置 - Docker本地模式
PORT=$PORT
TZ=Asia/Shanghai
DEBUG=${DEBUG:-false}
MODE=docker-local

# 服务配置
HOST=0.0.0.0
WORKERS=4
MAX_COMPILE_JOBS=2

# 编译配置
DEFAULT_THREADS=\$(nproc)
ENABLE_CCACHE=true
CCACHE_SIZE=10G

# 邮箱配置（可选）
MAIL_SERVER=
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=
MAIL_PASSWORD=
MAIL_DEFAULT_SENDER=

# iStore配置
ENABLE_ISTORE=true
ISTORE_REPO=https://github.com/linkease/istore.git

# 安全配置
SECRET_KEY=\$(openssl rand -hex 32 2>/dev/null || echo "change-this-secret-key")
SESSION_TIMEOUT=3600

# 日志配置
LOG_LEVEL=INFO
LOG_MAX_SIZE=100MB
LOG_BACKUP_COUNT=5
EOF

    # 创建Nginx配置
    mkdir -p config
    cat > config/nginx.conf << 'EOF'
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
    use epoll;
    multi_accept on;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # 字符编码
    charset utf-8;

    # 日志格式
    log_format main '\$remote_addr - \$remote_user [\$time_local] "\$request" '
                    '\$status \$body_bytes_sent "\$http_referer" '
                    '"\$http_user_agent" "\$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;

    # 基础配置
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    server_tokens off;

    # Gzip压缩
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml text/javascript application/json application/javascript application/xml+rss application/atom+xml image/svg+xml;

    # 上游服务器
    upstream openwrt_backend {
        server openwrt-compiler:9963;
        keepalive 32;
    }

    # 主服务器配置
    server {
        listen 80;
        server_name localhost _;

        charset utf-8;

        # 安全头
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;

        # 健康检查
        location /health {
            proxy_pass http://openwrt_backend/api/health;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
            access_log off;
        }

        # API代理
        location /api/ {
            proxy_pass http://openwrt_backend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade \$http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
            proxy_cache_bypass \$http_upgrade;

            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 300s;
        }

        # WebSocket支持
        location /ws/ {
            proxy_pass http://openwrt_backend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade \$http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;

            proxy_buffering off;
            proxy_cache off;
            proxy_read_timeout 86400s;
            proxy_send_timeout 86400s;
        }

        # 静态文件
        location ~* \.(css|js|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)\$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
            add_header Vary "Accept-Encoding";
            access_log off;
            try_files \$uri @backend;
        }

        # 默认代理
        location / {
            try_files \$uri \$uri/ @backend;
        }

        location @backend {
            proxy_pass http://openwrt_backend;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
        }

        # 错误页面
        error_page 404 /404.html;
        error_page 500 502 503 504 /50x.html;
    }
}
EOF

    # 创建Redis配置
    cat > config/redis.conf << 'EOF'
# Redis配置文件 - Docker本地模式
bind 0.0.0.0
port 6379
timeout 300
tcp-keepalive 300

daemonize no
supervised no
pidfile /var/run/redis_6379.pid
loglevel notice
logfile ""
databases 16

maxmemory 128mb
maxmemory-policy allkeys-lru
maxmemory-samples 5

save 900 1
save 300 10
save 60 10000
stop-writes-on-bgsave-error yes
rdbcompression yes
rdbchecksum yes
dbfilename dump.rdb
dir /data

appendonly yes
appendfilename "appendonly.aof"
appendfsync everysec
no-appendfsync-on-rewrite no
auto-aof-rewrite-percentage 100
auto-aof-rewrite-min-size 64mb
aof-load-truncated yes
aof-use-rdb-preamble yes

maxclients 1000
slowlog-log-slower-than 10000
slowlog-max-len 128
latency-monitor-threshold 100
notify-keyspace-events ""

hash-max-ziplist-entries 512
hash-max-ziplist-value 64
list-max-ziplist-size -2
list-compress-depth 0
set-max-intset-entries 512
zset-max-ziplist-entries 128
zset-max-ziplist-value 64
hll-sparse-max-bytes 3000
stream-node-max-bytes 4096
stream-node-max-entries 100
activerehashing yes
client-output-buffer-limit normal 0 0 0
client-output-buffer-limit replica 256mb 64mb 60
client-output-buffer-limit pubsub 32mb 8mb 60
hz 10
dynamic-hz yes
aof-rewrite-incremental-fsync yes
rdb-save-incremental-fsync yes
EOF

    log_success "配置文件创建完成"
}

# 创建管理脚本
create_management_scripts() {
    log_step "创建管理脚本..."

    cd "$INSTALL_DIR"

    # 创建启动脚本
    cat > start.sh << 'EOF'
#!/bin/bash

# OpenWrt编译器启动脚本 - Docker本地模式

set -e

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🚀 启动OpenWrt编译器 - Docker本地模式${NC}"

# 获取脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 检查Docker环境
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker未安装${NC}"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo -e "${RED}❌ Docker服务未运行${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose未安装${NC}"
    exit 1
fi

# 创建必要目录
mkdir -p workspace/{users,shared/{cache,downloads,ccache}}
mkdir -p logs/{compile,system,access,nginx}
mkdir -p data/{configs,firmware,uploads}
mkdir -p tmp

# 停止现有服务
echo -e "${YELLOW}停止现有服务...${NC}"
docker-compose down 2>/dev/null || true

# 构建镜像
echo -e "${BLUE}构建Docker镜像...${NC}"
docker-compose build --no-cache

# 启动服务
echo -e "${BLUE}启动服务...${NC}"
docker-compose up -d

# 等待服务启动
echo -e "${BLUE}等待服务启动...${NC}"
sleep 15

# 检查服务状态
if docker-compose ps | grep -q "Up"; then
    echo -e "${GREEN}✅ 服务启动成功！${NC}"

    # 获取端口
    local port=$(grep "PORT=" .env 2>/dev/null | cut -d'=' -f2 || echo "9963")
    local ip=$(ip route get 1.1.1.1 2>/dev/null | grep -oP 'src \K\S+' || echo "localhost")

    echo ""
    echo -e "${GREEN}🌐 访问地址:${NC}"
    echo -e "   本地: ${BLUE}http://localhost:$port${NC}"
    echo -e "   网络: ${BLUE}http://$ip:$port${NC}"
    echo -e "   代理: ${BLUE}http://localhost${NC} (如果启用Nginx)"
    echo ""
else
    echo -e "${RED}❌ 服务启动失败${NC}"
    docker-compose logs
    exit 1
fi
EOF

    # 创建停止脚本
    cat > stop.sh << 'EOF'
#!/bin/bash

# OpenWrt编译器停止脚本

set -e

echo "🛑 停止OpenWrt编译器..."

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 停止服务
docker-compose down

echo "✅ 服务已停止"
EOF

    # 创建重启脚本
    cat > restart.sh << 'EOF'
#!/bin/bash

# OpenWrt编译器重启脚本

echo "🔄 重启OpenWrt编译器..."
./stop.sh
sleep 2
./start.sh
EOF

    # 创建状态检查脚本
    cat > status.sh << 'EOF'
#!/bin/bash

# OpenWrt编译器状态检查脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "📊 OpenWrt编译器状态检查"
echo "=========================="

# 检查容器状态
echo "🐳 容器状态:"
docker-compose ps

echo ""
echo "💻 系统资源:"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"

echo ""
echo "🌐 网络连接:"
local port=$(grep "PORT=" .env 2>/dev/null | cut -d'=' -f2 || echo "9963")
if curl -f -s http://localhost:$port/api/health &> /dev/null; then
    echo "✅ HTTP服务响应正常 (端口 $port)"
else
    echo "❌ HTTP服务响应异常 (端口 $port)"
fi

if curl -f -s http://localhost/health &> /dev/null; then
    echo "✅ Nginx代理响应正常 (端口 80)"
else
    echo "⚠️ Nginx代理响应异常 (端口 80)"
fi
EOF

    # 创建日志查看脚本
    cat > logs.sh << 'EOF'
#!/bin/bash

# OpenWrt编译器日志查看脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [[ $# -eq 0 ]]; then
    echo "📋 查看所有服务日志:"
    docker-compose logs --tail=50
elif [[ "$1" == "-f" ]]; then
    echo "📋 实时查看所有服务日志:"
    docker-compose logs -f
else
    echo "📋 查看指定服务日志: $1"
    docker-compose logs --tail=50 "$1"
fi
EOF

    # 设置执行权限
    chmod +x start.sh stop.sh restart.sh status.sh logs.sh

    log_success "管理脚本创建完成"
}

# 构建Docker镜像
build_docker_image() {
    log_step "构建Docker镜像..."

    cd "$INSTALL_DIR"

    # 构建镜像
    log_info "开始构建Docker镜像，这可能需要几分钟..."
    if docker-compose build --no-cache; then
        log_success "Docker镜像构建完成"
    else
        log_error "Docker镜像构建失败"
        exit 1
    fi
}

# 启动服务
start_services() {
    log_step "启动Docker服务..."

    cd "$INSTALL_DIR"

    if [[ "${AUTO_START:-true}" == "true" ]]; then
        log_info "启动Docker服务..."

        # 创建必要目录
        mkdir -p workspace/{users,shared/{cache,downloads,ccache}}
        mkdir -p logs/{compile,system,access,nginx}
        mkdir -p data/{configs,firmware,uploads}
        mkdir -p tmp

        # 启动服务
        if docker-compose up -d; then
            log_info "等待服务启动..."
            sleep 15

            # 检查服务状态
            if docker-compose ps | grep -q "Up"; then
                log_success "服务启动成功"
            else
                log_warning "服务可能未完全启动，请检查日志"
                docker-compose logs --tail=10
            fi
        else
            log_error "服务启动失败"
            exit 1
        fi
    else
        log_info "跳过自动启动，使用以下命令手动启动:"
        echo "  cd $INSTALL_DIR && ./start.sh"
    fi
}

# 显示安装结果
show_result() {
    local local_ip
    local_ip=$(ip route get 1.1.1.1 2>/dev/null | grep -oP 'src \K\S+' || echo "localhost")

    echo ""
    log_success "🎉 OpenWrt编译器Docker本地模式安装完成！"
    echo ""

    # 显示访问信息
    echo -e "${CYAN}📍 访问信息:${NC}"
    echo -e "   🌐 主服务: ${BLUE}http://localhost:$PORT${NC}"
    echo -e "   🌍 网络访问: ${BLUE}http://$local_ip:$PORT${NC}"
    echo -e "   🔗 代理访问: ${BLUE}http://localhost${NC} (如果启用Nginx)"
    echo -e "   📁 安装目录: ${BLUE}$INSTALL_DIR${NC}"
    echo -e "   📝 安装日志: ${BLUE}$LOG_FILE${NC}"
    echo ""

    # 显示系统信息
    echo -e "${CYAN}💻 系统信息:${NC}"
    echo -e "   部署模式: ${YELLOW}Docker本地模式${NC}"
    echo -e "   服务端口: ${YELLOW}$PORT${NC}"
    echo -e "   容器数量: ${YELLOW}3个 (主服务+Nginx+Redis)${NC}"
    echo -e "   安装时间: ${YELLOW}$(date)${NC}"
    echo ""

    # 显示管理命令
    echo -e "${CYAN}🔧 管理命令:${NC}"
    echo -e "   启动服务: ${YELLOW}cd $INSTALL_DIR && ./start.sh${NC}"
    echo -e "   停止服务: ${YELLOW}cd $INSTALL_DIR && ./stop.sh${NC}"
    echo -e "   重启服务: ${YELLOW}cd $INSTALL_DIR && ./restart.sh${NC}"
    echo -e "   查看状态: ${YELLOW}cd $INSTALL_DIR && ./status.sh${NC}"
    echo -e "   查看日志: ${YELLOW}cd $INSTALL_DIR && ./logs.sh${NC}"
    echo ""

    # 显示Docker命令
    echo -e "${CYAN}🐳 Docker命令:${NC}"
    echo -e "   查看容器: ${YELLOW}docker-compose ps${NC}"
    echo -e "   查看日志: ${YELLOW}docker-compose logs -f${NC}"
    echo -e "   进入容器: ${YELLOW}docker exec -it openwrt-compiler /bin/bash${NC}"
    echo -e "   重建镜像: ${YELLOW}docker-compose build --no-cache${NC}"
    echo ""

    # 显示功能特性
    echo -e "${CYAN}🚀 功能特性:${NC}"
    echo -e "   ✅ Docker本地模式部署"
    echo -e "   ✅ 不依赖外部Docker仓库"
    echo -e "   ✅ 完整的容器化服务编排"
    echo -e "   ✅ Nginx反向代理支持"
    echo -e "   ✅ Redis缓存加速"
    echo -e "   ✅ 多用户支持"
    echo -e "   ✅ Web版menuconfig"
    echo -e "   ✅ 实时编译日志"
    echo -e "   ✅ 自动iStore集成"
    echo ""

    # 显示下一步操作
    echo -e "${CYAN}📋 下一步操作:${NC}"
    echo -e "   1. 访问Web界面创建用户账户"
    echo -e "   2. 选择目标设备和配置"
    echo -e "   3. 开始编译OpenWrt固件"
    echo ""

    # 显示故障排除
    echo -e "${CYAN}🔍 故障排除:${NC}"
    echo -e "   检查服务: ${YELLOW}cd $INSTALL_DIR && ./status.sh${NC}"
    echo -e "   查看日志: ${YELLOW}cat $LOG_FILE${NC}"
    echo -e "   容器日志: ${YELLOW}cd $INSTALL_DIR && ./logs.sh${NC}"
    echo ""

    echo -e "${GREEN}✨ 享受Docker化的OpenWrt固件编译之旅！${NC}"
    echo -e "${WHITE}📖 更多信息请查看: https://github.com/moyanjiang/openwrt_make_web${NC}"
    echo ""
}

# 主函数
main() {
    # 初始化日志文件
    echo "OpenWrt编译器Docker本地模式安装日志 - $(date)" > "$LOG_FILE"

    # 解析命令行参数
    PORT=$DEFAULT_PORT
    REPO_URL=$DEFAULT_REPO
    AUTO_START=true
    FORCE=false
    DEBUG=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            -p|--port)
                PORT="$2"
                shift 2
                ;;
            -d|--dir)
                INSTALL_DIR="$2"
                shift 2
                ;;
            -r|--repo)
                REPO_URL="$2"
                shift 2
                ;;
            --no-start)
                AUTO_START=false
                shift
                ;;
            --force)
                FORCE=true
                shift
                ;;
            --debug)
                DEBUG=true
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                log_error "未知参数: $1"
                show_help
                exit 1
                ;;
        esac
    done

    # 验证参数
    if ! [[ "$PORT" =~ ^[0-9]+$ ]] || [[ $PORT -lt 1 ]] || [[ $PORT -gt 65535 ]]; then
        log_error "无效端口: $PORT"
        exit 1
    fi

    # 显示横幅
    show_banner

    # 显示配置信息
    echo -e "${CYAN}📋 安装配置:${NC}"
    echo -e "   部署模式: ${YELLOW}Docker本地模式${NC}"
    echo -e "   服务端口: ${YELLOW}$PORT${NC}"
    echo -e "   安装目录: ${YELLOW}$INSTALL_DIR${NC}"
    echo -e "   Git仓库: ${YELLOW}$REPO_URL${NC}"
    echo -e "   自动启动: ${YELLOW}$AUTO_START${NC}"
    echo -e "   强制安装: ${YELLOW}$FORCE${NC}"
    echo -e "   调试模式: ${YELLOW}$DEBUG${NC}"
    echo ""

    # 确认安装（除非强制模式）
    if [[ "$FORCE" != "true" ]]; then
        read -p "是否继续安装? (Y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Nn]$ ]]; then
            log_info "安装取消"
            exit 0
        fi
    fi

    # 记录开始时间
    local start_time=$(date +%s)

    # 执行安装步骤
    log_step "开始Docker本地模式安装流程..."

    # 1. 检查Docker环境
    check_docker_environment

    # 2. 拉取项目代码
    pull_project_code

    # 3. 创建Docker配置文件
    create_docker_files

    # 4. 创建配置文件
    create_config_files

    # 5. 创建管理脚本
    create_management_scripts

    # 6. 构建Docker镜像
    build_docker_image

    # 7. 启动服务
    start_services

    # 计算安装时间
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    local minutes=$((duration / 60))
    local seconds=$((duration % 60))

    # 显示结果
    show_result

    log_success "Docker本地模式安装完成！总耗时: ${minutes}分${seconds}秒"
    log_info "详细日志已保存到: $LOG_FILE"
}

# 运行主函数
main "$@"
