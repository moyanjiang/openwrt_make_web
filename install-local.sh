#!/bin/bash

# OpenWrt编译器Docker本地部署脚本
# 本地构建Docker镜像，不依赖外部Docker仓库

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
LOG_FILE="/tmp/openwrt-install-local.log"

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
 ██████╗ ██████╗ ███████╗███╗   ██╗██╗    ██╗██████╗ ████████╗
██╔═══██╗██╔══██╗██╔════╝████╗  ██║██║    ██║██╔══██╗╚══██╔══╝
██║   ██║██████╔╝█████╗  ██╔██╗ ██║██║ █╗ ██║██████╔╝   ██║   
██║   ██║██╔═══╝ ██╔══╝  ██║╚██╗██║██║███╗██║██╔══██╗   ██║   
╚██████╔╝██║     ███████╗██║ ╚████║╚███╔███╔╝██║  ██║   ██║   
 ╚═════╝ ╚═╝     ╚══════╝╚═╝  ╚═══╝ ╚══╝╚══╝ ╚═╝  ╚═╝   ╚═╝   
                                                              
        编译器本地模式部署脚本 v${SCRIPT_VERSION}
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
    ${YELLOW}✅ 本地构建Docker镜像${NC}
    ${YELLOW}✅ 不依赖外部Docker仓库${NC}
    ${YELLOW}✅ 容器化部署${NC}
    ${YELLOW}✅ 完整的服务编排${NC}

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

EOF
}

# 检测系统信息
detect_system() {
    log_step "检测系统信息..."
    
    # 检测发行版
    if [[ -f /etc/os-release ]]; then
        source /etc/os-release
        OS_NAME="$NAME"
        OS_VERSION="$VERSION"
        OS_ID="$ID"
    else
        OS_NAME="Unknown"
        OS_VERSION="Unknown"
        OS_ID="unknown"
    fi
    
    # 检测架构
    ARCH=$(uname -m)
    
    # 检测内核版本
    KERNEL_VERSION=$(uname -r)
    
    # 检测包管理器
    if command -v apt-get &> /dev/null; then
        PKG_MANAGER="apt"
    elif command -v yum &> /dev/null; then
        PKG_MANAGER="yum"
    elif command -v dnf &> /dev/null; then
        PKG_MANAGER="dnf"
    else
        PKG_MANAGER="unknown"
    fi
    
    log_info "系统: $OS_NAME $OS_VERSION ($OS_ID)"
    log_info "架构: $ARCH"
    log_info "内核: $KERNEL_VERSION"
    log_info "包管理器: $PKG_MANAGER"
}

# 检查系统要求
check_system() {
    log_step "检查系统环境..."
    
    # 检测系统信息
    detect_system
    
    # 检查操作系统支持
    case "$OS_ID" in
        ubuntu|debian)
            if [[ "$PKG_MANAGER" != "apt" ]]; then
                log_error "Debian/Ubuntu系统但未找到apt包管理器"
                exit 1
            fi
            log_info "操作系统: $OS_NAME $OS_VERSION ✓"
            ;;
        centos|rhel|fedora)
            if [[ "$PKG_MANAGER" != "yum" && "$PKG_MANAGER" != "dnf" ]]; then
                log_error "RedHat系系统但未找到yum/dnf包管理器"
                exit 1
            fi
            log_info "操作系统: $OS_NAME $OS_VERSION ✓"
            ;;
        *)
            log_warning "未测试的操作系统: $OS_NAME"
            if [[ "${FORCE:-false}" != "true" ]]; then
                read -p "是否继续安装? (y/N): " -n 1 -r
                echo
                if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                    exit 1
                fi
            fi
            ;;
    esac
    
    # 检查Docker
    if command -v docker &> /dev/null; then
        local docker_version=$(docker --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')
        log_info "Docker版本: $docker_version ✓"

        # 检查Docker服务状态
        if docker info &> /dev/null; then
            log_info "Docker服务: 运行中 ✓"
        else
            log_error "Docker服务未运行，请启动Docker服务"
            exit 1
        fi
    else
        log_error "Docker未安装，请先安装Docker"
        exit 1
    fi

    # 检查Docker Compose
    if command -v docker-compose &> /dev/null; then
        local compose_version=$(docker-compose --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')
        log_info "Docker Compose版本: $compose_version ✓"
    else
        log_error "Docker Compose未安装，请先安装Docker Compose"
        exit 1
    fi
    
    # 检查系统资源
    local mem_gb=$(free -g | awk '/^Mem:/{print $2}')
    local disk_gb=$(df -BG / | awk 'NR==2{print int($4)}')
    local cpu_cores=$(nproc)
    
    log_info "系统资源:"
    log_info "  CPU核心: ${cpu_cores}"
    log_info "  内存: ${mem_gb}GB"
    log_info "  可用磁盘: ${disk_gb}GB"
    
    # 资源检查
    local warnings=0
    if [[ $mem_gb -lt 4 ]]; then
        log_warning "内存不足4GB，编译可能会失败"
        ((warnings++))
    fi
    
    if [[ $disk_gb -lt 50 ]]; then
        log_warning "磁盘空间不足50GB，可能无法完成编译"
        ((warnings++))
    fi
    
    if [[ $cpu_cores -lt 2 ]]; then
        log_warning "CPU核心数少于2，编译速度会很慢"
        ((warnings++))
    fi
    
    # 如果有严重警告且非强制模式，询问用户
    if [[ $warnings -gt 0 && "${FORCE:-false}" != "true" ]]; then
        log_warning "检测到 $warnings 个资源警告"
        read -p "是否继续安装? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    log_success "系统检查完成"
}

# 安装系统依赖
install_system_dependencies() {
    log_step "安装系统依赖..."
    
    case "$PKG_MANAGER" in
        apt)
            install_dependencies_debian
            ;;
        yum|dnf)
            install_dependencies_redhat
            ;;
        *)
            log_warning "未知包管理器: $PKG_MANAGER，跳过系统依赖安装"
            ;;
    esac
}

# Debian/Ubuntu系统依赖
install_dependencies_debian() {
    log_info "安装Debian/Ubuntu系统依赖..."

    # 更新包列表
    sudo apt-get update

    # 基础工具
    local basic_packages=(
        "curl" "wget" "git" "unzip" "vim" "htop" "tree"
        "ca-certificates" "gnupg" "lsb-release"
    )

    # 安装基础包
    log_info "安装基础工具..."
    sudo apt-get install -y "${basic_packages[@]}"

    # 检查并安装Docker
    if ! command -v docker &> /dev/null; then
        log_info "安装Docker..."
        install_docker_debian
    else
        log_info "Docker已安装，跳过安装"
    fi

    # 检查并安装Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_info "安装Docker Compose..."
        install_docker_compose
    else
        log_info "Docker Compose已安装，跳过安装"
    fi

    log_success "系统依赖安装完成"
}

# 安装Docker
install_docker_debian() {
    log_info "安装Docker CE..."

    # 添加Docker官方GPG密钥
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

    # 添加Docker仓库
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

    # 更新包列表并安装Docker
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io

    # 启动Docker服务
    sudo systemctl start docker
    sudo systemctl enable docker

    # 添加用户到docker组
    sudo usermod -aG docker $USER

    log_success "Docker安装完成"
}

# 安装Docker Compose
install_docker_compose() {
    log_info "安装Docker Compose..."

    # 下载Docker Compose
    local compose_version="2.20.2"
    sudo curl -L "https://github.com/docker/compose/releases/download/v${compose_version}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

    # 设置执行权限
    sudo chmod +x /usr/local/bin/docker-compose

    # 创建软链接
    sudo ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose

    log_success "Docker Compose安装完成"
}

# RedHat系系统依赖
install_dependencies_redhat() {
    log_info "安装RedHat系系统依赖..."

    # 基础工具
    local basic_packages=(
        "curl" "wget" "git" "unzip" "vim" "htop" "tree"
        "gcc" "gcc-c++" "make" "python3" "python3-pip"
        "python3-devel"
    )

    # OpenWrt编译依赖
    local openwrt_packages=(
        "ncurses-devel" "zlib-devel" "gawk" "gettext" "openssl-devel"
        "libxslt" "rsync" "subversion" "mercurial" "bzr" "java-1.8.0-openjdk"
        "elfutils-libelf-devel" "python3-devel" "swig" "gmp-devel"
        "mpfr-devel" "libmpc-devel" "libusb-devel" "xz-devel"
        "net-snmp-devel" "libevent-devel" "avahi-devel" "sqlite-devel"
        "pcre2-devel" "ccache" "nginx" "supervisor"
    )

    # 安装基础包
    log_info "安装基础工具..."
    sudo $PKG_MANAGER install -y "${basic_packages[@]}"

    # 安装OpenWrt编译依赖
    log_info "安装OpenWrt编译依赖..."
    sudo $PKG_MANAGER install -y "${openwrt_packages[@]}"

    log_success "系统依赖安装完成"
}

# 下载项目代码
download_project() {
    log_step "下载项目代码..."

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

    # 克隆项目或使用当前目录
    if [[ -f "backend/app.py" || -f "frontend/index.html" ]]; then
        log_info "检测到本地项目文件，复制到安装目录..."
        sudo cp -r . "$INSTALL_DIR/"
    else
        log_info "从 $REPO_URL 克隆项目..."
        if ! sudo git clone "$REPO_URL" "$INSTALL_DIR"; then
            log_error "项目克隆失败"
            exit 1
        fi
    fi

    # 设置权限
    sudo chown -R $USER:$USER "$INSTALL_DIR"

    log_success "项目代码下载完成"
}

# 创建Python虚拟环境
create_virtual_environment() {
    log_step "创建Python虚拟环境..."

    cd "$INSTALL_DIR"

    # 创建虚拟环境
    if [[ ! -d "venv" ]]; then
        log_info "创建Python虚拟环境..."
        python3 -m venv venv
    else
        log_info "虚拟环境已存在"
    fi

    # 激活虚拟环境并升级pip
    source venv/bin/activate
    pip install --upgrade pip setuptools wheel

    # 安装Python依赖
    if [[ -f "requirements.txt" ]]; then
        log_info "安装Python依赖包..."
        pip install -r requirements.txt
    else
        log_info "安装基础Python依赖..."
        pip install Flask Flask-SocketIO Flask-CORS requests PyYAML psutil watchdog click colorama
    fi

    deactivate
    log_success "Python环境创建完成"
}

# 配置环境
configure_environment() {
    log_step "配置环境..."

    cd "$INSTALL_DIR"

    # 创建环境变量文件
    if [[ ! -f ".env" ]] || [[ "${FORCE:-false}" == "true" ]]; then
        log_info "创建环境配置文件..."
        cat > .env << EOF
# OpenWrt编译器配置 - 本地模式
PORT=$PORT
TZ=Asia/Shanghai
DEBUG=${DEBUG:-false}
MODE=local

# 服务配置
HOST=0.0.0.0
WORKERS=4
MAX_COMPILE_JOBS=2

# 编译配置
DEFAULT_THREADS=$(nproc)
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
SECRET_KEY=$(openssl rand -hex 32 2>/dev/null || echo "change-this-secret-key")
SESSION_TIMEOUT=3600

# 日志配置
LOG_LEVEL=INFO
LOG_MAX_SIZE=100MB
LOG_BACKUP_COUNT=5
EOF
        log_success "环境配置文件创建完成"
    else
        log_info "环境配置文件已存在，跳过创建"
    fi

    # 创建必要目录结构
    log_info "创建目录结构..."
    local directories=(
        "workspace/users"
        "workspace/shared/cache"
        "workspace/shared/downloads"
        "workspace/shared/ccache"
        "logs/compile"
        "logs/system"
        "logs/access"
        "data/configs"
        "data/firmware"
        "data/uploads"
        "tmp"
    )

    for dir in "${directories[@]}"; do
        mkdir -p "$dir"
    done

    # 设置目录权限
    chmod 755 workspace logs data
    chmod 777 tmp

    # 配置ccache
    if command -v ccache &> /dev/null; then
        export CCACHE_DIR="$INSTALL_DIR/workspace/shared/ccache"
        ccache --set-config=cache_dir="$CCACHE_DIR"
        ccache --set-config=max_size=10G
        ccache --set-config=compression=true
        log_info "ccache配置完成"
    fi

    log_success "环境配置完成"
}

# 创建启动脚本
create_startup_scripts() {
    log_step "创建启动脚本..."

    cd "$INSTALL_DIR"

    # 创建主启动脚本
    cat > start.sh << 'EOF'
#!/bin/bash

# OpenWrt编译器启动脚本 - 本地模式

set -e

# 获取脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}🚀 启动OpenWrt编译器 - 本地模式${NC}"

# 加载环境变量
if [[ -f ".env" ]]; then
    source .env
    echo -e "${GREEN}✓ 环境配置加载完成${NC}"
else
    echo -e "${YELLOW}⚠ 未找到.env文件，使用默认配置${NC}"
    PORT=9963
fi

# 激活虚拟环境
if [[ -d "venv" ]]; then
    source venv/bin/activate
    echo -e "${GREEN}✓ Python虚拟环境激活${NC}"
else
    echo -e "${YELLOW}⚠ 未找到虚拟环境，使用系统Python${NC}"
fi

# 设置环境变量
export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"
export LANG=zh_CN.UTF-8
export LC_ALL=zh_CN.UTF-8
export PYTHONIOENCODING=utf-8

# 创建PID文件目录
mkdir -p tmp

# 启动后端服务
echo -e "${BLUE}启动后端服务...${NC}"
cd backend
nohup python3 app.py --host 0.0.0.0 --port ${PORT:-9963} > ../logs/app.log 2>&1 &
echo $! > ../tmp/app.pid

# 等待服务启动
sleep 3

# 检查服务状态
if kill -0 $(cat ../tmp/app.pid) 2>/dev/null; then
    echo -e "${GREEN}✅ 后端服务启动成功 (PID: $(cat ../tmp/app.pid))${NC}"
    echo -e "${GREEN}🌐 访问地址: http://localhost:${PORT:-9963}${NC}"
else
    echo -e "${RED}❌ 后端服务启动失败${NC}"
    exit 1
fi

echo -e "${GREEN}🎉 OpenWrt编译器启动完成！${NC}"
EOF

    # 创建停止脚本
    cat > stop.sh << 'EOF'
#!/bin/bash

# OpenWrt编译器停止脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🛑 停止OpenWrt编译器..."

# 停止后端服务
if [[ -f "tmp/app.pid" ]]; then
    local pid=$(cat tmp/app.pid)
    if kill -0 $pid 2>/dev/null; then
        kill $pid
        echo "✅ 后端服务已停止 (PID: $pid)"
    else
        echo "⚠ 后端服务未运行"
    fi
    rm -f tmp/app.pid
else
    echo "⚠ 未找到PID文件"
fi

echo "🎉 OpenWrt编译器已停止"
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

# 检查PID文件
if [[ -f "tmp/app.pid" ]]; then
    local pid=$(cat tmp/app.pid)
    if kill -0 $pid 2>/dev/null; then
        echo "✅ 后端服务运行中 (PID: $pid)"

        # 检查端口
        local port=$(grep "PORT=" .env 2>/dev/null | cut -d'=' -f2 || echo "9963")
        if netstat -tlnp 2>/dev/null | grep -q ":$port "; then
            echo "✅ 端口 $port 监听正常"
        else
            echo "❌ 端口 $port 未监听"
        fi

        # 检查HTTP响应
        if curl -f -s http://localhost:$port/health &> /dev/null; then
            echo "✅ HTTP服务响应正常"
        else
            echo "⚠ HTTP服务响应异常"
        fi
    else
        echo "❌ 后端服务未运行"
    fi
else
    echo "❌ 未找到PID文件，服务可能未启动"
fi

# 显示系统资源
echo ""
echo "💻 系统资源:"
echo "  CPU使用率: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)%"
echo "  内存使用: $(free -h | awk '/^Mem:/ {print $3"/"$2}')"
echo "  磁盘使用: $(df -h . | awk 'NR==2 {print $3"/"$2" ("$5")"}')"
EOF

    # 设置执行权限
    chmod +x start.sh stop.sh restart.sh status.sh

    log_success "启动脚本创建完成"
}

# 创建systemd服务
create_systemd_service() {
    log_step "创建systemd服务..."

    # 创建服务文件
    cat > /tmp/openwrt-compiler.service << EOF
[Unit]
Description=OpenWrt Compiler Service
After=network.target
Wants=network.target

[Service]
Type=forking
User=$USER
Group=$USER
WorkingDirectory=$INSTALL_DIR
Environment=PATH=$INSTALL_DIR/venv/bin:/usr/local/bin:/usr/bin:/bin
Environment=PYTHONPATH=$INSTALL_DIR
Environment=LANG=zh_CN.UTF-8
Environment=LC_ALL=zh_CN.UTF-8
Environment=PYTHONIOENCODING=utf-8
ExecStart=$INSTALL_DIR/start.sh
ExecStop=$INSTALL_DIR/stop.sh
ExecReload=$INSTALL_DIR/restart.sh
PIDFile=$INSTALL_DIR/tmp/app.pid
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

    # 安装服务文件
    if sudo mv /tmp/openwrt-compiler.service /etc/systemd/system/; then
        sudo systemctl daemon-reload
        sudo systemctl enable openwrt-compiler
        log_success "systemd服务创建完成"
    else
        log_warning "systemd服务创建失败，但不影响手动启动"
    fi
}

# 配置Nginx代理（可选）
configure_nginx() {
    log_step "配置Nginx代理..."

    if ! command -v nginx &> /dev/null; then
        log_warning "Nginx未安装，跳过代理配置"
        return
    fi

    # 创建Nginx配置
    cat > /tmp/openwrt-compiler.conf << EOF
server {
    listen 80;
    server_name localhost _;

    # 字符编码
    charset utf-8;

    # 代理到后端
    location / {
        proxy_pass http://127.0.0.1:$PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        # WebSocket支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # 静态文件
    location /static/ {
        alias $INSTALL_DIR/frontend/static/;
        expires 1y;
    }

    # 日志
    access_log /var/log/nginx/openwrt-compiler.access.log;
    error_log /var/log/nginx/openwrt-compiler.error.log;
}
EOF

    # 安装Nginx配置
    if sudo mv /tmp/openwrt-compiler.conf /etc/nginx/sites-available/; then
        sudo ln -sf /etc/nginx/sites-available/openwrt-compiler.conf /etc/nginx/sites-enabled/
        sudo nginx -t && sudo systemctl reload nginx
        log_success "Nginx代理配置完成"
    else
        log_warning "Nginx配置失败，但不影响直接访问"
    fi
}

# 启动服务
start_service() {
    log_step "启动OpenWrt编译器服务..."

    cd "$INSTALL_DIR"

    if [[ "${AUTO_START:-true}" == "true" ]]; then
        log_info "启动服务..."
        ./start.sh

        # 等待服务启动
        sleep 5

        # 检查服务状态
        if [[ -f "tmp/app.pid" ]] && kill -0 $(cat tmp/app.pid) 2>/dev/null; then
            log_success "服务启动成功"
        else
            log_warning "服务可能未完全启动，请检查日志"
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
    log_success "🎉 OpenWrt编译器本地模式安装完成！"
    echo ""

    # 显示访问信息
    echo -e "${CYAN}📍 访问信息:${NC}"
    echo -e "   🌐 本地访问: ${BLUE}http://localhost:$PORT${NC}"
    echo -e "   🌍 网络访问: ${BLUE}http://$local_ip:$PORT${NC}"
    echo -e "   📁 安装目录: ${BLUE}$INSTALL_DIR${NC}"
    echo -e "   📝 安装日志: ${BLUE}$LOG_FILE${NC}"
    echo ""

    # 显示系统信息
    echo -e "${CYAN}💻 系统信息:${NC}"
    echo -e "   操作系统: ${YELLOW}$OS_NAME $OS_VERSION${NC}"
    echo -e "   部署模式: ${YELLOW}本地模式 (无Docker依赖)${NC}"
    echo -e "   服务端口: ${YELLOW}$PORT${NC}"
    echo -e "   安装时间: ${YELLOW}$(date)${NC}"
    echo ""

    # 显示管理命令
    echo -e "${CYAN}🔧 管理命令:${NC}"
    echo -e "   启动服务: ${YELLOW}cd $INSTALL_DIR && ./start.sh${NC}"
    echo -e "   停止服务: ${YELLOW}cd $INSTALL_DIR && ./stop.sh${NC}"
    echo -e "   重启服务: ${YELLOW}cd $INSTALL_DIR && ./restart.sh${NC}"
    echo -e "   查看状态: ${YELLOW}cd $INSTALL_DIR && ./status.sh${NC}"
    echo -e "   查看日志: ${YELLOW}tail -f $INSTALL_DIR/logs/app.log${NC}"
    echo ""

    # 显示systemd命令（如果可用）
    if systemctl is-enabled openwrt-compiler &>/dev/null; then
        echo -e "${CYAN}🔧 系统服务命令:${NC}"
        echo -e "   启动服务: ${YELLOW}sudo systemctl start openwrt-compiler${NC}"
        echo -e "   停止服务: ${YELLOW}sudo systemctl stop openwrt-compiler${NC}"
        echo -e "   重启服务: ${YELLOW}sudo systemctl restart openwrt-compiler${NC}"
        echo -e "   查看状态: ${YELLOW}sudo systemctl status openwrt-compiler${NC}"
        echo -e "   开机启动: ${YELLOW}sudo systemctl enable openwrt-compiler${NC}"
        echo ""
    fi

    # 显示功能特性
    echo -e "${CYAN}🚀 功能特性:${NC}"
    echo -e "   ✅ 本地模式部署，无Docker依赖"
    echo -e "   ✅ 多用户支持，独立编译环境"
    echo -e "   ✅ 智能设备搜索和配置"
    echo -e "   ✅ Web版menuconfig界面"
    echo -e "   ✅ 自动集成iStore商店"
    echo -e "   ✅ 实时编译日志查看"
    echo -e "   ✅ ccache编译加速"
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
    echo -e "   应用日志: ${YELLOW}tail -f $INSTALL_DIR/logs/app.log${NC}"
    echo ""

    echo -e "${GREEN}✨ 享受OpenWrt固件编译之旅！${NC}"
    echo -e "${WHITE}📖 更多信息请查看: https://github.com/moyanjiang/openwrt_make_web${NC}"
    echo ""
}

# 主函数
main() {
    # 初始化日志文件
    echo "OpenWrt编译器本地模式安装日志 - $(date)" > "$LOG_FILE"

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
    echo -e "   部署模式: ${YELLOW}本地模式 (无Docker依赖)${NC}"
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
    log_step "开始本地模式安装流程..."

    # 1. 系统检查
    check_system

    # 2. 安装系统依赖
    install_system_dependencies

    # 3. 下载项目代码
    download_project

    # 4. 创建Python环境
    create_virtual_environment

    # 5. 配置环境
    configure_environment

    # 6. 创建启动脚本
    create_startup_scripts

    # 7. 创建系统服务
    create_systemd_service

    # 8. 配置Nginx代理
    configure_nginx

    # 9. 启动服务
    start_service

    # 计算安装时间
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    local minutes=$((duration / 60))
    local seconds=$((duration % 60))

    # 显示结果
    show_result

    log_success "本地模式安装完成！总耗时: ${minutes}分${seconds}秒"
    log_info "详细日志已保存到: $LOG_FILE"
}

# 运行主函数
main "$@"
