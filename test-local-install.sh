#!/bin/bash

# OpenWrt编译器本地安装测试脚本
# 验证本地模式安装是否成功

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
TEST_TIMEOUT=30

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
 ████████╗███████╗███████╗████████╗
 ╚══██╔══╝██╔════╝██╔════╝╚══██╔══╝
    ██║   █████╗  ███████╗   ██║   
    ██║   ██╔══╝  ╚════██║   ██║   
    ██║   ███████╗███████║   ██║   
    ╚═╝   ╚══════╝╚══════╝   ╚═╝   
                                   
    本地安装测试工具
EOF
    echo -e "${NC}"
    echo -e "${GREEN}🧪 OpenWrt编译器本地模式安装测试${NC}"
    echo ""
}

# 测试系统环境
test_system_environment() {
    log_test "测试系统环境..."
    
    local tests_passed=0
    local total_tests=5
    
    # 测试Python版本
    if python3 --version &> /dev/null; then
        local python_version=$(python3 --version | grep -oE '[0-9]+\.[0-9]+')
        local major=$(echo $python_version | cut -d. -f1)
        local minor=$(echo $python_version | cut -d. -f2)
        
        if [[ $major -ge 3 && $minor -ge 8 ]]; then
            log_success "Python版本: $python_version ✓"
            ((tests_passed++))
        else
            log_error "Python版本过低: $python_version (需要3.8+)"
        fi
    else
        log_error "Python3未安装"
    fi
    
    # 测试Git
    if command -v git &> /dev/null; then
        log_success "Git: $(git --version | cut -d' ' -f3) ✓"
        ((tests_passed++))
    else
        log_error "Git未安装"
    fi
    
    # 测试系统资源
    local mem_gb=$(free -g | awk '/^Mem:/{print $2}')
    if [[ $mem_gb -ge 4 ]]; then
        log_success "内存: ${mem_gb}GB ✓"
        ((tests_passed++))
    else
        log_warning "内存不足: ${mem_gb}GB (建议4GB+)"
    fi
    
    # 测试磁盘空间
    local disk_gb=$(df -BG / | awk 'NR==2{print int($4)}')
    if [[ $disk_gb -ge 50 ]]; then
        log_success "磁盘空间: ${disk_gb}GB ✓"
        ((tests_passed++))
    else
        log_warning "磁盘空间不足: ${disk_gb}GB (建议50GB+)"
    fi
    
    # 测试网络连接
    if ping -c 1 -W 3 github.com &> /dev/null; then
        log_success "网络连接: 正常 ✓"
        ((tests_passed++))
    else
        log_warning "网络连接异常"
    fi
    
    echo ""
    log_info "系统环境测试: $tests_passed/$total_tests 通过"
    
    if [[ $tests_passed -ge 3 ]]; then
        return 0
    else
        return 1
    fi
}

# 测试安装目录
test_installation_directory() {
    log_test "测试安装目录..."
    
    if [[ ! -d "$INSTALL_DIR" ]]; then
        log_error "安装目录不存在: $INSTALL_DIR"
        return 1
    fi
    
    local tests_passed=0
    local total_tests=6
    
    # 检查主要目录
    local required_dirs=(
        "backend"
        "workspace"
        "logs"
        "data"
        "venv"
    )
    
    for dir in "${required_dirs[@]}"; do
        if [[ -d "$INSTALL_DIR/$dir" ]]; then
            log_success "目录存在: $dir ✓"
            ((tests_passed++))
        else
            log_error "目录缺失: $dir"
        fi
    done
    
    # 检查主要文件
    if [[ -f "$INSTALL_DIR/backend/app.py" ]]; then
        log_success "主应用文件存在 ✓"
        ((tests_passed++))
    else
        log_error "主应用文件缺失: backend/app.py"
    fi
    
    echo ""
    log_info "安装目录测试: $tests_passed/$total_tests 通过"
    
    return $([[ $tests_passed -eq $total_tests ]] && echo 0 || echo 1)
}

# 测试Python环境
test_python_environment() {
    log_test "测试Python环境..."
    
    cd "$INSTALL_DIR"
    
    local tests_passed=0
    local total_tests=4
    
    # 检查虚拟环境
    if [[ -d "venv" ]]; then
        log_success "虚拟环境存在 ✓"
        ((tests_passed++))
    else
        log_error "虚拟环境不存在"
        return 1
    fi
    
    # 激活虚拟环境并测试
    source venv/bin/activate
    
    # 测试Flask
    if python3 -c "import flask; print('Flask version:', flask.__version__)" &> /dev/null; then
        local flask_version=$(python3 -c "import flask; print(flask.__version__)")
        log_success "Flask: $flask_version ✓"
        ((tests_passed++))
    else
        log_error "Flask未安装或版本不兼容"
    fi
    
    # 测试其他依赖
    local packages=("requests" "psutil")
    for pkg in "${packages[@]}"; do
        if python3 -c "import $pkg" &> /dev/null; then
            log_success "Python包: $pkg ✓"
            ((tests_passed++))
        else
            log_error "Python包缺失: $pkg"
        fi
    done
    
    deactivate
    
    echo ""
    log_info "Python环境测试: $tests_passed/$total_tests 通过"
    
    return $([[ $tests_passed -eq $total_tests ]] && echo 0 || echo 1)
}

# 测试服务启动
test_service_startup() {
    log_test "测试服务启动..."
    
    cd "$INSTALL_DIR"
    
    # 检查启动脚本
    if [[ ! -f "start.sh" ]]; then
        log_error "启动脚本不存在: start.sh"
        return 1
    fi
    
    if [[ ! -x "start.sh" ]]; then
        log_error "启动脚本无执行权限"
        chmod +x start.sh
    fi
    
    # 启动服务
    log_info "启动服务..."
    ./start.sh &
    local start_pid=$!
    
    # 等待服务启动
    local wait_time=0
    while [[ $wait_time -lt $TEST_TIMEOUT ]]; do
        if [[ -f "tmp/app.pid" ]] && kill -0 $(cat tmp/app.pid) 2>/dev/null; then
            log_success "服务启动成功 (PID: $(cat tmp/app.pid))"
            break
        fi
        sleep 1
        ((wait_time++))
    done
    
    if [[ $wait_time -ge $TEST_TIMEOUT ]]; then
        log_error "服务启动超时"
        return 1
    fi
    
    return 0
}

# 测试HTTP服务
test_http_service() {
    log_test "测试HTTP服务..."
    
    local tests_passed=0
    local total_tests=4
    
    # 测试端口监听
    if netstat -tlnp 2>/dev/null | grep -q ":$TEST_PORT "; then
        log_success "端口监听: $TEST_PORT ✓"
        ((tests_passed++))
    else
        log_error "端口未监听: $TEST_PORT"
    fi
    
    # 等待HTTP服务就绪
    sleep 3
    
    # 测试主页
    if curl -f -s http://localhost:$TEST_PORT/ &> /dev/null; then
        log_success "主页访问: 正常 ✓"
        ((tests_passed++))
    else
        log_error "主页访问失败"
    fi
    
    # 测试健康检查API
    if curl -f -s http://localhost:$TEST_PORT/api/health &> /dev/null; then
        log_success "健康检查API: 正常 ✓"
        ((tests_passed++))
    else
        log_error "健康检查API失败"
    fi
    
    # 测试状态API
    if curl -f -s http://localhost:$TEST_PORT/api/status &> /dev/null; then
        log_success "状态API: 正常 ✓"
        ((tests_passed++))
    else
        log_error "状态API失败"
    fi
    
    echo ""
    log_info "HTTP服务测试: $tests_passed/$total_tests 通过"
    
    return $([[ $tests_passed -eq $total_tests ]] && echo 0 || echo 1)
}

# 测试服务停止
test_service_stop() {
    log_test "测试服务停止..."
    
    cd "$INSTALL_DIR"
    
    if [[ -f "stop.sh" ]]; then
        ./stop.sh
        sleep 2
        
        if [[ ! -f "tmp/app.pid" ]] || ! kill -0 $(cat tmp/app.pid) 2>/dev/null; then
            log_success "服务停止成功 ✓"
            return 0
        else
            log_error "服务停止失败"
            return 1
        fi
    else
        log_error "停止脚本不存在"
        return 1
    fi
}

# 显示测试结果
show_test_results() {
    local total_passed=$1
    local total_tests=$2
    
    echo ""
    echo "=" * 50
    echo -e "${CYAN}📊 测试结果汇总${NC}"
    echo "=" * 50
    
    if [[ $total_passed -eq $total_tests ]]; then
        echo -e "${GREEN}🎉 所有测试通过！($total_passed/$total_tests)${NC}"
        echo ""
        echo -e "${GREEN}✅ 本地模式安装成功！${NC}"
        echo -e "${BLUE}🌐 访问地址: http://localhost:$TEST_PORT${NC}"
        echo ""
        echo -e "${CYAN}🔧 管理命令:${NC}"
        echo -e "   启动: ${YELLOW}cd $INSTALL_DIR && ./start.sh${NC}"
        echo -e "   停止: ${YELLOW}cd $INSTALL_DIR && ./stop.sh${NC}"
        echo -e "   状态: ${YELLOW}cd $INSTALL_DIR && ./status.sh${NC}"
    else
        echo -e "${RED}❌ 部分测试失败 ($total_passed/$total_tests)${NC}"
        echo ""
        echo -e "${YELLOW}🔧 建议操作:${NC}"
        echo -e "   1. 检查安装日志: ${YELLOW}cat /tmp/openwrt-install-local.log${NC}"
        echo -e "   2. 重新运行安装: ${YELLOW}./install-local.sh --force${NC}"
        echo -e "   3. 手动启动调试: ${YELLOW}cd $INSTALL_DIR/backend && python3 app.py --debug${NC}"
    fi
    
    echo ""
}

# 主函数
main() {
    show_banner
    
    log_info "开始本地安装测试..."
    echo ""
    
    local total_tests=6
    local passed_tests=0
    
    # 执行测试
    if test_system_environment; then
        ((passed_tests++))
    fi
    echo ""
    
    if test_installation_directory; then
        ((passed_tests++))
    fi
    echo ""
    
    if test_python_environment; then
        ((passed_tests++))
    fi
    echo ""
    
    if test_service_startup; then
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
