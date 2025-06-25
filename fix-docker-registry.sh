#!/bin/bash

# Docker Registry连接问题修复脚本
# 解决registry-1.docker.io连接问题

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
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

echo -e "${CYAN}"
cat << 'EOF'
 ██████╗  ██████╗  ██████╗██╗  ██╗███████╗██████╗ 
 ██╔══██╗██╔═══██╗██╔════╝██║ ██╔╝██╔════╝██╔══██╗
 ██║  ██║██║   ██║██║     █████╔╝ █████╗  ██████╔╝
 ██║  ██║██║   ██║██║     ██╔═██╗ ██╔══╝  ██╔══██╗
 ██████╔╝╚██████╔╝╚██████╗██║  ██╗███████╗██║  ██║
 ╚═════╝  ╚═════╝  ╚═════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝
                                                   
    Docker Registry 连接问题修复工具
EOF
echo -e "${NC}"

log_info "🔧 开始修复Docker Registry连接问题..."

# 检查Docker服务状态
check_docker_service() {
    log_info "检查Docker服务状态..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装"
        return 1
    fi
    
    if ! systemctl is-active --quiet docker; then
        log_warning "Docker服务未运行，正在启动..."
        sudo systemctl start docker
        sleep 3
    fi
    
    if docker info &> /dev/null; then
        log_success "Docker服务运行正常"
        return 0
    else
        log_error "Docker服务异常"
        return 1
    fi
}

# 配置Docker镜像源
configure_docker_mirrors() {
    log_info "配置Docker镜像源..."
    
    # 创建Docker配置目录
    sudo mkdir -p /etc/docker
    
    # 备份现有配置
    if [[ -f /etc/docker/daemon.json ]]; then
        sudo cp /etc/docker/daemon.json /etc/docker/daemon.json.backup
        log_info "已备份现有Docker配置"
    fi
    
    # 创建新的daemon.json配置
    cat > /tmp/daemon.json << 'EOF'
{
    "registry-mirrors": [
        "https://docker.mirrors.ustc.edu.cn",
        "https://hub-mirror.c.163.com",
        "https://mirror.baidubce.com",
        "https://ccr.ccs.tencentyun.com"
    ],
    "insecure-registries": [],
    "debug": false,
    "experimental": false,
    "features": {
        "buildkit": true
    },
    "builder": {
        "gc": {
            "enabled": true,
            "defaultKeepStorage": "20GB"
        }
    },
    "log-driver": "json-file",
    "log-opts": {
        "max-size": "10m",
        "max-file": "3"
    }
}
EOF
    
    # 移动配置文件
    sudo mv /tmp/daemon.json /etc/docker/daemon.json
    sudo chmod 644 /etc/docker/daemon.json
    
    log_success "Docker镜像源配置完成"
}

# 重启Docker服务
restart_docker_service() {
    log_info "重启Docker服务以应用新配置..."
    
    sudo systemctl daemon-reload
    sudo systemctl restart docker
    
    # 等待Docker服务启动
    sleep 5
    
    if docker info &> /dev/null; then
        log_success "Docker服务重启成功"
    else
        log_error "Docker服务重启失败"
        return 1
    fi
}

# 测试Docker镜像拉取
test_docker_pull() {
    log_info "测试Docker镜像拉取..."
    
    # 测试拉取小镜像
    if docker pull hello-world:latest; then
        log_success "Docker镜像拉取测试成功"
        docker rmi hello-world:latest 2>/dev/null || true
        return 0
    else
        log_warning "Docker镜像拉取测试失败，但可能不影响使用"
        return 1
    fi
}

# 配置DNS解析
configure_dns() {
    log_info "配置DNS解析..."
    
    # 备份现有DNS配置
    sudo cp /etc/resolv.conf /etc/resolv.conf.backup 2>/dev/null || true
    
    # 添加可靠的DNS服务器
    cat > /tmp/resolv.conf << 'EOF'
# 优化的DNS配置
nameserver 8.8.8.8
nameserver 8.8.4.4
nameserver 114.114.114.114
nameserver 223.5.5.5
options timeout:2
options attempts:3
options rotate
EOF
    
    # 检查是否使用systemd-resolved
    if systemctl is-active --quiet systemd-resolved; then
        log_info "检测到systemd-resolved，配置DNS..."
        
        # 配置systemd-resolved
        sudo mkdir -p /etc/systemd/resolved.conf.d
        cat > /tmp/dns.conf << 'EOF'
[Resolve]
DNS=8.8.8.8 8.8.4.4 114.114.114.114 223.5.5.5
FallbackDNS=1.1.1.1 1.0.0.1
Domains=~.
DNSSEC=no
DNSOverTLS=no
Cache=yes
DNSStubListener=yes
EOF
        sudo mv /tmp/dns.conf /etc/systemd/resolved.conf.d/dns.conf
        sudo systemctl restart systemd-resolved
    else
        # 直接配置resolv.conf
        sudo mv /tmp/resolv.conf /etc/resolv.conf
    fi
    
    log_success "DNS配置完成"
}

# 测试网络连接
test_network_connectivity() {
    log_info "测试网络连接..."
    
    local test_hosts=(
        "docker.io"
        "registry-1.docker.io"
        "index.docker.io"
        "github.com"
    )
    
    local success_count=0
    for host in "${test_hosts[@]}"; do
        if ping -c 2 -W 3 "$host" &> /dev/null; then
            log_success "✓ $host 连接正常"
            ((success_count++))
        else
            log_warning "✗ $host 连接失败"
        fi
    done
    
    if [[ $success_count -ge 2 ]]; then
        log_success "网络连接基本正常"
        return 0
    else
        log_warning "网络连接存在问题，但可能不影响使用"
        return 1
    fi
}

# 清理Docker缓存
clean_docker_cache() {
    log_info "清理Docker缓存..."
    
    # 清理未使用的镜像、容器、网络、卷
    docker system prune -f 2>/dev/null || true
    
    log_success "Docker缓存清理完成"
}

# 显示Docker信息
show_docker_info() {
    log_info "显示Docker配置信息..."
    
    echo -e "${CYAN}Docker版本信息:${NC}"
    docker --version
    
    echo -e "${CYAN}Docker系统信息:${NC}"
    docker info | grep -E "(Registry|Mirrors|Server Version)" || true
    
    echo -e "${CYAN}Docker镜像源配置:${NC}"
    if [[ -f /etc/docker/daemon.json ]]; then
        cat /etc/docker/daemon.json | grep -A 10 "registry-mirrors" || true
    fi
}

# 主修复流程
main() {
    log_info "开始修复Docker Registry连接问题..."
    
    # 1. 检查Docker服务
    if ! check_docker_service; then
        log_error "Docker服务检查失败，请先安装Docker"
        exit 1
    fi
    
    # 2. 配置DNS
    configure_dns
    
    # 3. 配置Docker镜像源
    configure_docker_mirrors
    
    # 4. 重启Docker服务
    if ! restart_docker_service; then
        log_error "Docker服务重启失败"
        exit 1
    fi
    
    # 5. 清理缓存
    clean_docker_cache
    
    # 6. 测试网络连接
    test_network_connectivity
    
    # 7. 测试Docker拉取
    test_docker_pull
    
    # 8. 显示配置信息
    show_docker_info
    
    echo ""
    log_success "🎉 Docker Registry连接问题修复完成！"
    echo ""
    echo -e "${CYAN}📋 修复内容:${NC}"
    echo -e "   ✅ 配置了国内Docker镜像源"
    echo -e "   ✅ 优化了DNS解析配置"
    echo -e "   ✅ 重启了Docker服务"
    echo -e "   ✅ 清理了Docker缓存"
    echo ""
    echo -e "${CYAN}🚀 下一步:${NC}"
    echo -e "   现在可以继续运行OpenWrt编译器安装脚本"
    echo -e "   或者重新运行: ${YELLOW}./install.sh${NC}"
    echo ""
    echo -e "${CYAN}🔧 验证命令:${NC}"
    echo -e "   测试Docker: ${YELLOW}docker run hello-world${NC}"
    echo -e "   查看配置: ${YELLOW}cat /etc/docker/daemon.json${NC}"
    echo ""
}

# 运行主函数
main "$@"
