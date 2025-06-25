#!/bin/bash
set -e

# OpenWrt编译器 Docker 启动脚本

echo "🚀 启动 OpenWrt 编译器..."

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_debug() {
    if [ "$FLASK_DEBUG" = "True" ] || [ "$FLASK_DEBUG" = "true" ]; then
        echo -e "${BLUE}[DEBUG]${NC} $1"
    fi
}

# 检查环境变量
check_environment() {
    log_info "检查环境变量..."
    
    # 设置默认值
    export FLASK_ENV=${FLASK_ENV:-production}
    export HOST=${HOST:-0.0.0.0}
    export PORT=${PORT:-5000}
    export WORKERS=${WORKERS:-auto}
    export WORKSPACE_DIR=${WORKSPACE_DIR:-/app/workspace}
    export LOG_LEVEL=${LOG_LEVEL:-INFO}
    
    log_debug "FLASK_ENV: $FLASK_ENV"
    log_debug "HOST: $HOST"
    log_debug "PORT: $PORT"
    log_debug "WORKERS: $WORKERS"
    log_debug "WORKSPACE_DIR: $WORKSPACE_DIR"
}

# 检查目录权限
check_directories() {
    log_info "检查目录权限..."
    
    # 必需的目录
    REQUIRED_DIRS=(
        "$WORKSPACE_DIR"
        "$WORKSPACE_DIR/lede"
        "$WORKSPACE_DIR/configs"
        "$WORKSPACE_DIR/firmware"
        "$WORKSPACE_DIR/uploads"
        "$WORKSPACE_DIR/temp"
        "/app/logs"
    )
    
    for dir in "${REQUIRED_DIRS[@]}"; do
        if [ ! -d "$dir" ]; then
            log_warn "创建目录: $dir"
            mkdir -p "$dir"
        fi
        
        # 检查写权限
        if [ ! -w "$dir" ]; then
            log_error "目录无写权限: $dir"
            exit 1
        fi
    done
    
    log_info "目录权限检查完成"
}

# 检查Python依赖
check_dependencies() {
    log_info "检查Python依赖..."
    
    # 检查关键依赖
    python3 -c "import flask" || {
        log_error "Flask未安装"
        exit 1
    }
    
    python3 -c "import flask_socketio" || {
        log_error "Flask-SocketIO未安装"
        exit 1
    }
    
    log_info "Python依赖检查完成"
}

# 检查系统工具
check_system_tools() {
    log_info "检查系统工具..."
    
    # 检查Git
    if ! command -v git &> /dev/null; then
        log_error "Git未安装"
        exit 1
    fi
    
    # 检查编译工具
    if ! command -v gcc &> /dev/null; then
        log_error "GCC未安装"
        exit 1
    fi
    
    if ! command -v make &> /dev/null; then
        log_error "Make未安装"
        exit 1
    fi
    
    log_info "系统工具检查完成"
}

# 初始化配置
initialize_config() {
    log_info "初始化配置..."
    
    # 如果没有.env文件，复制示例文件
    if [ ! -f "/app/.env" ]; then
        if [ -f "/app/.env.example" ]; then
            log_warn "复制配置文件: .env.example -> .env"
            cp /app/.env.example /app/.env
        else
            log_warn "创建默认配置文件"
            cat > /app/.env << EOF
FLASK_ENV=production
HOST=0.0.0.0
PORT=5000
WORKSPACE_DIR=/app/workspace
LOG_LEVEL=INFO
EOF
        fi
    fi
    
    log_info "配置初始化完成"
}

# 数据库迁移 (如果使用数据库)
migrate_database() {
    if [ "$USE_DATABASE" = "true" ]; then
        log_info "执行数据库迁移..."
        python3 -c "
from backend.app import create_app
from backend.database import db
app = create_app()
with app.app_context():
    db.create_all()
    print('数据库迁移完成')
" || log_warn "数据库迁移失败，继续启动..."
    fi
}

# 清理临时文件
cleanup_temp_files() {
    log_info "清理临时文件..."
    
    # 清理上传临时文件
    find "$WORKSPACE_DIR/uploads" -type f -mtime +1 -delete 2>/dev/null || true
    
    # 清理编译临时文件
    find "$WORKSPACE_DIR/temp" -type f -mtime +1 -delete 2>/dev/null || true
    
    log_info "临时文件清理完成"
}

# 设置信号处理
setup_signal_handlers() {
    # 优雅关闭处理
    trap 'log_info "收到关闭信号，正在优雅关闭..."; kill -TERM $PID; wait $PID' TERM INT
}

# 启动前检查
pre_start_checks() {
    log_info "执行启动前检查..."
    
    check_environment
    check_directories
    check_dependencies
    check_system_tools
    initialize_config
    migrate_database
    cleanup_temp_files
    
    log_info "启动前检查完成"
}

# 启动应用
start_application() {
    log_info "启动应用程序..."
    
    cd /app
    
    # 根据环境选择启动方式
    if [ "$FLASK_ENV" = "development" ]; then
        log_info "开发模式启动"
        python3 backend/app.py --host "$HOST" --port "$PORT" --debug &
    else
        log_info "生产模式启动"
        
        # 计算worker数量
        if [ "$WORKERS" = "auto" ]; then
            WORKERS=$(nproc)
            log_info "自动检测worker数量: $WORKERS"
        fi
        
        # 使用Gunicorn启动
        if command -v gunicorn &> /dev/null; then
            log_info "使用Gunicorn启动 (workers: $WORKERS)"
            gunicorn \
                --bind "$HOST:$PORT" \
                --workers "$WORKERS" \
                --worker-class eventlet \
                --worker-connections 1000 \
                --timeout 300 \
                --keepalive 2 \
                --max-requests 1000 \
                --max-requests-jitter 100 \
                --preload \
                --access-logfile - \
                --error-logfile - \
                --log-level info \
                backend.app:app &
        else
            log_warn "Gunicorn未安装，使用Flask开发服务器"
            python3 backend/app.py --host "$HOST" --port "$PORT" &
        fi
    fi
    
    PID=$!
    log_info "应用程序已启动 (PID: $PID)"
}

# 健康检查
health_check() {
    log_info "等待应用程序启动..."
    
    # 等待应用启动
    for i in {1..30}; do
        if curl -f "http://localhost:$PORT/api/health" >/dev/null 2>&1; then
            log_info "应用程序启动成功"
            return 0
        fi
        log_debug "等待应用启动... ($i/30)"
        sleep 2
    done
    
    log_error "应用程序启动失败"
    return 1
}

# 主函数
main() {
    log_info "OpenWrt编译器 Docker 容器启动"
    log_info "版本: ${APP_VERSION:-unknown}"
    log_info "时间: $(date)"
    
    # 设置信号处理
    setup_signal_handlers
    
    # 执行启动前检查
    pre_start_checks
    
    # 启动应用
    start_application
    
    # 健康检查
    if health_check; then
        log_info "🎉 OpenWrt编译器启动成功!"
        log_info "访问地址: http://localhost:$PORT"
        log_info "API文档: http://localhost:$PORT/api/docs"
        log_info "健康检查: http://localhost:$PORT/api/health"
    else
        log_error "❌ OpenWrt编译器启动失败!"
        exit 1
    fi
    
    # 等待进程结束
    wait $PID
    EXIT_CODE=$?
    
    log_info "应用程序已退出 (退出码: $EXIT_CODE)"
    exit $EXIT_CODE
}

# 如果直接执行此脚本
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    main "$@"
fi
