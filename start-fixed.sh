#!/bin/bash

# OpenWrt编译器修复版启动脚本
# 解决网页乱码和内网穿透问题

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

# 显示横幅
echo -e "${CYAN}"
cat << 'EOF'
 ███████╗████████╗ █████╗ ██████╗ ████████╗    ███████╗██╗██╗  ██╗███████╗██████╗ 
 ██╔════╝╚══██╔══╝██╔══██╗██╔══██╗╚══██╔══╝    ██╔════╝██║╚██╗██╔╝██╔════╝██╔══██╗
 ███████╗   ██║   ███████║██████╔╝   ██║       █████╗  ██║ ╚███╔╝ █████╗  ██║  ██║
 ╚════██║   ██║   ██╔══██║██╔══██╗   ██║       ██╔══╝  ██║ ██╔██╗ ██╔══╝  ██║  ██║
 ███████║   ██║   ██║  ██║██║  ██║   ██║       ██║     ██║██╔╝ ██╗███████╗██████╔╝
 ╚══════╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝       ╚═╝     ╚═╝╚═╝  ╚═╝╚══════╝╚═════╝ 
                                                                                   
        OpenWrt编译器修复版启动脚本
EOF
echo -e "${NC}"

log_info "🚀 启动OpenWrt编译器修复版..."

# 检查Docker环境
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

# 设置环境变量
export LANG=zh_CN.UTF-8
export LC_ALL=zh_CN.UTF-8
export PYTHONIOENCODING=utf-8

log_info "设置字符编码环境变量..."
log_info "LANG=$LANG"
log_info "LC_ALL=$LC_ALL"
log_info "PYTHONIOENCODING=$PYTHONIOENCODING"

# 创建必要目录
log_info "创建必要目录..."
mkdir -p workspace/{users,shared/{cache,downloads,ccache}}
mkdir -p logs/{compile,system,access,nginx}
mkdir -p data/{configs,firmware,uploads}
mkdir -p config tmp

# 停止现有服务
log_info "停止现有服务..."
docker-compose -f docker-compose.fixed.yml down 2>/dev/null || true
docker-compose down 2>/dev/null || true

# 清理旧容器（如果存在）
log_info "清理旧容器..."
docker rm -f openwrt-compiler-fixed openwrt-nginx-fixed openwrt-redis-fixed 2>/dev/null || true

# 构建修复版镜像
log_info "构建修复版Docker镜像..."
docker-compose -f docker-compose.fixed.yml build --no-cache

# 启动修复版服务
log_info "启动修复版服务..."
docker-compose -f docker-compose.fixed.yml up -d

# 等待服务启动
log_info "等待服务启动..."
sleep 20

# 检查服务状态
log_info "检查服务状态..."
docker-compose -f docker-compose.fixed.yml ps

# 检查容器健康状态
log_info "检查容器健康状态..."
for i in {1..30}; do
    if docker-compose -f docker-compose.fixed.yml ps | grep -q "healthy\|Up"; then
        log_success "服务启动成功！"
        break
    fi
    if [ $i -eq 30 ]; then
        log_warning "服务启动超时，但可能仍在初始化中"
    fi
    sleep 2
done

# 测试服务连接
log_info "测试服务连接..."

# 测试后端服务
if curl -f -s http://localhost:5000/api/health &> /dev/null; then
    log_success "✅ 后端服务连接正常 (端口 5000)"
else
    log_warning "⚠️ 后端服务连接失败 (端口 5000)"
fi

# 测试前端代理
if curl -f -s http://localhost:80/health &> /dev/null; then
    log_success "✅ 前端代理连接正常 (端口 80)"
else
    log_warning "⚠️ 前端代理连接失败 (端口 80)"
fi

# 显示访问信息
echo ""
log_success "🎉 OpenWrt编译器修复版启动完成！"
echo ""
echo -e "${CYAN}📍 访问地址:${NC}"
echo -e "   🌐 主页面: ${GREEN}http://localhost${NC}"
echo -e "   🌍 外网访问: ${GREEN}http://openwrt.xdaidai.com${NC}"
echo -e "   🔧 编码测试: ${GREEN}http://localhost/test-encoding${NC}"
echo -e "   💚 健康检查: ${GREEN}http://localhost/health${NC}"
echo -e "   📊 系统状态: ${GREEN}http://localhost/api/status${NC}"
echo ""
echo -e "${CYAN}🔧 管理命令:${NC}"
echo -e "   查看日志: ${YELLOW}docker-compose -f docker-compose.fixed.yml logs -f${NC}"
echo -e "   查看状态: ${YELLOW}docker-compose -f docker-compose.fixed.yml ps${NC}"
echo -e "   重启服务: ${YELLOW}docker-compose -f docker-compose.fixed.yml restart${NC}"
echo -e "   停止服务: ${YELLOW}docker-compose -f docker-compose.fixed.yml down${NC}"
echo ""
echo -e "${CYAN}🐛 故障排除:${NC}"
echo -e "   检查容器: ${YELLOW}docker ps | grep openwrt${NC}"
echo -e "   查看日志: ${YELLOW}docker logs openwrt-compiler-fixed${NC}"
echo -e "   进入容器: ${YELLOW}docker exec -it openwrt-compiler-fixed /bin/bash${NC}"
echo ""

# 显示服务日志（最后几行）
log_info "显示最新服务日志..."
docker-compose -f docker-compose.fixed.yml logs --tail=10

echo ""
log_success "✨ 修复版启动完成！如果网页仍显示乱码，请检查浏览器编码设置。"
