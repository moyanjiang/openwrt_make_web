#!/bin/bash

# OpenWrt编译器一键安装脚本 v2.0
# 支持Docker部署，多种安装模式，智能环境检测
# 仓库地址: https://github.com/moyanjiang/openwrt_make_web

set -e

# 脚本版本
SCRIPT_VERSION="2.0.0"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# 默认配置
DEFAULT_PORT=9963
DEFAULT_REPO="https://github.com/moyanjiang/openwrt_make_web"
INSTALL_DIR="/opt/openwrt-compiler"
BACKUP_DIR="/opt/openwrt-compiler-backup"
LOG_FILE="/tmp/openwrt-install.log"

# 系统要求
MIN_MEMORY_GB=4
MIN_DISK_GB=50
RECOMMENDED_MEMORY_GB=8
RECOMMENDED_DISK_GB=100

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

log_debug() {
    local msg="$1"
    if [[ "${DEBUG:-false}" == "true" ]]; then
        echo -e "${CYAN}[DEBUG]${NC} $msg"
    fi
    echo "$(date '+%Y-%m-%d %H:%M:%S') [DEBUG] $msg" >> "$LOG_FILE"
}

# 进度条函数
show_progress() {
    local current=$1
    local total=$2
    local width=50
    local percentage=$((current * 100 / total))
    local completed=$((current * width / total))
    local remaining=$((width - completed))

    printf "\r${CYAN}["
    printf "%*s" $completed | tr ' ' '='
    printf "%*s" $remaining | tr ' ' '-'
    printf "] %d%% (%d/%d)${NC}" $percentage $current $total
}

# 错误处理
handle_error() {
    local exit_code=$?
    local line_number=$1
    log_error "脚本在第 $line_number 行出错，退出码: $exit_code"
    log_error "查看详细日志: $LOG_FILE"
    cleanup_on_error
    exit $exit_code
}

# 清理函数
cleanup_on_error() {
    log_warning "正在清理临时文件..."
    # 这里可以添加清理逻辑
}

# 设置错误处理
trap 'handle_error $LINENO' ERR

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

        编译器 Docker 一键安装脚本 v${SCRIPT_VERSION}
EOF
    echo -e "${NC}"
    echo -e "${GREEN}🚀 OpenWrt固件在线编译系统${NC}"
    echo -e "${BLUE}📦 仓库地址: ${DEFAULT_REPO}${NC}"
    echo -e "${WHITE}📝 安装日志: ${LOG_FILE}${NC}"
    echo ""
}

# 检测系统信息
detect_system() {
    log_debug "检测系统信息..."

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
    elif command -v pacman &> /dev/null; then
        PKG_MANAGER="pacman"
    else
        PKG_MANAGER="unknown"
    fi

    log_debug "系统: $OS_NAME $OS_VERSION ($OS_ID)"
    log_debug "架构: $ARCH"
    log_debug "内核: $KERNEL_VERSION"
    log_debug "包管理器: $PKG_MANAGER"
}

# 检查网络连接
check_network() {
    log_step "检查网络连接..."

    local test_urls=(
        "github.com"
        "docker.com"
        "registry-1.docker.io"
    )

    for url in "${test_urls[@]}"; do
        if ping -c 1 -W 3 "$url" &> /dev/null; then
            log_info "网络连接正常: $url ✓"
        else
            log_warning "无法连接到: $url"
        fi
    done
}

# 显示帮助信息
show_help() {
    cat << EOF
${WHITE}OpenWrt编译器一键安装脚本 v${SCRIPT_VERSION}${NC}

${CYAN}用法:${NC}
    $0 [选项]

${CYAN}选项:${NC}
    ${GREEN}-p, --port PORT${NC}         设置服务端口 (默认: $DEFAULT_PORT)
    ${GREEN}-d, --dir DIR${NC}          设置安装目录 (默认: $INSTALL_DIR)
    ${GREEN}-r, --repo URL${NC}         设置Git仓库地址 (默认: $DEFAULT_REPO)
    ${GREEN}-m, --mode MODE${NC}        安装模式: docker|native|test (默认: docker)
    ${GREEN}-b, --branch BRANCH${NC}    Git分支 (默认: main)
    ${GREEN}--backup${NC}               安装前备份现有安装
    ${GREEN}--no-start${NC}             安装后不自动启动服务
    ${GREEN}--dev${NC}                  安装开发版本
    ${GREEN}--debug${NC}                启用调试模式
    ${GREEN}--force${NC}                强制安装，跳过确认
    ${GREEN}--offline${NC}              离线安装模式
    ${GREEN}-h, --help${NC}             显示帮助信息

${CYAN}安装模式:${NC}
    ${YELLOW}docker${NC}                 Docker容器化部署 (推荐)
    ${YELLOW}native${NC}                 原生Python环境部署
    ${YELLOW}test${NC}                   测试模式，仅验证环境

${CYAN}示例:${NC}
    $0                          # 使用默认配置安装
    $0 -p 8080                  # 使用端口8080安装
    $0 -d /home/openwrt         # 安装到指定目录
    $0 -m native                # 原生环境安装
    $0 --dev --debug            # 开发版本+调试模式
    $0 --backup                 # 备份现有安装

${CYAN}环境要求:${NC}
    • 内存: 最低 ${MIN_MEMORY_GB}GB，推荐 ${RECOMMENDED_MEMORY_GB}GB+
    • 磁盘: 最低 ${MIN_DISK_GB}GB，推荐 ${RECOMMENDED_DISK_GB}GB+
    • 系统: Ubuntu 18.04+, Debian 10+, CentOS 7+

EOF
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

    # 检查架构支持
    case "$ARCH" in
        x86_64|amd64)
            log_info "架构: $ARCH ✓"
            ;;
        aarch64|arm64)
            log_info "架构: $ARCH ✓"
            log_warning "ARM64架构，某些功能可能受限"
            ;;
        *)
            log_error "不支持的架构: $ARCH"
            exit 1
            ;;
    esac

    # 检查是否为root用户
    if [[ $EUID -eq 0 ]]; then
        log_warning "检测到root用户，建议使用普通用户运行"
        if [[ "${FORCE:-false}" != "true" ]]; then
            read -p "是否继续? (y/N): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                exit 1
            fi
        fi
    fi

    # 检查sudo权限
    if ! sudo -n true 2>/dev/null; then
        log_warning "需要sudo权限来安装系统依赖"
        sudo -v || {
            log_error "无法获取sudo权限"
            exit 1
        }
    fi

    # 检查系统资源
    local mem_gb=$(free -g | awk '/^Mem:/{print $2}')
    local disk_gb=$(df -BG / | awk 'NR==2{print int($4)}')
    local cpu_cores=$(nproc)
    local load_avg=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | sed 's/,//')

    log_info "系统资源:"
    log_info "  CPU核心: ${cpu_cores}"
    log_info "  内存: ${mem_gb}GB"
    log_info "  可用磁盘: ${disk_gb}GB"
    log_info "  系统负载: ${load_avg}"

    # 资源检查
    local warnings=0
    if [[ $mem_gb -lt $MIN_MEMORY_GB ]]; then
        log_warning "内存不足${MIN_MEMORY_GB}GB，编译可能会失败"
        ((warnings++))
    elif [[ $mem_gb -lt $RECOMMENDED_MEMORY_GB ]]; then
        log_warning "内存少于推荐的${RECOMMENDED_MEMORY_GB}GB，编译速度可能较慢"
    fi

    if [[ $disk_gb -lt $MIN_DISK_GB ]]; then
        log_warning "磁盘空间不足${MIN_DISK_GB}GB，可能无法完成编译"
        ((warnings++))
    elif [[ $disk_gb -lt $RECOMMENDED_DISK_GB ]]; then
        log_warning "磁盘空间少于推荐的${RECOMMENDED_DISK_GB}GB"
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

# 检查并安装Docker
install_docker() {
    log_step "检查Docker环境..."

    local docker_installed=false
    local compose_installed=false

    # 检查Docker
    if command -v docker &> /dev/null; then
        local docker_version=$(docker --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
        log_info "Docker已安装: $docker_version"
        docker_installed=true

        # 检查Docker服务状态
        if ! docker info &> /dev/null; then
            log_warning "Docker服务未运行，尝试启动..."
            sudo systemctl start docker || {
                log_error "无法启动Docker服务"
                exit 1
            }
        fi
    else
        log_info "Docker未安装，开始安装..."

        # 根据系统选择安装方法
        case "$OS_ID" in
            ubuntu|debian)
                install_docker_debian
                ;;
            centos|rhel|fedora)
                install_docker_redhat
                ;;
            *)
                # 使用官方安装脚本
                install_docker_official
                ;;
        esac

        docker_installed=true
    fi

    # 检查Docker Compose
    if command -v docker-compose &> /dev/null; then
        local compose_version=$(docker-compose --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
        log_info "Docker Compose已安装: $compose_version"
        compose_installed=true
    else
        log_info "安装Docker Compose..."
        install_docker_compose
        compose_installed=true
    fi

    # 配置Docker用户权限
    if [[ $EUID -ne 0 ]] && ! groups $USER | grep -q docker; then
        log_info "添加用户到docker组..."
        sudo usermod -aG docker $USER
        log_warning "用户已添加到docker组，需要重新登录生效"
        log_warning "或者运行: newgrp docker"

        # 尝试使用newgrp临时生效
        if command -v newgrp &> /dev/null; then
            log_info "尝试临时激活docker组权限..."
            # 注意：newgrp在脚本中可能不会按预期工作
        fi
    fi

    # 验证Docker安装
    verify_docker_installation

    log_success "Docker环境检查完成"
}

# Debian/Ubuntu系统安装Docker
install_docker_debian() {
    log_info "在Debian/Ubuntu系统上安装Docker..."

    # 更新包索引
    sudo apt-get update

    # 安装必要的包
    sudo apt-get install -y \
        apt-transport-https \
        ca-certificates \
        curl \
        gnupg \
        lsb-release

    # 添加Docker官方GPG密钥
    curl -fsSL https://download.docker.com/linux/$OS_ID/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

    # 添加Docker仓库
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/$OS_ID $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

    # 安装Docker
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io

    # 启动并启用Docker服务
    sudo systemctl enable docker
    sudo systemctl start docker

    log_success "Docker安装完成"
}

# RedHat系系统安装Docker
install_docker_redhat() {
    log_info "在RedHat系系统上安装Docker..."

    # 安装必要的包
    sudo $PKG_MANAGER install -y yum-utils device-mapper-persistent-data lvm2

    # 添加Docker仓库
    sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo

    # 安装Docker
    sudo $PKG_MANAGER install -y docker-ce docker-ce-cli containerd.io

    # 启动并启用Docker服务
    sudo systemctl enable docker
    sudo systemctl start docker

    log_success "Docker安装完成"
}

# 使用官方脚本安装Docker
install_docker_official() {
    log_info "使用官方脚本安装Docker..."

    # 下载并执行官方安装脚本
    curl -fsSL https://get.docker.com | sudo sh

    # 启动并启用Docker服务
    sudo systemctl enable docker
    sudo systemctl start docker

    log_success "Docker安装完成"
}

# 安装Docker Compose
install_docker_compose() {
    log_info "安装Docker Compose..."

    # 获取最新版本号
    local latest_version
    if command -v curl &> /dev/null; then
        latest_version=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep -oE '"tag_name": "[^"]*"' | cut -d'"' -f4)
    fi

    # 如果无法获取最新版本，使用备用版本
    if [[ -z "$latest_version" ]]; then
        latest_version="v2.20.0"
        log_warning "无法获取最新版本，使用备用版本: $latest_version"
    fi

    # 下载Docker Compose
    local compose_url="https://github.com/docker/compose/releases/download/${latest_version}/docker-compose-$(uname -s)-$(uname -m)"

    sudo curl -L "$compose_url" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose

    # 创建符号链接（如果需要）
    if [[ ! -f /usr/bin/docker-compose ]]; then
        sudo ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose
    fi

    log_success "Docker Compose安装完成: $(docker-compose --version)"
}

# 验证Docker安装
verify_docker_installation() {
    log_info "验证Docker安装..."

    # 检查Docker版本
    if ! docker --version &> /dev/null; then
        log_error "Docker命令不可用"
        exit 1
    fi

    # 检查Docker服务
    if ! docker info &> /dev/null; then
        log_error "Docker服务未运行"
        exit 1
    fi

    # 检查Docker Compose
    if ! docker-compose --version &> /dev/null; then
        log_error "Docker Compose不可用"
        exit 1
    fi

    # 测试Docker运行
    log_info "测试Docker运行..."
    if docker run --rm hello-world &> /dev/null; then
        log_success "Docker运行测试通过"
    else
        log_warning "Docker运行测试失败，但可能不影响使用"
    fi
}

# 备份现有安装
backup_existing_installation() {
    if [[ ! -d "$INSTALL_DIR" ]]; then
        return 0
    fi

    log_step "备份现有安装..."

    local backup_name="openwrt-compiler-backup-$(date +%Y%m%d-%H%M%S)"
    local backup_path="$BACKUP_DIR/$backup_name"

    # 创建备份目录
    sudo mkdir -p "$BACKUP_DIR"

    # 停止现有服务
    if [[ -f "$INSTALL_DIR/docker-compose.yml" ]]; then
        log_info "停止现有服务..."
        cd "$INSTALL_DIR"
        docker-compose down 2>/dev/null || true
    fi

    # 备份安装目录
    log_info "备份到: $backup_path"
    sudo cp -r "$INSTALL_DIR" "$backup_path"

    # 备份配置文件
    if [[ -f "$INSTALL_DIR/.env" ]]; then
        sudo cp "$INSTALL_DIR/.env" "$backup_path/.env.backup"
    fi

    log_success "备份完成: $backup_path"

    # 记录备份信息
    echo "$(date): 备份到 $backup_path" | sudo tee -a "$BACKUP_DIR/backup.log" > /dev/null
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
        "build-essential" "python3" "python3-pip" "python3-venv"
    )

    # OpenWrt编译依赖
    local openwrt_packages=(
        "libncurses5-dev" "libncursesw5-dev" "zlib1g-dev" "gawk"
        "gettext" "libssl-dev" "xsltproc" "rsync" "subversion"
        "mercurial" "bzr" "ecj" "fastjar" "file" "g++" "java-propose-classpath"
        "libelf-dev" "python3-distutils" "python3-setuptools" "python3-dev"
        "swig" "aria2" "libtinfo5" "libgmp3-dev" "libmpc-dev" "libmpfr-dev"
        "libusb-1.0-0-dev" "libusb-dev" "liblzma-dev" "libsnmp-dev"
        "libevent-dev" "libavahi-client-dev" "libsqlite3-dev" "libpcre2-dev"
    )

    # 安装基础包
    log_info "安装基础工具..."
    sudo apt-get install -y "${basic_packages[@]}"

    # 安装OpenWrt编译依赖（仅在非Docker模式下）
    if [[ "$INSTALL_MODE" != "docker" ]]; then
        log_info "安装OpenWrt编译依赖..."
        sudo apt-get install -y "${openwrt_packages[@]}"
    fi

    log_success "系统依赖安装完成"
}

# RedHat系系统依赖
install_dependencies_redhat() {
    log_info "安装RedHat系系统依赖..."

    # 基础工具
    local basic_packages=(
        "curl" "wget" "git" "unzip" "vim" "htop" "tree"
        "gcc" "gcc-c++" "make" "python3" "python3-pip"
    )

    # OpenWrt编译依赖
    local openwrt_packages=(
        "ncurses-devel" "zlib-devel" "gawk" "gettext" "openssl-devel"
        "libxslt" "rsync" "subversion" "mercurial" "bzr" "java-1.8.0-openjdk"
        "elfutils-libelf-devel" "python3-devel" "swig" "gmp-devel"
        "mpfr-devel" "libmpc-devel" "libusb-devel" "xz-devel"
        "net-snmp-devel" "libevent-devel" "avahi-devel" "sqlite-devel"
        "pcre2-devel"
    )

    # 安装基础包
    log_info "安装基础工具..."
    sudo $PKG_MANAGER install -y "${basic_packages[@]}"

    # 安装OpenWrt编译依赖（仅在非Docker模式下）
    if [[ "$INSTALL_MODE" != "docker" ]]; then
        log_info "安装OpenWrt编译依赖..."
        sudo $PKG_MANAGER install -y "${openwrt_packages[@]}"
    fi

    log_success "系统依赖安装完成"
}

# 下载项目代码
download_project() {
    log_step "下载项目代码..."

    # 检查Git
    if ! command -v git &> /dev/null; then
        log_info "安装Git..."
        case "$PKG_MANAGER" in
            apt)
                sudo apt-get update && sudo apt-get install -y git
                ;;
            yum|dnf)
                sudo $PKG_MANAGER install -y git
                ;;
            *)
                log_error "无法安装Git，请手动安装"
                exit 1
                ;;
        esac
    fi

    # 处理现有安装
    if [[ -d "$INSTALL_DIR" ]]; then
        if [[ "${BACKUP:-false}" == "true" ]]; then
            backup_existing_installation
        else
            log_warning "目录 $INSTALL_DIR 已存在"
            if [[ "${FORCE:-false}" != "true" ]]; then
                read -p "是否删除并重新安装? (y/N): " -n 1 -r
                echo
                if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                    log_error "安装取消"
                    exit 1
                fi
            fi
        fi

        # 停止现有服务
        if [[ -f "$INSTALL_DIR/docker-compose.yml" ]]; then
            log_info "停止现有服务..."
            cd "$INSTALL_DIR"
            docker-compose down 2>/dev/null || true
        fi

        # 删除现有目录
        sudo rm -rf "$INSTALL_DIR"
    fi

    # 创建安装目录
    log_info "创建安装目录: $INSTALL_DIR"
    sudo mkdir -p "$(dirname "$INSTALL_DIR")"

    # 克隆项目
    log_info "从 $REPO_URL 克隆项目 (分支: ${GIT_BRANCH:-main})..."

    local git_cmd="git clone"
    if [[ -n "${GIT_BRANCH:-}" ]]; then
        git_cmd="$git_cmd -b $GIT_BRANCH"
    fi
    git_cmd="$git_cmd $REPO_URL $INSTALL_DIR"

    if ! sudo $git_cmd; then
        log_error "项目克隆失败"
        exit 1
    fi

    # 设置权限
    sudo chown -R $USER:$USER "$INSTALL_DIR"

    # 显示项目信息
    cd "$INSTALL_DIR"
    local commit_hash=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
    local commit_date=$(git log -1 --format=%cd --date=short 2>/dev/null || echo "unknown")

    log_info "项目信息:"
    log_info "  提交哈希: $commit_hash"
    log_info "  提交日期: $commit_date"
    log_info "  分支: $(git branch --show-current 2>/dev/null || echo 'unknown')"

    log_success "项目代码下载完成"
}

# 配置环境
configure_environment() {
    log_step "配置环境..."

    cd "$INSTALL_DIR"

    # 检测本机IP地址
    local local_ip
    local_ip=$(ip route get 1.1.1.1 2>/dev/null | grep -oP 'src \K\S+' || echo "localhost")

    # 创建环境变量文件
    if [[ ! -f ".env" ]] || [[ "${FORCE:-false}" == "true" ]]; then
        log_info "创建环境配置文件..."
        cat > .env << EOF
# OpenWrt编译器配置 - 自动生成于 $(date)
PORT=$PORT
TZ=Asia/Shanghai
DEBUG=${DEBUG:-false}

# 服务配置
HOST=0.0.0.0
WORKERS=4
MAX_COMPILE_JOBS=2

# 网络配置
LOCAL_IP=$local_ip
DOWNLOAD_BASE_URL=http://$local_ip:$PORT

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

# Docker配置
DOCKER_BUILDKIT=1
COMPOSE_DOCKER_CLI_BUILD=1
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
        log_debug "创建目录: $dir"
    done

    # 设置目录权限
    chmod 755 workspace logs data tmp
    chmod 777 tmp  # 临时目录需要写权限

    # 创建配置文件模板
    create_config_templates

    # 设置Git配置（如果需要）
    setup_git_config

    log_success "环境配置完成"
}

# 创建配置文件模板
create_config_templates() {
    log_info "创建配置文件模板..."

    # 创建设备配置模板目录
    mkdir -p data/configs/templates

    # 创建基础设备配置
    cat > data/configs/templates/base.config << 'EOF'
# OpenWrt基础配置模板
CONFIG_TARGET_x86=y
CONFIG_TARGET_x86_64=y
CONFIG_TARGET_x86_64_DEVICE_generic=y

# 基础包
CONFIG_PACKAGE_luci=y
CONFIG_PACKAGE_luci-ssl=y
CONFIG_PACKAGE_luci-app-firewall=y
CONFIG_PACKAGE_luci-app-opkg=y

# 网络工具
CONFIG_PACKAGE_curl=y
CONFIG_PACKAGE_wget=y
CONFIG_PACKAGE_htop=y
CONFIG_PACKAGE_nano=y

# 文件系统支持
CONFIG_PACKAGE_kmod-fs-ext4=y
CONFIG_PACKAGE_kmod-fs-vfat=y
CONFIG_PACKAGE_kmod-fs-ntfs=y
EOF

    # 创建iStore配置模板
    if [[ "${ENABLE_ISTORE:-true}" == "true" ]]; then
        cat > data/configs/templates/istore.config << 'EOF'
# iStore商店配置
CONFIG_PACKAGE_luci-app-store=y
CONFIG_PACKAGE_luci-lib-taskd=y
CONFIG_PACKAGE_luci-lib-xterm=y
CONFIG_PACKAGE_taskd=y
CONFIG_PACKAGE_quickstart=y
EOF
    fi

    log_success "配置文件模板创建完成"
}

# 设置Git配置
setup_git_config() {
    if ! git config --global user.name &>/dev/null; then
        log_info "设置Git用户配置..."
        git config --global user.name "OpenWrt Compiler"
        git config --global user.email "compiler@openwrt.local"
        git config --global init.defaultBranch main
        log_success "Git配置完成"
    fi
}

# 构建和启动服务
start_service() {
    log_step "构建和启动服务..."

    cd "$INSTALL_DIR"

    case "$INSTALL_MODE" in
        docker)
            start_docker_service
            ;;
        native)
            start_native_service
            ;;
        test)
            run_test_mode
            ;;
        *)
            log_error "未知安装模式: $INSTALL_MODE"
            exit 1
            ;;
    esac
}

# Docker模式启动
start_docker_service() {
    log_info "使用Docker模式启动服务..."

    # 检查Docker Compose文件
    if [[ ! -f "docker-compose.yml" ]]; then
        log_error "未找到docker-compose.yml文件"
        exit 1
    fi

    # 设置环境变量
    export PORT=$PORT
    export INSTALL_MODE=$INSTALL_MODE

    # 拉取基础镜像（可选，加速构建）
    log_info "拉取基础镜像..."
    docker pull ubuntu:22.04 2>/dev/null || log_warning "无法拉取基础镜像，将在构建时下载"

    # 构建镜像
    log_info "构建Docker镜像..."
    show_progress 1 4

    if ! docker-compose build --no-cache; then
        log_error "Docker镜像构建失败"
        exit 1
    fi
    show_progress 2 4

    # 启动服务
    log_info "启动Docker服务..."
    if ! docker-compose up -d; then
        log_error "服务启动失败"
        exit 1
    fi
    show_progress 3 4

    # 等待服务启动
    wait_for_service
    show_progress 4 4
    echo  # 换行

    log_success "Docker服务启动成功"
}

# 原生模式启动
start_native_service() {
    log_info "使用原生模式启动服务..."

    # 检查Python环境
    if ! command -v python3 &> /dev/null; then
        log_error "Python3未安装"
        exit 1
    fi

    # 创建虚拟环境
    if [[ ! -d "venv" ]]; then
        log_info "创建Python虚拟环境..."
        python3 -m venv venv
    fi

    # 激活虚拟环境并安装依赖
    source venv/bin/activate

    if [[ -f "requirements.txt" ]]; then
        log_info "安装Python依赖..."
        pip install --upgrade pip
        pip install -r requirements.txt
    fi

    # 启动服务
    log_info "启动原生服务..."
    nohup python3 backend/app.py --host 0.0.0.0 --port $PORT > logs/app.log 2>&1 &
    echo $! > tmp/app.pid

    # 等待服务启动
    wait_for_service

    log_success "原生服务启动成功"
}

# 测试模式
run_test_mode() {
    log_info "运行测试模式..."

    # 创建简单的测试页面
    mkdir -p test-html
    cat > test-html/index.html << 'EOF'
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OpenWrt编译器 - 测试模式</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            text-align: center;
            padding: 50px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .container {
            background: rgba(255,255,255,0.1);
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.2);
        }
        h1 { color: #fff; margin-bottom: 20px; }
        .success { color: #4CAF50; font-size: 18px; font-weight: bold; }
        .info { margin: 15px 0; }
        .time { font-family: monospace; background: rgba(0,0,0,0.2); padding: 5px 10px; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 OpenWrt编译器</h1>
        <div class="success">✅ 测试模式运行成功！</div>
        <div class="info">
            <p><strong>模式:</strong> 测试模式</p>
            <p><strong>端口:</strong> PORT_PLACEHOLDER</p>
            <p><strong>状态:</strong> 运行中</p>
            <p><strong>时间:</strong> <span class="time" id="time"></span></p>
        </div>
        <div class="info">
            <h3>🎯 下一步</h3>
            <p>1. 测试成功，可以部署完整版本</p>
            <p>2. 配置邮箱通知（可选）</p>
            <p>3. 开始编译OpenWrt固件</p>
        </div>
    </div>
    <script>
        function updateTime() {
            document.getElementById('time').textContent = new Date().toLocaleString('zh-CN');
        }
        updateTime();
        setInterval(updateTime, 1000);
    </script>
</body>
</html>
EOF

    # 替换端口占位符
    sed -i "s/PORT_PLACEHOLDER/$PORT/g" test-html/index.html

    # 创建测试用的docker-compose.yml
    cat > docker-compose.test.yml << EOF
version: '3.8'
services:
  test-web:
    image: nginx:alpine
    container_name: openwrt-test-$PORT
    ports:
      - "$PORT:80"
    volumes:
      - ./test-html:/usr/share/nginx/html
    restart: unless-stopped
EOF

    # 启动测试服务
    log_info "启动测试服务..."
    docker-compose -f docker-compose.test.yml up -d

    # 等待服务启动
    wait_for_service

    log_success "测试模式启动成功"
}

# 等待服务启动
wait_for_service() {
    log_info "等待服务启动..."

    local max_attempts=30
    local attempt=1
    local health_url="http://localhost:$PORT"

    # 如果是测试模式，直接检查根路径
    if [[ "$INSTALL_MODE" == "test" ]]; then
        health_url="http://localhost:$PORT/"
    else
        health_url="http://localhost:$PORT/health"
    fi

    while [[ $attempt -le $max_attempts ]]; do
        if curl -f -s "$health_url" &> /dev/null; then
            log_success "服务响应正常 (尝试 $attempt/$max_attempts)"
            return 0
        fi

        log_debug "等待服务启动... ($attempt/$max_attempts)"
        sleep 2
        ((attempt++))
    done

    log_warning "服务可能未完全启动，请稍后手动检查"
    log_warning "检查命令: curl -I http://localhost:$PORT"
    return 1
}

# 显示安装结果
show_result() {
    local local_ip
    local_ip=$(ip route get 1.1.1.1 2>/dev/null | grep -oP 'src \K\S+' || echo "localhost")

    echo ""
    echo -e "${GREEN}🎉 OpenWrt编译器安装完成！${NC}"
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
    echo -e "   安装模式: ${YELLOW}$INSTALL_MODE${NC}"
    echo -e "   服务端口: ${YELLOW}$PORT${NC}"
    echo -e "   安装时间: ${YELLOW}$(date)${NC}"
    echo ""

    # 显示管理命令
    echo -e "${CYAN}🔧 管理命令:${NC}"
    case "$INSTALL_MODE" in
        docker)
            echo -e "   启动服务: ${YELLOW}cd $INSTALL_DIR && docker-compose up -d${NC}"
            echo -e "   停止服务: ${YELLOW}cd $INSTALL_DIR && docker-compose down${NC}"
            echo -e "   查看日志: ${YELLOW}cd $INSTALL_DIR && docker-compose logs -f${NC}"
            echo -e "   重启服务: ${YELLOW}cd $INSTALL_DIR && docker-compose restart${NC}"
            echo -e "   查看状态: ${YELLOW}cd $INSTALL_DIR && docker-compose ps${NC}"
            ;;
        native)
            echo -e "   启动服务: ${YELLOW}cd $INSTALL_DIR && source venv/bin/activate && python backend/app.py${NC}"
            echo -e "   停止服务: ${YELLOW}kill \$(cat $INSTALL_DIR/tmp/app.pid)${NC}"
            echo -e "   查看日志: ${YELLOW}tail -f $INSTALL_DIR/logs/app.log${NC}"
            ;;
        test)
            echo -e "   停止测试: ${YELLOW}cd $INSTALL_DIR && docker-compose -f docker-compose.test.yml down${NC}"
            echo -e "   查看状态: ${YELLOW}cd $INSTALL_DIR && docker-compose -f docker-compose.test.yml ps${NC}"
            ;;
    esac
    echo ""

    # 显示配置信息
    echo -e "${CYAN}⚙️  配置文件:${NC}"
    echo -e "   环境配置: ${YELLOW}$INSTALL_DIR/.env${NC}"
    echo -e "   编辑配置: ${YELLOW}nano $INSTALL_DIR/.env${NC}"
    if [[ "$INSTALL_MODE" == "docker" ]]; then
        echo -e "   重启生效: ${YELLOW}cd $INSTALL_DIR && docker-compose restart${NC}"
    fi
    echo ""

    # 显示功能特性
    echo -e "${CYAN}🚀 功能特性:${NC}"
    echo -e "   ✅ 多用户支持，独立编译环境"
    echo -e "   ✅ 智能设备搜索和配置"
    echo -e "   ✅ Web版menuconfig界面"
    echo -e "   ✅ 自动集成iStore商店"
    echo -e "   ✅ 邮件通知编译结果"
    echo -e "   ✅ 实时编译日志查看"
    echo -e "   ✅ 固件下载和管理"
    echo ""

    # 显示下一步操作
    echo -e "${CYAN}📋 下一步操作:${NC}"
    echo -e "   1. 访问Web界面创建用户账户"
    echo -e "   2. 选择目标设备和配置"
    echo -e "   3. 开始编译OpenWrt固件"
    if [[ "$INSTALL_MODE" == "test" ]]; then
        echo -e "   4. 测试成功后可升级到完整版本"
    fi
    echo ""

    # 显示故障排除
    echo -e "${CYAN}🔍 故障排除:${NC}"
    echo -e "   检查服务: ${YELLOW}curl -I http://localhost:$PORT${NC}"
    echo -e "   查看日志: ${YELLOW}cat $LOG_FILE${NC}"
    if [[ "$INSTALL_MODE" == "docker" ]]; then
        echo -e "   容器状态: ${YELLOW}docker ps | grep openwrt${NC}"
        echo -e "   容器日志: ${YELLOW}docker logs openwrt-compiler${NC}"
    fi
    echo ""

    # 显示备份信息
    if [[ -d "$BACKUP_DIR" ]]; then
        echo -e "${CYAN}💾 备份信息:${NC}"
        echo -e "   备份目录: ${YELLOW}$BACKUP_DIR${NC}"
        echo -e "   备份列表: ${YELLOW}ls -la $BACKUP_DIR${NC}"
        echo ""
    fi

    echo -e "${GREEN}✨ 享受OpenWrt固件编译之旅！${NC}"
    echo -e "${WHITE}📖 更多信息请查看: https://github.com/moyanjiang/openwrt_make_web${NC}"
    echo ""
}

# 显示安装摘要
show_install_summary() {
    echo ""
    echo -e "${WHITE}📊 安装摘要${NC}"
    echo -e "${WHITE}===================${NC}"
    echo -e "脚本版本: ${CYAN}$SCRIPT_VERSION${NC}"
    echo -e "安装模式: ${CYAN}$INSTALL_MODE${NC}"
    echo -e "安装目录: ${CYAN}$INSTALL_DIR${NC}"
    echo -e "服务端口: ${CYAN}$PORT${NC}"
    echo -e "Git仓库: ${CYAN}$REPO_URL${NC}"
    if [[ -n "${GIT_BRANCH:-}" ]]; then
        echo -e "Git分支: ${CYAN}$GIT_BRANCH${NC}"
    fi
    echo -e "系统信息: ${CYAN}$OS_NAME $OS_VERSION ($ARCH)${NC}"
    echo -e "安装时间: ${CYAN}$(date)${NC}"
    echo -e "安装日志: ${CYAN}$LOG_FILE${NC}"
    echo ""
}

# 主函数
main() {
    # 初始化日志文件
    echo "OpenWrt编译器安装日志 - $(date)" > "$LOG_FILE"

    # 解析命令行参数
    PORT=$DEFAULT_PORT
    REPO_URL=$DEFAULT_REPO
    INSTALL_MODE="docker"
    AUTO_START=true
    DEV_MODE=false
    DEBUG=false
    FORCE=false
    BACKUP=false
    OFFLINE=false
    GIT_BRANCH=""

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
            -m|--mode)
                INSTALL_MODE="$2"
                shift 2
                ;;
            -b|--branch)
                GIT_BRANCH="$2"
                shift 2
                ;;
            --backup)
                BACKUP=true
                shift
                ;;
            --no-start)
                AUTO_START=false
                shift
                ;;
            --dev)
                DEV_MODE=true
                GIT_BRANCH="develop"
                shift
                ;;
            --debug)
                DEBUG=true
                shift
                ;;
            --force)
                FORCE=true
                shift
                ;;
            --offline)
                OFFLINE=true
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

    if [[ ! "$INSTALL_MODE" =~ ^(docker|native|test)$ ]]; then
        log_error "无效安装模式: $INSTALL_MODE"
        log_error "支持的模式: docker, native, test"
        exit 1
    fi

    # 显示横幅
    show_banner

    # 检查网络连接（除非离线模式）
    if [[ "$OFFLINE" != "true" ]]; then
        check_network
    fi

    # 显示配置信息
    echo -e "${CYAN}📋 安装配置:${NC}"
    echo -e "   安装模式: ${YELLOW}$INSTALL_MODE${NC}"
    echo -e "   服务端口: ${YELLOW}$PORT${NC}"
    echo -e "   安装目录: ${YELLOW}$INSTALL_DIR${NC}"
    echo -e "   Git仓库: ${YELLOW}$REPO_URL${NC}"
    if [[ -n "$GIT_BRANCH" ]]; then
        echo -e "   Git分支: ${YELLOW}$GIT_BRANCH${NC}"
    fi
    echo -e "   开发模式: ${YELLOW}$DEV_MODE${NC}"
    echo -e "   调试模式: ${YELLOW}$DEBUG${NC}"
    echo -e "   强制安装: ${YELLOW}$FORCE${NC}"
    echo -e "   备份现有: ${YELLOW}$BACKUP${NC}"
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
    log_step "开始安装流程..."

    # 1. 系统检查
    check_system

    # 2. 安装系统依赖
    install_system_dependencies

    # 3. 安装Docker（如果需要）
    if [[ "$INSTALL_MODE" == "docker" || "$INSTALL_MODE" == "test" ]]; then
        install_docker
    fi

    # 4. 下载项目代码
    if [[ "$OFFLINE" != "true" ]]; then
        download_project
    else
        log_warning "离线模式，跳过项目下载"
    fi

    # 5. 配置环境
    configure_environment

    # 6. 启动服务（如果需要）
    if [[ "$AUTO_START" == "true" ]]; then
        start_service
    fi

    # 计算安装时间
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    local minutes=$((duration / 60))
    local seconds=$((duration % 60))

    # 显示结果
    if [[ "$AUTO_START" == "true" ]]; then
        show_result
    else
        log_success "安装完成，但未启动服务"
        echo ""
        echo -e "${CYAN}手动启动命令:${NC}"
        case "$INSTALL_MODE" in
            docker|test)
                echo -e "   ${YELLOW}cd $INSTALL_DIR && docker-compose up -d${NC}"
                ;;
            native)
                echo -e "   ${YELLOW}cd $INSTALL_DIR && source venv/bin/activate && python backend/app.py${NC}"
                ;;
        esac
    fi

    # 显示安装摘要
    show_install_summary

    log_success "安装完成！总耗时: ${minutes}分${seconds}秒"
    log_info "详细日志已保存到: $LOG_FILE"
}

# 运行主函数
main "$@"
