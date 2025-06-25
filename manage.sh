#!/bin/bash

# OpenWrt编译器管理脚本
# 提供便捷的管理命令

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m'

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

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
${WHITE}OpenWrt编译器管理脚本${NC}

${CYAN}用法:${NC}
    $0 <命令> [选项]

${CYAN}命令:${NC}
    ${GREEN}start${NC}           启动所有服务
    ${GREEN}stop${NC}            停止所有服务
    ${GREEN}restart${NC}         重启所有服务
    ${GREEN}status${NC}          查看服务状态
    ${GREEN}logs${NC}            查看日志
    ${GREEN}build${NC}           构建镜像
    ${GREEN}update${NC}          更新代码并重启
    ${GREEN}backup${NC}          备份数据
    ${GREEN}restore${NC}         恢复数据
    ${GREEN}clean${NC}           清理缓存和临时文件
    ${GREEN}shell${NC}           进入容器shell
    ${GREEN}health${NC}          健康检查
    ${GREEN}install${NC}         运行安装脚本

${CYAN}示例:${NC}
    $0 start                # 启动服务
    $0 logs -f              # 实时查看日志
    $0 shell openwrt-compiler  # 进入主容器
    $0 backup /path/to/backup  # 备份到指定目录

EOF
}

# 检查Docker环境
check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose未安装"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        log_error "Docker服务未运行"
        exit 1
    fi
}

# 启动服务
start_service() {
    log_info "启动OpenWrt编译器服务..."
    check_docker
    
    # 创建必要目录
    mkdir -p workspace/users workspace/shared/{cache,downloads,ccache}
    mkdir -p logs/{compile,system,access,nginx}
    mkdir -p data/{configs,firmware,uploads,ssl}
    mkdir -p tmp
    
    # 启动服务
    docker-compose up -d
    
    # 等待服务启动
    log_info "等待服务启动..."
    sleep 10
    
    # 检查服务状态
    if docker-compose ps | grep -q "Up"; then
        log_success "服务启动成功"
        show_access_info
    else
        log_error "服务启动失败"
        docker-compose logs
        exit 1
    fi
}

# 停止服务
stop_service() {
    log_info "停止OpenWrt编译器服务..."
    check_docker
    docker-compose down
    log_success "服务已停止"
}

# 重启服务
restart_service() {
    log_info "重启OpenWrt编译器服务..."
    stop_service
    start_service
}

# 查看服务状态
show_status() {
    check_docker
    echo -e "${CYAN}=== 服务状态 ===${NC}"
    docker-compose ps
    echo ""
    echo -e "${CYAN}=== 资源使用 ===${NC}"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"
}

# 查看日志
show_logs() {
    check_docker
    if [[ $# -gt 1 ]]; then
        docker-compose logs "${@:2}"
    else
        docker-compose logs --tail=100
    fi
}

# 构建镜像
build_image() {
    log_info "构建Docker镜像..."
    check_docker
    docker-compose build --no-cache
    log_success "镜像构建完成"
}

# 更新代码
update_code() {
    log_info "更新代码并重启服务..."
    
    # 拉取最新代码
    git pull origin main
    
    # 重新构建并启动
    docker-compose down
    docker-compose build
    docker-compose up -d
    
    log_success "更新完成"
}

# 备份数据
backup_data() {
    local backup_dir="${1:-./backup-$(date +%Y%m%d-%H%M%S)}"
    log_info "备份数据到: $backup_dir"
    
    mkdir -p "$backup_dir"
    
    # 备份工作空间
    if [[ -d "workspace" ]]; then
        cp -r workspace "$backup_dir/"
    fi
    
    # 备份数据目录
    if [[ -d "data" ]]; then
        cp -r data "$backup_dir/"
    fi
    
    # 备份配置文件
    cp .env "$backup_dir/" 2>/dev/null || true
    cp docker-compose.yml "$backup_dir/"
    
    # 备份数据库（如果有）
    if docker-compose ps | grep -q redis; then
        docker-compose exec redis redis-cli BGSAVE
        docker cp "$(docker-compose ps -q redis):/data/dump.rdb" "$backup_dir/"
    fi
    
    log_success "备份完成: $backup_dir"
}

# 恢复数据
restore_data() {
    local backup_dir="$1"
    if [[ -z "$backup_dir" || ! -d "$backup_dir" ]]; then
        log_error "请指定有效的备份目录"
        exit 1
    fi
    
    log_info "从备份恢复数据: $backup_dir"
    
    # 停止服务
    docker-compose down
    
    # 恢复数据
    if [[ -d "$backup_dir/workspace" ]]; then
        rm -rf workspace
        cp -r "$backup_dir/workspace" .
    fi
    
    if [[ -d "$backup_dir/data" ]]; then
        rm -rf data
        cp -r "$backup_dir/data" .
    fi
    
    # 恢复配置
    if [[ -f "$backup_dir/.env" ]]; then
        cp "$backup_dir/.env" .
    fi
    
    # 启动服务
    docker-compose up -d
    
    log_success "数据恢复完成"
}

# 清理缓存
clean_cache() {
    log_info "清理缓存和临时文件..."
    
    # 清理Docker
    docker system prune -f
    docker volume prune -f
    
    # 清理本地缓存
    rm -rf tmp/*
    rm -rf workspace/shared/cache/*
    
    log_success "清理完成"
}

# 进入容器shell
enter_shell() {
    local container="${1:-openwrt-compiler}"
    check_docker
    
    if docker ps | grep -q "$container"; then
        log_info "进入容器: $container"
        docker exec -it "$container" /bin/bash
    else
        log_error "容器 $container 未运行"
        exit 1
    fi
}

# 健康检查
health_check() {
    check_docker
    
    echo -e "${CYAN}=== 健康检查 ===${NC}"
    
    # 检查容器状态
    local containers=$(docker-compose ps -q)
    for container in $containers; do
        local name=$(docker inspect --format='{{.Name}}' "$container" | sed 's/\///')
        local health=$(docker inspect --format='{{.State.Health.Status}}' "$container" 2>/dev/null || echo "no-health-check")
        local status=$(docker inspect --format='{{.State.Status}}' "$container")
        
        if [[ "$status" == "running" ]]; then
            if [[ "$health" == "healthy" ]]; then
                echo -e "  ${GREEN}✓${NC} $name: 运行中 (健康)"
            elif [[ "$health" == "no-health-check" ]]; then
                echo -e "  ${YELLOW}?${NC} $name: 运行中 (无健康检查)"
            else
                echo -e "  ${RED}✗${NC} $name: 运行中 (不健康)"
            fi
        else
            echo -e "  ${RED}✗${NC} $name: $status"
        fi
    done
    
    # 检查端口
    local port=$(grep "PORT=" .env 2>/dev/null | cut -d'=' -f2 || echo "9963")
    if curl -f -s "http://localhost:$port/health" &> /dev/null; then
        echo -e "  ${GREEN}✓${NC} Web服务: 可访问 (端口 $port)"
    else
        echo -e "  ${RED}✗${NC} Web服务: 不可访问 (端口 $port)"
    fi
}

# 显示访问信息
show_access_info() {
    local port=$(grep "PORT=" .env 2>/dev/null | cut -d'=' -f2 || echo "9963")
    local ip=$(ip route get 1.1.1.1 2>/dev/null | grep -oP 'src \K\S+' || echo "localhost")
    
    echo ""
    echo -e "${GREEN}🎉 OpenWrt编译器已启动！${NC}"
    echo -e "${CYAN}📍 访问地址:${NC}"
    echo -e "   本地: ${BLUE}http://localhost:$port${NC}"
    echo -e "   网络: ${BLUE}http://$ip:$port${NC}"
    echo ""
}

# 运行安装脚本
run_install() {
    if [[ -f "install.sh" ]]; then
        log_info "运行安装脚本..."
        bash install.sh "$@"
    else
        log_error "未找到install.sh文件"
        exit 1
    fi
}

# 主函数
main() {
    case "${1:-help}" in
        start)
            start_service
            ;;
        stop)
            stop_service
            ;;
        restart)
            restart_service
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs "$@"
            ;;
        build)
            build_image
            ;;
        update)
            update_code
            ;;
        backup)
            backup_data "$2"
            ;;
        restore)
            restore_data "$2"
            ;;
        clean)
            clean_cache
            ;;
        shell)
            enter_shell "$2"
            ;;
        health)
            health_check
            ;;
        install)
            run_install "${@:2}"
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "未知命令: $1"
            show_help
            exit 1
            ;;
    esac
}

# 运行主函数
main "$@"
