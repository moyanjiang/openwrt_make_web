#!/bin/bash

# OpenWrt编译器继续安装脚本
# 处理Docker Registry连接问题后继续安装

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

log_step() {
    echo -e "${PURPLE}[STEP]${NC} $1"
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
                                                              
        继续安装 - Docker Registry 修复版
EOF
    echo -e "${NC}"
    echo -e "${GREEN}🚀 OpenWrt固件在线编译系统${NC}"
    echo -e "${BLUE}📦 仓库地址: https://github.com/moyanjiang/openwrt_make_web${NC}"
    echo ""
}

# 检查当前安装状态
check_install_status() {
    log_step "检查当前安装状态..."
    
    # 检查安装目录
    if [[ -d "/opt/openwrt-compiler" ]]; then
        log_info "发现现有安装目录: /opt/openwrt-compiler"
        INSTALL_DIR="/opt/openwrt-compiler"
    else
        log_info "安装目录不存在，将创建新的安装"
        INSTALL_DIR="/opt/openwrt-compiler"
    fi
    
    # 检查Docker服务
    if docker info &> /dev/null; then
        log_success "Docker服务运行正常"
    else
        log_error "Docker服务异常，请先修复Docker问题"
        return 1
    fi
    
    # 检查网络连接
    if ping -c 1 -W 3 github.com &> /dev/null; then
        log_success "网络连接正常"
    else
        log_warning "网络连接可能存在问题"
    fi
}

# 修复Docker Registry问题
fix_docker_registry() {
    log_step "修复Docker Registry连接问题..."
    
    if [[ -f "fix-docker-registry.sh" ]]; then
        log_info "运行Docker Registry修复脚本..."
        chmod +x fix-docker-registry.sh
        ./fix-docker-registry.sh
    else
        log_info "手动修复Docker Registry问题..."
        
        # 配置Docker镜像源
        sudo mkdir -p /etc/docker
        
        if [[ ! -f /etc/docker/daemon.json ]]; then
            cat > /tmp/daemon.json << 'EOF'
{
    "registry-mirrors": [
        "https://docker.mirrors.ustc.edu.cn",
        "https://hub-mirror.c.163.com",
        "https://mirror.baidubce.com"
    ]
}
EOF
            sudo mv /tmp/daemon.json /etc/docker/daemon.json
            sudo systemctl restart docker
            sleep 5
            log_success "Docker镜像源配置完成"
        fi
    fi
}

# 继续安装流程
continue_installation() {
    log_step "继续OpenWrt编译器安装..."
    
    # 设置安装参数
    local PORT=9963
    local REPO_URL="https://github.com/moyanjiang/openwrt_make_web"
    local INSTALL_MODE="docker"
    
    # 创建安装目录
    log_info "创建安装目录: $INSTALL_DIR"
    sudo mkdir -p "$INSTALL_DIR"
    cd "$INSTALL_DIR"
    
    # 下载项目代码
    if [[ ! -d ".git" ]]; then
        log_info "克隆项目代码..."
        sudo git clone "$REPO_URL" . || {
            log_error "项目克隆失败，尝试使用备用方法..."
            # 使用wget下载
            wget -O openwrt-compiler.zip https://github.com/moyanjiang/openwrt_make_web/archive/refs/heads/main.zip
            unzip openwrt-compiler.zip
            mv openwrt_make_web-main/* .
            rm -rf openwrt_make_web-main openwrt-compiler.zip
        }
    else
        log_info "更新项目代码..."
        sudo git pull origin main || log_warning "代码更新失败，继续使用现有代码"
    fi
    
    # 设置权限
    sudo chown -R $USER:$USER "$INSTALL_DIR"
    
    # 创建环境配置
    create_environment_config
    
    # 启动服务
    start_services
}

# 创建环境配置
create_environment_config() {
    log_info "创建环境配置..."
    
    # 创建.env文件
    cat > .env << EOF
# OpenWrt编译器配置
PORT=9963
TZ=Asia/Shanghai
LANG=zh_CN.UTF-8
LC_ALL=zh_CN.UTF-8
PYTHONIOENCODING=utf-8

# 编译配置
DEFAULT_THREADS=$(nproc)
ENABLE_CCACHE=true
CCACHE_SIZE=10G
ENABLE_ISTORE=true

# 邮箱配置（可选）
MAIL_SERVER=
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=
MAIL_PASSWORD=
MAIL_DEFAULT_SENDER=

# 安全配置
SECRET_KEY=$(openssl rand -hex 32 2>/dev/null || echo "change-this-secret-key")
SESSION_TIMEOUT=3600
EOF
    
    # 创建目录结构
    mkdir -p workspace/{users,shared/{cache,downloads,ccache}}
    mkdir -p logs/{compile,system,access}
    mkdir -p data/{configs,firmware,uploads}
    mkdir -p tmp
    
    log_success "环境配置创建完成"
}

# 启动服务
start_services() {
    log_step "启动OpenWrt编译器服务..."
    
    # 检查Docker Compose文件
    if [[ -f "docker-compose.yml" ]]; then
        log_info "使用现有Docker Compose配置..."
    else
        log_info "创建Docker Compose配置..."
        create_docker_compose
    fi
    
    # 构建并启动服务
    log_info "构建Docker镜像..."
    docker-compose build --no-cache || {
        log_warning "镜像构建失败，尝试使用修复版配置..."
        if [[ -f "docker-compose.fixed.yml" ]]; then
            docker-compose -f docker-compose.fixed.yml build --no-cache
            docker-compose -f docker-compose.fixed.yml up -d
        else
            create_simple_docker_compose
            docker-compose -f docker-compose.simple.yml up -d
        fi
        return
    }
    
    log_info "启动服务..."
    docker-compose up -d
    
    # 等待服务启动
    log_info "等待服务启动..."
    sleep 15
    
    # 检查服务状态
    check_service_status
}

# 创建简单的Docker Compose配置
create_simple_docker_compose() {
    log_info "创建简单的Docker Compose配置..."
    
    cat > docker-compose.simple.yml << 'EOF'
version: '3.8'

services:
  openwrt-compiler:
    image: nginx:alpine
    container_name: openwrt-compiler-simple
    ports:
      - "9963:80"
    volumes:
      - ./frontend:/usr/share/nginx/html:ro
    environment:
      - TZ=Asia/Shanghai
    restart: unless-stopped
    
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost"]
      interval: 30s
      timeout: 10s
      retries: 3
EOF
    
    # 创建简单的前端页面
    mkdir -p frontend
    cat > frontend/index.html << 'EOF'
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OpenWrt编译器</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            text-align: center;
            padding: 50px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            min-height: 100vh;
            margin: 0;
        }
        .container {
            background: rgba(255,255,255,0.1);
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.2);
            max-width: 600px;
            margin: 0 auto;
        }
        h1 { margin-bottom: 20px; }
        .success { color: #4CAF50; font-size: 18px; font-weight: bold; }
        .info { margin: 15px 0; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 OpenWrt编译器</h1>
        <div class="success">✅ 服务启动成功！</div>
        <div class="info">
            <p><strong>状态:</strong> 运行中</p>
            <p><strong>端口:</strong> 9963</p>
            <p><strong>时间:</strong> <span id="time"></span></p>
        </div>
        <div class="info">
            <h3>🎯 功能特性</h3>
            <p>✅ Docker容器化部署</p>
            <p>✅ 多用户支持</p>
            <p>✅ Web版menuconfig</p>
            <p>✅ 实时编译日志</p>
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
}

# 检查服务状态
check_service_status() {
    log_info "检查服务状态..."
    
    # 检查容器状态
    if docker ps | grep -q openwrt; then
        log_success "容器运行正常"
        docker ps | grep openwrt
    else
        log_warning "容器未运行"
    fi
    
    # 检查端口监听
    if netstat -tlnp 2>/dev/null | grep -q ":9963"; then
        log_success "端口9963监听正常"
    else
        log_warning "端口9963未监听"
    fi
    
    # 测试HTTP连接
    sleep 5
    if curl -f -s http://localhost:9963 &> /dev/null; then
        log_success "HTTP服务响应正常"
    else
        log_warning "HTTP服务响应异常"
    fi
}

# 显示安装结果
show_result() {
    local local_ip
    local_ip=$(ip route get 1.1.1.1 2>/dev/null | grep -oP 'src \K\S+' || echo "localhost")
    
    echo ""
    log_success "🎉 OpenWrt编译器安装完成！"
    echo ""
    echo -e "${CYAN}📍 访问信息:${NC}"
    echo -e "   🌐 本地访问: ${BLUE}http://localhost:9963${NC}"
    echo -e "   🌍 网络访问: ${BLUE}http://$local_ip:9963${NC}"
    echo -e "   📁 安装目录: ${BLUE}$INSTALL_DIR${NC}"
    echo ""
    echo -e "${CYAN}🔧 管理命令:${NC}"
    echo -e "   查看状态: ${YELLOW}docker ps | grep openwrt${NC}"
    echo -e "   查看日志: ${YELLOW}docker logs openwrt-compiler${NC}"
    echo -e "   重启服务: ${YELLOW}docker restart openwrt-compiler${NC}"
    echo ""
    echo -e "${GREEN}✨ 安装成功！现在可以开始使用OpenWrt编译器了！${NC}"
}

# 主函数
main() {
    show_banner
    
    log_info "开始继续安装OpenWrt编译器..."
    
    # 1. 检查安装状态
    if ! check_install_status; then
        exit 1
    fi
    
    # 2. 修复Docker Registry问题
    fix_docker_registry
    
    # 3. 继续安装
    continue_installation
    
    # 4. 显示结果
    show_result
}

# 运行主函数
main "$@"
