#!/bin/bash

# OpenWrt编译器网页乱码和内网穿透修复脚本
# 解决字符编码和代理配置问题

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

# 显示横幅
show_banner() {
    clear
    echo -e "${CYAN}"
    cat << 'EOF'
 ███████╗██╗██╗  ██╗    ███████╗███╗   ██╗ ██████╗ ██████╗ ██████╗ ██╗███╗   ██╗ ██████╗ 
 ██╔════╝██║╚██╗██╔╝    ██╔════╝████╗  ██║██╔════╝██╔═══██╗██╔══██╗██║████╗  ██║██╔════╝ 
 █████╗  ██║ ╚███╔╝     █████╗  ██╔██╗ ██║██║     ██║   ██║██║  ██║██║██╔██╗ ██║██║  ███╗
 ██╔══╝  ██║ ██╔██╗     ██╔══╝  ██║╚██╗██║██║     ██║   ██║██║  ██║██║██║╚██╗██║██║   ██║
 ██║     ██║██╔╝ ██╗    ███████╗██║ ╚████║╚██████╗╚██████╔╝██████╔╝██║██║ ╚████║╚██████╔╝
 ╚═╝     ╚═╝╚═╝  ╚═╝    ╚══════╝╚═╝  ╚═══╝ ╚═════╝ ╚═════╝ ╚═════╝ ╚═╝╚═╝  ╚═══╝ ╚═════╝ 
                                                                                          
        网页乱码和内网穿透修复工具
EOF
    echo -e "${NC}"
    echo -e "${GREEN}🔧 OpenWrt编译器问题修复工具${NC}"
    echo -e "${BLUE}🌐 目标网址: http://openwrt.xdaidai.com${NC}"
    echo ""
}

# 检查当前服务状态
check_service_status() {
    log_info "检查当前服务状态..."
    
    # 检查Docker服务
    if command -v docker &> /dev/null; then
        if docker ps | grep -q openwrt; then
            log_success "发现运行中的OpenWrt容器"
            docker ps | grep openwrt
        else
            log_warning "未发现运行中的OpenWrt容器"
        fi
    else
        log_warning "Docker未安装或不可用"
    fi
    
    # 检查端口占用
    local common_ports=(80 443 5000 8000 9963)
    for port in "${common_ports[@]}"; do
        if netstat -tlnp 2>/dev/null | grep -q ":$port "; then
            log_info "端口 $port 正在使用"
            netstat -tlnp 2>/dev/null | grep ":$port "
        fi
    done
}

# 修复字符编码问题
fix_encoding_issues() {
    log_info "修复字符编码问题..."
    
    # 设置系统locale
    log_info "配置系统locale..."
    
    # 检查当前locale
    local current_locale=$(locale | grep LANG= | cut -d= -f2)
    log_info "当前locale: $current_locale"
    
    # 确保UTF-8支持
    if ! locale -a | grep -q "zh_CN.utf8\|en_US.utf8"; then
        log_warning "系统缺少UTF-8 locale支持"
        
        # 生成locale（如果可能）
        if command -v locale-gen &> /dev/null; then
            sudo locale-gen zh_CN.UTF-8 en_US.UTF-8 2>/dev/null || true
        fi
    fi
    
    # 创建环境变量配置
    cat > /tmp/encoding_fix.env << 'EOF'
# 字符编码修复配置
export LANG=zh_CN.UTF-8
export LC_ALL=zh_CN.UTF-8
export LC_CTYPE=zh_CN.UTF-8
export PYTHONIOENCODING=utf-8
export PYTHONUNBUFFERED=1
EOF
    
    log_success "字符编码配置已创建"
}

# 修复HTML文件编码
fix_html_encoding() {
    log_info "修复HTML文件编码..."
    
    # 查找HTML文件
    local html_files=(
        "frontend/index.html"
        "frontend/*.html"
        "backend/templates/*.html"
    )
    
    for pattern in "${html_files[@]}"; do
        for file in $pattern; do
            if [[ -f "$file" ]]; then
                log_info "处理文件: $file"
                
                # 检查文件编码
                local encoding=$(file -bi "$file" | cut -d= -f2)
                log_info "文件编码: $encoding"
                
                # 确保HTML文件有正确的meta标签
                if ! grep -q "charset.*utf-8" "$file"; then
                    log_warning "文件缺少UTF-8编码声明，正在修复..."
                    
                    # 备份原文件
                    cp "$file" "$file.backup"
                    
                    # 添加UTF-8编码声明
                    if grep -q "<head>" "$file"; then
                        sed -i '/<head>/a\    <meta charset="UTF-8">' "$file"
                    elif grep -q "<html>" "$file"; then
                        sed -i '/<html>/a\<head>\n    <meta charset="UTF-8">\n</head>' "$file"
                    fi
                    
                    log_success "已修复文件编码: $file"
                fi
            fi
        done
    done
}

# 创建Nginx配置修复代理问题
create_nginx_proxy_config() {
    log_info "创建Nginx代理配置..."
    
    mkdir -p config/nginx/conf.d
    
    cat > config/nginx/conf.d/encoding-fix.conf << 'EOF'
# 字符编码和代理修复配置

# 设置默认字符集
charset utf-8;
charset_types text/xml text/plain text/vnd.wap.wml application/javascript application/rss+xml;

# 上游服务器配置
upstream openwrt_backend {
    server 127.0.0.1:5000;
    server 127.0.0.1:8000 backup;
    server 127.0.0.1:9963 backup;
}

# 主服务器配置
server {
    listen 80;
    server_name openwrt.xdaidai.com _;
    
    # 字符编码设置
    charset utf-8;
    
    # 安全头设置
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # 代理设置
    location / {
        proxy_pass http://openwrt_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # 编码设置
        proxy_set_header Accept-Charset "utf-8";
        
        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # 缓冲设置
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
    }
    
    # 静态文件处理
    location ~* \.(css|js|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
        add_header Vary "Accept-Encoding";
        
        # 尝试本地文件，否则代理
        try_files $uri @backend;
    }
    
    location @backend {
        proxy_pass http://openwrt_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # 错误页面
    error_page 404 /404.html;
    error_page 500 502 503 504 /50x.html;
    
    # 日志设置
    access_log /var/log/nginx/openwrt_access.log;
    error_log /var/log/nginx/openwrt_error.log;
}
EOF
    
    log_success "Nginx代理配置已创建"
}

# 创建修复后的Docker Compose配置
create_fixed_docker_compose() {
    log_info "创建修复后的Docker Compose配置..."
    
    cat > docker-compose-fixed.yml << 'EOF'
version: '3.8'

services:
  # OpenWrt编译器主服务
  openwrt-compiler:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: openwrt-compiler-fixed
    hostname: openwrt-compiler
    restart: unless-stopped
    
    environment:
      - PORT=5000
      - LANG=zh_CN.UTF-8
      - LC_ALL=zh_CN.UTF-8
      - PYTHONIOENCODING=utf-8
      - PYTHONUNBUFFERED=1
      - TZ=Asia/Shanghai
    
    ports:
      - "5000:5000"
      - "8000:8000"
    
    volumes:
      - ./workspace:/app/workspace
      - ./logs:/app/logs
      - ./data:/app/data
      - ./config:/app/config
    
    networks:
      - openwrt-network
    
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

  # Nginx代理服务
  nginx-proxy:
    image: nginx:alpine
    container_name: openwrt-nginx-proxy
    restart: unless-stopped
    
    ports:
      - "80:80"
      - "443:443"
    
    volumes:
      - ./config/nginx/conf.d:/etc/nginx/conf.d:ro
      - ./logs/nginx:/var/log/nginx
    
    depends_on:
      - openwrt-compiler
    
    networks:
      - openwrt-network
    
    environment:
      - TZ=Asia/Shanghai

networks:
  openwrt-network:
    driver: bridge
EOF
    
    log_success "修复后的Docker Compose配置已创建"
}

# 创建启动脚本
create_startup_script() {
    log_info "创建启动脚本..."
    
    cat > start-fixed.sh << 'EOF'
#!/bin/bash

# OpenWrt编译器修复版启动脚本

set -e

echo "🚀 启动修复版OpenWrt编译器..."

# 设置环境变量
export LANG=zh_CN.UTF-8
export LC_ALL=zh_CN.UTF-8
export PYTHONIOENCODING=utf-8
export PYTHONUNBUFFERED=1

# 创建必要目录
mkdir -p workspace logs data config/nginx/conf.d

# 停止现有服务
echo "停止现有服务..."
docker-compose -f docker-compose-fixed.yml down 2>/dev/null || true

# 启动修复版服务
echo "启动修复版服务..."
docker-compose -f docker-compose-fixed.yml up -d

# 等待服务启动
echo "等待服务启动..."
sleep 15

# 检查服务状态
echo "检查服务状态..."
docker-compose -f docker-compose-fixed.yml ps

# 测试连接
echo "测试服务连接..."
if curl -f -s http://localhost:5000/health &> /dev/null; then
    echo "✅ 服务启动成功！"
    echo "🌐 本地访问: http://localhost"
    echo "🌍 外网访问: http://openwrt.xdaidai.com"
else
    echo "❌ 服务启动失败，请检查日志"
    docker-compose -f docker-compose-fixed.yml logs
fi
EOF
    
    chmod +x start-fixed.sh
    log_success "启动脚本已创建"
}

# 创建测试页面
create_test_page() {
    log_info "创建测试页面..."
    
    mkdir -p frontend
    
    cat > frontend/test-encoding.html << 'EOF'
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OpenWrt编译器 - 编码测试</title>
    <style>
        body {
            font-family: 'Microsoft YaHei', 'SimHei', Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            min-height: 100vh;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: rgba(255,255,255,0.1);
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.2);
        }
        h1 { text-align: center; margin-bottom: 30px; }
        .test-section {
            background: rgba(255,255,255,0.1);
            padding: 20px;
            margin: 15px 0;
            border-radius: 10px;
        }
        .success { color: #4CAF50; }
        .warning { color: #FF9800; }
        .error { color: #F44336; }
        .info { color: #2196F3; }
        .code {
            background: rgba(0,0,0,0.3);
            padding: 10px;
            border-radius: 5px;
            font-family: 'Courier New', monospace;
            margin: 10px 0;
        }
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        .status-ok { background-color: #4CAF50; }
        .status-warning { background-color: #FF9800; }
        .status-error { background-color: #F44336; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔧 OpenWrt编译器编码测试</h1>
        
        <div class="test-section">
            <h3><span class="status-indicator status-ok"></span>中文字符测试</h3>
            <p>如果您能正常看到这些中文字符，说明编码配置正确：</p>
            <div class="code">
                测试字符串：你好世界！OpenWrt固件编译器
                特殊字符：①②③④⑤ ★☆♠♥♦♣ ←→↑↓
                技术术语：路由器、固件、编译、配置、安装
            </div>
        </div>
        
        <div class="test-section">
            <h3><span class="status-indicator status-ok"></span>网络连接测试</h3>
            <p>当前访问信息：</p>
            <div class="code" id="network-info">
                正在检测网络信息...
            </div>
        </div>
        
        <div class="test-section">
            <h3><span class="status-indicator status-warning"></span>服务状态检测</h3>
            <p>后端服务连接状态：</p>
            <div class="code" id="service-status">
                正在检测服务状态...
            </div>
        </div>
        
        <div class="test-section">
            <h3><span class="status-indicator status-info"></span>浏览器信息</h3>
            <div class="code" id="browser-info">
                正在获取浏览器信息...
            </div>
        </div>
        
        <div class="test-section">
            <h3>🔗 相关链接</h3>
            <p>
                <a href="/" style="color: #4CAF50;">返回主页</a> |
                <a href="/api/health" style="color: #4CAF50;">健康检查</a> |
                <a href="/api/status" style="color: #4CAF50;">系统状态</a>
            </p>
        </div>
    </div>

    <script>
        // 更新网络信息
        document.getElementById('network-info').innerHTML = `
            URL: ${window.location.href}
            主机: ${window.location.hostname}
            端口: ${window.location.port || '80'}
            协议: ${window.location.protocol}
            时间: ${new Date().toLocaleString('zh-CN')}
        `;
        
        // 更新浏览器信息
        document.getElementById('browser-info').innerHTML = `
            用户代理: ${navigator.userAgent}
            语言: ${navigator.language}
            平台: ${navigator.platform}
            Cookie启用: ${navigator.cookieEnabled}
            在线状态: ${navigator.onLine}
        `;
        
        // 检测服务状态
        fetch('/api/health')
            .then(response => response.json())
            .then(data => {
                document.getElementById('service-status').innerHTML = `
                    ✅ 后端服务正常
                    状态: ${data.status || '正常'}
                    时间: ${data.timestamp || new Date().toISOString()}
                `;
            })
            .catch(error => {
                document.getElementById('service-status').innerHTML = `
                    ❌ 后端服务连接失败
                    错误: ${error.message}
                    建议: 检查服务是否正常运行
                `;
            });
    </script>
</body>
</html>
EOF
    
    log_success "测试页面已创建"
}

# 主修复流程
main() {
    show_banner
    
    log_info "开始修复网页乱码和内网穿透问题..."
    
    # 1. 检查当前状态
    check_service_status
    
    # 2. 修复字符编码
    fix_encoding_issues
    fix_html_encoding
    
    # 3. 创建代理配置
    create_nginx_proxy_config
    
    # 4. 创建修复版配置
    create_fixed_docker_compose
    
    # 5. 创建启动脚本
    create_startup_script
    
    # 6. 创建测试页面
    create_test_page
    
    echo ""
    log_success "修复配置已完成！"
    echo ""
    echo -e "${CYAN}📋 下一步操作:${NC}"
    echo -e "1. 运行修复版服务: ${YELLOW}./start-fixed.sh${NC}"
    echo -e "2. 测试编码页面: ${YELLOW}http://localhost/test-encoding.html${NC}"
    echo -e "3. 访问主页面: ${YELLOW}http://openwrt.xdaidai.com${NC}"
    echo ""
    echo -e "${CYAN}🔧 故障排除:${NC}"
    echo -e "- 查看服务日志: ${YELLOW}docker-compose -f docker-compose-fixed.yml logs${NC}"
    echo -e "- 检查服务状态: ${YELLOW}docker-compose -f docker-compose-fixed.yml ps${NC}"
    echo -e "- 重启服务: ${YELLOW}docker-compose -f docker-compose-fixed.yml restart${NC}"
    echo ""
    echo -e "${GREEN}✨ 修复完成！${NC}"
}

# 运行主函数
main "$@"
