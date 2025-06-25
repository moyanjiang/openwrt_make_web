#!/bin/bash

# OpenWrt编译器Docker本地安装测试脚本
# 验证Docker本地模式安装是否成功

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# 测试配置
TEST_PORT=9963
INSTALL_DIR="/opt/openwrt-compiler"
TEST_TIMEOUT=60

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

log_test() {
    echo -e "${CYAN}[TEST]${NC} $1"
}

# 显示横幅
show_banner() {
    clear
    echo -e "${CYAN}"
    cat << 'EOF'
 ████████╗███████╗███████╗████████╗    ██████╗  ██████╗  ██████╗██╗  ██╗███████╗██████╗ 
 ╚══██╔══╝██╔════╝██╔════╝╚══██╔══╝    ██╔══██╗██╔═══██╗██╔════╝██║ ██╔╝██╔════╝██╔══██╗
    ██║   █████╗  ███████╗   ██║       ██║  ██║██║   ██║██║     █████╔╝ █████╗  ██████╔╝
    ██║   ██╔══╝  ╚════██║   ██║       ██║  ██║██║   ██║██║     ██╔═██╗ ██╔══╝  ██╔══██╗
    ██║   ███████╗███████║   ██║       ██████╔╝╚██████╔╝╚██████╗██║  ██╗███████╗██║  ██║
    ╚═╝   ╚══════╝╚══════╝   ╚═╝       ╚═════╝  ╚═════╝  ╚═════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝
                                                                                          
    Docker本地安装测试工具
EOF
    echo -e "${NC}"
    echo -e "${GREEN}🧪 OpenWrt编译器Docker本地模式安装测试${NC}"
    echo ""
}

# 测试Docker环境
test_docker_environment() {
    log_test "测试Docker环境..."
    
    local tests_passed=0
    local total_tests=4
    
    # 测试Docker
    if command -v docker &> /dev/null; then
        local docker_version=$(docker --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')
        log_success "Docker版本: $docker_version ✓"
        ((tests_passed++))
    else
        log_error "Docker未安装"
    fi
    
    # 测试Docker服务
    if docker info &> /dev/null; then
        log_success "Docker服务: 运行中 ✓"
        ((tests_passed++))
    else
        log_error "Docker服务未运行"
    fi
    
    # 测试Docker Compose
    if command -v docker-compose &> /dev/null; then
        local compose_version=$(docker-compose --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')
        log_success "Docker Compose版本: $compose_version ✓"
        ((tests_passed++))
    else
        log_error "Docker Compose未安装"
    fi
    
    # 测试Docker权限
    if docker ps &> /dev/null; then
        log_success "Docker权限: 正常 ✓"
        ((tests_passed++))
    else
        log_error "Docker权限不足"
    fi
    
    echo ""
    log_info "Docker环境测试: $tests_passed/$total_tests 通过"
    
    return $([[ $tests_passed -eq $total_tests ]] && echo 0 || echo 1)
}

# 测试安装目录
test_installation_directory() {
    log_test "测试安装目录..."
    
    if [[ ! -d "$INSTALL_DIR" ]]; then
        log_error "安装目录不存在: $INSTALL_DIR"
        return 1
    fi
    
    local tests_passed=0
    local total_tests=8
    
    # 检查主要文件
    local required_files=(
        "Dockerfile"
        "docker-compose.yml"
        ".env"
        "start.sh"
        "stop.sh"
        "status.sh"
    )
    
    for file in "${required_files[@]}"; do
        if [[ -f "$INSTALL_DIR/$file" ]]; then
            log_success "文件存在: $file ✓"
            ((tests_passed++))
        else
            log_error "文件缺失: $file"
        fi
    done
    
    # 检查主要目录
    local required_dirs=(
        "backend"
        "config"
    )
    
    for dir in "${required_dirs[@]}"; do
        if [[ -d "$INSTALL_DIR/$dir" ]]; then
            log_success "目录存在: $dir ✓"
            ((tests_passed++))
        else
            log_error "目录缺失: $dir"
        fi
    done
    
    echo ""
    log_info "安装目录测试: $tests_passed/$total_tests 通过"
    
    return $([[ $tests_passed -eq $total_tests ]] && echo 0 || echo 1)
}

# 测试Docker镜像
test_docker_image() {
    log_test "测试Docker镜像..."
    
    cd "$INSTALL_DIR"
    
    local tests_passed=0
    local total_tests=2
    
    # 检查镜像是否存在
    if docker images | grep -q "openwrt-compiler"; then
        log_success "Docker镜像存在 ✓"
        ((tests_passed++))
    else
        log_warning "Docker镜像不存在，尝试构建..."
        if docker-compose build --no-cache; then
            log_success "Docker镜像构建成功 ✓"
            ((tests_passed++))
        else
            log_error "Docker镜像构建失败"
        fi
    fi
    
    # 检查docker-compose配置
    if docker-compose config &> /dev/null; then
        log_success "Docker Compose配置有效 ✓"
        ((tests_passed++))
    else
        log_error "Docker Compose配置无效"
    fi
    
    echo ""
    log_info "Docker镜像测试: $tests_passed/$total_tests 通过"
    
    return $([[ $tests_passed -eq $total_tests ]] && echo 0 || echo 1)
}

# 测试服务启动
test_service_startup() {
    log_test "测试服务启动..."
    
    cd "$INSTALL_DIR"
    
    # 停止现有服务
    log_info "停止现有服务..."
    docker-compose down 2>/dev/null || true
    
    # 启动服务
    log_info "启动服务..."
    if ! docker-compose up -d; then
        log_error "服务启动失败"
        return 1
    fi
    
    # 等待服务启动
    local wait_time=0
    log_info "等待服务启动..."
    while [[ $wait_time -lt $TEST_TIMEOUT ]]; do
        if docker-compose ps | grep -q "Up"; then
            log_success "服务启动成功"
            break
        fi
        sleep 2
        ((wait_time+=2))
    done
    
    if [[ $wait_time -ge $TEST_TIMEOUT ]]; then
        log_error "服务启动超时"
        docker-compose logs
        return 1
    fi
    
    return 0
}

# 测试容器状态
test_container_status() {
    log_test "测试容器状态..."
    
    cd "$INSTALL_DIR"
    
    local tests_passed=0
    local total_tests=3
    
    # 检查主容器
    if docker ps | grep -q "openwrt-compiler"; then
        log_success "主容器运行中 ✓"
        ((tests_passed++))
    else
        log_error "主容器未运行"
    fi
    
    # 检查Nginx容器
    if docker ps | grep -q "openwrt-nginx"; then
        log_success "Nginx容器运行中 ✓"
        ((tests_passed++))
    else
        log_warning "Nginx容器未运行"
    fi
    
    # 检查Redis容器
    if docker ps | grep -q "openwrt-redis"; then
        log_success "Redis容器运行中 ✓"
        ((tests_passed++))
    else
        log_warning "Redis容器未运行"
    fi
    
    echo ""
    log_info "容器状态测试: $tests_passed/$total_tests 通过"
    
    return $([[ $tests_passed -ge 1 ]] && echo 0 || echo 1)
}

# 测试HTTP服务
test_http_service() {
    log_test "测试HTTP服务..."
    
    local tests_passed=0
    local total_tests=4
    
    # 等待HTTP服务就绪
    sleep 10
    
    # 测试主服务端口
    if netstat -tlnp 2>/dev/null | grep -q ":$TEST_PORT "; then
        log_success "主服务端口监听: $TEST_PORT ✓"
        ((tests_passed++))
    else
        log_error "主服务端口未监听: $TEST_PORT"
    fi
    
    # 测试主页访问
    if curl -f -s --max-time 10 http://localhost:$TEST_PORT/ &> /dev/null; then
        log_success "主页访问: 正常 ✓"
        ((tests_passed++))
    else
        log_error "主页访问失败"
    fi
    
    # 测试健康检查API
    if curl -f -s --max-time 10 http://localhost:$TEST_PORT/api/health &> /dev/null; then
        log_success "健康检查API: 正常 ✓"
        ((tests_passed++))
    else
        log_error "健康检查API失败"
    fi
    
    # 测试Nginx代理（如果启用）
    if curl -f -s --max-time 10 http://localhost/health &> /dev/null; then
        log_success "Nginx代理: 正常 ✓"
        ((tests_passed++))
    else
        log_warning "Nginx代理未启用或异常"
    fi
    
    echo ""
    log_info "HTTP服务测试: $tests_passed/$total_tests 通过"
    
    return $([[ $tests_passed -ge 2 ]] && echo 0 || echo 1)
}

# 测试服务停止
test_service_stop() {
    log_test "测试服务停止..."
    
    cd "$INSTALL_DIR"
    
    if docker-compose down; then
        sleep 5
        if ! docker ps | grep -q "openwrt"; then
            log_success "服务停止成功 ✓"
            return 0
        else
            log_error "服务停止失败"
            return 1
        fi
    else
        log_error "服务停止命令失败"
        return 1
    fi
}

# 显示测试结果
show_test_results() {
    local total_passed=$1
    local total_tests=$2
    
    echo ""
    echo "=" * 60
    echo -e "${CYAN}📊 测试结果汇总${NC}"
    echo "=" * 60
    
    if [[ $total_passed -eq $total_tests ]]; then
        echo -e "${GREEN}🎉 所有测试通过！($total_passed/$total_tests)${NC}"
        echo ""
        echo -e "${GREEN}✅ Docker本地模式安装成功！${NC}"
        echo -e "${BLUE}🌐 访问地址: http://localhost:$TEST_PORT${NC}"
        echo -e "${BLUE}🔗 代理地址: http://localhost${NC}"
        echo ""
        echo -e "${CYAN}🔧 管理命令:${NC}"
        echo -e "   启动: ${YELLOW}cd $INSTALL_DIR && ./start.sh${NC}"
        echo -e "   停止: ${YELLOW}cd $INSTALL_DIR && ./stop.sh${NC}"
        echo -e "   状态: ${YELLOW}cd $INSTALL_DIR && ./status.sh${NC}"
        echo -e "   日志: ${YELLOW}cd $INSTALL_DIR && ./logs.sh${NC}"
    else
        echo -e "${RED}❌ 部分测试失败 ($total_passed/$total_tests)${NC}"
        echo ""
        echo -e "${YELLOW}🔧 建议操作:${NC}"
        echo -e "   1. 检查安装日志: ${YELLOW}cat /tmp/openwrt-docker-install.log${NC}"
        echo -e "   2. 重新运行安装: ${YELLOW}./install-docker-local.sh --force${NC}"
        echo -e "   3. 查看容器日志: ${YELLOW}cd $INSTALL_DIR && ./logs.sh${NC}"
        echo -e "   4. 检查Docker状态: ${YELLOW}docker ps -a${NC}"
    fi
    
    echo ""
}

# 主函数
main() {
    show_banner
    
    log_info "开始Docker本地安装测试..."
    echo ""
    
    local total_tests=7
    local passed_tests=0
    
    # 执行测试
    if test_docker_environment; then
        ((passed_tests++))
    fi
    echo ""
    
    if test_installation_directory; then
        ((passed_tests++))
    fi
    echo ""
    
    if test_docker_image; then
        ((passed_tests++))
    fi
    echo ""
    
    if test_service_startup; then
        ((passed_tests++))
    fi
    echo ""
    
    if test_container_status; then
        ((passed_tests++))
    fi
    echo ""
    
    if test_http_service; then
        ((passed_tests++))
    fi
    echo ""
    
    if test_service_stop; then
        ((passed_tests++))
    fi
    
    # 显示结果
    show_test_results $passed_tests $total_tests
    
    # 返回结果
    if [[ $passed_tests -eq $total_tests ]]; then
        exit 0
    else
        exit 1
    fi
}

# 运行主函数
main "$@"
