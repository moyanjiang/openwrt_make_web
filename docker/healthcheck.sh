#!/bin/bash
# OpenWrt编译器健康检查脚本

set -e

# 配置
HOST=${HOST:-localhost}
PORT=${PORT:-5000}
TIMEOUT=${HEALTH_CHECK_TIMEOUT:-10}
MAX_RETRIES=${HEALTH_CHECK_RETRIES:-3}

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 日志函数
log_info() {
    echo -e "${GREEN}[HEALTH]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[HEALTH]${NC} $1"
}

log_error() {
    echo -e "${RED}[HEALTH]${NC} $1"
}

# 检查HTTP服务
check_http_service() {
    local url="http://${HOST}:${PORT}/api/health"
    
    log_info "检查HTTP服务: $url"
    
    # 使用curl检查HTTP服务
    if command -v curl >/dev/null 2>&1; then
        local response
        local http_code
        
        response=$(curl -s -w "%{http_code}" --max-time "$TIMEOUT" "$url" 2>/dev/null || echo "000")
        http_code="${response: -3}"
        
        if [ "$http_code" = "200" ]; then
            log_info "HTTP服务正常 (状态码: $http_code)"
            return 0
        else
            log_error "HTTP服务异常 (状态码: $http_code)"
            return 1
        fi
    else
        log_warn "curl命令不可用，跳过HTTP检查"
        return 0
    fi
}

# 检查WebSocket服务
check_websocket_service() {
    local url="http://${HOST}:${PORT}/socket.io/"
    
    log_info "检查WebSocket服务: $url"
    
    # 简单检查WebSocket端点是否响应
    if command -v curl >/dev/null 2>&1; then
        local http_code
        
        http_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time "$TIMEOUT" "$url" 2>/dev/null || echo "000")
        
        if [ "$http_code" = "200" ] || [ "$http_code" = "400" ]; then
            # 400也是正常的，因为这是WebSocket握手失败，但服务是可用的
            log_info "WebSocket服务正常 (状态码: $http_code)"
            return 0
        else
            log_error "WebSocket服务异常 (状态码: $http_code)"
            return 1
        fi
    else
        log_warn "curl命令不可用，跳过WebSocket检查"
        return 0
    fi
}

# 检查进程状态
check_process_status() {
    log_info "检查应用进程状态"
    
    # 检查Python进程
    if pgrep -f "python.*app.py" >/dev/null 2>&1; then
        log_info "Python应用进程正常"
        return 0
    elif pgrep -f "gunicorn.*app:app" >/dev/null 2>&1; then
        log_info "Gunicorn应用进程正常"
        return 0
    else
        log_error "未找到应用进程"
        return 1
    fi
}

# 检查磁盘空间
check_disk_space() {
    log_info "检查磁盘空间"
    
    local workspace_dir=${WORKSPACE_DIR:-/app/workspace}
    local min_free_space=${MIN_FREE_SPACE_MB:-1024}  # 最小1GB
    
    if [ -d "$workspace_dir" ]; then
        local available_space
        available_space=$(df "$workspace_dir" | awk 'NR==2 {print $4}')
        
        if [ "$available_space" -gt "$min_free_space" ]; then
            log_info "磁盘空间充足 (可用: ${available_space}KB)"
            return 0
        else
            log_warn "磁盘空间不足 (可用: ${available_space}KB, 最小需要: ${min_free_space}KB)"
            return 1
        fi
    else
        log_warn "工作目录不存在: $workspace_dir"
        return 1
    fi
}

# 检查内存使用
check_memory_usage() {
    log_info "检查内存使用"
    
    if command -v free >/dev/null 2>&1; then
        local mem_usage
        mem_usage=$(free | awk 'NR==2{printf "%.1f", $3*100/$2}')
        
        log_info "内存使用率: ${mem_usage}%"
        
        # 如果内存使用超过90%，发出警告但不失败
        if (( $(echo "$mem_usage > 90" | bc -l) )); then
            log_warn "内存使用率过高: ${mem_usage}%"
        fi
        
        return 0
    else
        log_warn "free命令不可用，跳过内存检查"
        return 0
    fi
}

# 检查关键文件
check_critical_files() {
    log_info "检查关键文件"
    
    local critical_files=(
        "/app/backend/app.py"
        "/app/.env"
    )
    
    for file in "${critical_files[@]}"; do
        if [ ! -f "$file" ]; then
            log_error "关键文件缺失: $file"
            return 1
        fi
    done
    
    log_info "关键文件检查完成"
    return 0
}

# 检查网络连接
check_network_connectivity() {
    log_info "检查网络连接"
    
    # 检查本地回环
    if ping -c 1 -W 2 127.0.0.1 >/dev/null 2>&1; then
        log_info "本地网络正常"
    else
        log_error "本地网络异常"
        return 1
    fi
    
    # 检查外网连接（可选）
    if [ "$CHECK_EXTERNAL_NETWORK" = "true" ]; then
        if ping -c 1 -W 5 8.8.8.8 >/dev/null 2>&1; then
            log_info "外网连接正常"
        else
            log_warn "外网连接异常"
            # 外网连接失败不影响健康检查
        fi
    fi
    
    return 0
}

# 执行健康检查
perform_health_check() {
    local checks=(
        "check_critical_files"
        "check_process_status"
        "check_http_service"
        "check_websocket_service"
        "check_disk_space"
        "check_memory_usage"
        "check_network_connectivity"
    )
    
    local failed_checks=0
    local total_checks=${#checks[@]}
    
    log_info "开始健康检查 (共 $total_checks 项)"
    
    for check in "${checks[@]}"; do
        if ! $check; then
            ((failed_checks++))
        fi
    done
    
    log_info "健康检查完成: $((total_checks - failed_checks))/$total_checks 通过"
    
    if [ $failed_checks -eq 0 ]; then
        log_info "✅ 所有健康检查通过"
        return 0
    else
        log_error "❌ $failed_checks 项健康检查失败"
        return 1
    fi
}

# 重试机制
health_check_with_retry() {
    local attempt=1
    
    while [ $attempt -le $MAX_RETRIES ]; do
        log_info "健康检查尝试 $attempt/$MAX_RETRIES"
        
        if perform_health_check; then
            return 0
        fi
        
        if [ $attempt -lt $MAX_RETRIES ]; then
            log_warn "健康检查失败，等待重试..."
            sleep 2
        fi
        
        ((attempt++))
    done
    
    log_error "健康检查失败，已达到最大重试次数"
    return 1
}

# 主函数
main() {
    # 设置错误处理
    set -e
    
    # 检查bc命令（用于浮点数比较）
    if ! command -v bc >/dev/null 2>&1; then
        # 如果没有bc，创建一个简单的替代函数
        bc() {
            python3 -c "print(float('$1'.split()[0]) $2 float('$1'.split()[2]))"
        }
    fi
    
    # 执行健康检查
    if health_check_with_retry; then
        exit 0
    else
        exit 1
    fi
}

# 如果直接执行此脚本
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    main "$@"
fi
