#!/bin/bash

# OpenWrt编译器Docker部署脚本
# 支持开发环境和生产环境部署

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 显示帮助信息
show_help() {
    cat << EOF
OpenWrt编译器Docker部署脚本

用法:
    $0 [选项] [命令]

命令:
    dev         启动开发环境
    prod        启动生产环境
    stop        停止所有服务
    restart     重启服务
    logs        查看日志
    status      查看服务状态
    clean       清理Docker资源
    backup      备份数据
    restore     恢复数据

选项:
    -h, --help      显示帮助信息
    -v, --verbose   详细输出
    -f, --force     强制执行
    --no-cache      构建时不使用缓存

示例:
    $0 dev                  # 启动开发环境
    $0 prod                 # 启动生产环境
    $0 logs backend         # 查看后端日志
    $0 clean --force        # 强制清理所有资源

EOF
}

# 检查Docker环境
check_docker() {
    log_info "检查Docker环境..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装，请先安装Docker"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose未安装，请先安装Docker Compose"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        log_error "Docker服务未运行，请启动Docker服务"
        exit 1
    fi
    
    log_success "Docker环境检查通过"
}

# 创建必要的目录
create_directories() {
    log_info "创建必要的目录..."
    
    mkdir -p workspace/users
    mkdir -p logs
    mkdir -p backend/config_templates
    mkdir -p docker/ssl
    
    # 设置权限
    chmod 755 workspace
    chmod 755 logs
    
    log_success "目录创建完成"
}

# 生成SSL证书（自签名，仅用于开发）
generate_ssl_cert() {
    if [ ! -f "docker/ssl/cert.pem" ] || [ ! -f "docker/ssl/key.pem" ]; then
        log_info "生成SSL证书..."
        
        openssl req -x509 -newkey rsa:4096 -keyout docker/ssl/key.pem -out docker/ssl/cert.pem -days 365 -nodes \
            -subj "/C=CN/ST=Beijing/L=Beijing/O=OpenWrt Compiler/CN=localhost" 2>/dev/null || {
            log_warning "SSL证书生成失败，将使用HTTP"
        }
        
        if [ -f "docker/ssl/cert.pem" ]; then
            log_success "SSL证书生成完成"
        fi
    fi
}

# 检查环境变量
check_env() {
    log_info "检查环境变量..."
    
    if [ ! -f ".env" ]; then
        log_warning ".env文件不存在，创建示例文件..."
        cat > .env << EOF
# 邮箱配置（可选）
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=
MAIL_PASSWORD=
MAIL_DEFAULT_SENDER=

# 下载基础URL
DOWNLOAD_BASE_URL=http://localhost:9963

# Grafana配置（可选）
GRAFANA_USER=admin
GRAFANA_PASSWORD=admin123
EOF
        log_info "请编辑.env文件配置邮箱等信息"
    fi
}

# 启动开发环境
start_dev() {
    log_info "启动开发环境..."
    
    check_docker
    create_directories
    check_env
    
    # 构建并启动服务
    if [ "$NO_CACHE" = "true" ]; then
        docker-compose -f docker-compose.yml -f docker-compose.dev.yml build --no-cache
    else
        docker-compose -f docker-compose.yml -f docker-compose.dev.yml build
    fi
    
    docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
    
    log_success "开发环境启动完成"
    log_info "前端地址: http://localhost:9963"
    log_info "后端API: http://localhost:5000"
    log_info "Redis管理: http://localhost:8080"
    log_info "邮件测试: http://localhost:8025"
}

# 启动生产环境
start_prod() {
    log_info "启动生产环境..."
    
    check_docker
    create_directories
    generate_ssl_cert
    check_env
    
    # 构建并启动服务
    if [ "$NO_CACHE" = "true" ]; then
        docker-compose -f docker-compose.yml -f docker-compose.prod.yml build --no-cache
    else
        docker-compose -f docker-compose.yml -f docker-compose.prod.yml build
    fi
    
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
    
    log_success "生产环境启动完成"
    log_info "访问地址: http://localhost:9963"
    log_info "Nginx代理: http://localhost:80"
    log_info "监控面板: http://localhost:3000"
}

# 停止服务
stop_services() {
    log_info "停止所有服务..."
    
    docker-compose -f docker-compose.yml -f docker-compose.dev.yml down 2>/dev/null || true
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml down 2>/dev/null || true
    
    log_success "服务已停止"
}

# 重启服务
restart_services() {
    log_info "重启服务..."
    
    stop_services
    sleep 2
    
    if [ -f "docker-compose.dev.yml" ] && docker-compose -f docker-compose.yml -f docker-compose.dev.yml ps | grep -q "Up"; then
        start_dev
    else
        start_prod
    fi
}

# 查看日志
show_logs() {
    local service=$1
    
    if [ -n "$service" ]; then
        log_info "查看 $service 服务日志..."
        docker-compose logs -f "$service"
    else
        log_info "查看所有服务日志..."
        docker-compose logs -f
    fi
}

# 查看服务状态
show_status() {
    log_info "服务状态:"
    echo
    
    docker-compose ps
    echo
    
    log_info "容器资源使用:"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"
}

# 清理Docker资源
clean_docker() {
    log_warning "清理Docker资源..."
    
    if [ "$FORCE" = "true" ]; then
        log_warning "强制清理所有资源..."
        
        # 停止并删除容器
        docker-compose -f docker-compose.yml -f docker-compose.dev.yml down --volumes --remove-orphans 2>/dev/null || true
        docker-compose -f docker-compose.yml -f docker-compose.prod.yml down --volumes --remove-orphans 2>/dev/null || true
        
        # 删除镜像
        docker images | grep openwrt-compiler | awk '{print $3}' | xargs -r docker rmi -f
        
        # 清理未使用的资源
        docker system prune -af --volumes
        
        log_success "强制清理完成"
    else
        # 温和清理
        docker-compose down --remove-orphans
        docker system prune -f
        
        log_success "清理完成"
    fi
}

# 备份数据
backup_data() {
    local backup_dir="backup/$(date +%Y%m%d_%H%M%S)"
    
    log_info "备份数据到 $backup_dir..."
    
    mkdir -p "$backup_dir"
    
    # 备份工作空间
    if [ -d "workspace" ]; then
        tar -czf "$backup_dir/workspace.tar.gz" workspace/
        log_success "工作空间备份完成"
    fi
    
    # 备份日志
    if [ -d "logs" ]; then
        tar -czf "$backup_dir/logs.tar.gz" logs/
        log_success "日志备份完成"
    fi
    
    # 备份配置
    if [ -f ".env" ]; then
        cp .env "$backup_dir/"
        log_success "配置文件备份完成"
    fi
    
    log_success "数据备份完成: $backup_dir"
}

# 恢复数据
restore_data() {
    local backup_dir=$1
    
    if [ -z "$backup_dir" ]; then
        log_error "请指定备份目录"
        exit 1
    fi
    
    if [ ! -d "$backup_dir" ]; then
        log_error "备份目录不存在: $backup_dir"
        exit 1
    fi
    
    log_info "从 $backup_dir 恢复数据..."
    
    # 恢复工作空间
    if [ -f "$backup_dir/workspace.tar.gz" ]; then
        tar -xzf "$backup_dir/workspace.tar.gz"
        log_success "工作空间恢复完成"
    fi
    
    # 恢复日志
    if [ -f "$backup_dir/logs.tar.gz" ]; then
        tar -xzf "$backup_dir/logs.tar.gz"
        log_success "日志恢复完成"
    fi
    
    # 恢复配置
    if [ -f "$backup_dir/.env" ]; then
        cp "$backup_dir/.env" .
        log_success "配置文件恢复完成"
    fi
    
    log_success "数据恢复完成"
}

# 解析命令行参数
VERBOSE=false
FORCE=false
NO_CACHE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -f|--force)
            FORCE=true
            shift
            ;;
        --no-cache)
            NO_CACHE=true
            shift
            ;;
        dev)
            start_dev
            exit 0
            ;;
        prod)
            start_prod
            exit 0
            ;;
        stop)
            stop_services
            exit 0
            ;;
        restart)
            restart_services
            exit 0
            ;;
        logs)
            show_logs $2
            exit 0
            ;;
        status)
            show_status
            exit 0
            ;;
        clean)
            clean_docker
            exit 0
            ;;
        backup)
            backup_data
            exit 0
            ;;
        restore)
            restore_data $2
            exit 0
            ;;
        *)
            log_error "未知参数: $1"
            show_help
            exit 1
            ;;
    esac
done

# 如果没有指定命令，显示帮助
show_help
