# OpenWrt 编译器部署指南

本文档详细介绍了OpenWrt编译器在不同环境下的部署方法。

## 📋 部署前准备

### 系统要求

#### 最低配置
- **CPU**: 4核心
- **内存**: 8GB RAM
- **存储**: 100GB 可用空间
- **网络**: 稳定的互联网连接

#### 推荐配置
- **CPU**: 8核心或更多
- **内存**: 16GB RAM或更多
- **存储**: 500GB SSD
- **网络**: 100Mbps或更快的网络连接

#### 支持的操作系统
- **Linux**: Ubuntu 20.04+, CentOS 8+, Debian 11+
- **Windows**: Windows 10/11 (WSL2推荐)
- **macOS**: macOS 11.0+

### 依赖软件

#### 必需软件
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y python3 python3-pip python3-venv git build-essential

# CentOS/RHEL
sudo yum install -y python3 python3-pip git gcc gcc-c++ make

# macOS (使用Homebrew)
brew install python3 git

# Windows (使用Chocolatey)
choco install python3 git
```

#### 编译工具链
```bash
# Ubuntu/Debian
sudo apt install -y build-essential libncurses5-dev libncursesw5-dev \
  zlib1g-dev gawk git gettext libssl-dev xsltproc rsync wget unzip

# CentOS/RHEL
sudo yum groupinstall -y "Development Tools"
sudo yum install -y ncurses-devel zlib-devel openssl-devel
```

## 🚀 部署方式

### 方式一：标准部署

#### 1. 下载源码
```bash
git clone https://github.com/your-username/openwrt-compiler.git
cd openwrt-compiler
```

#### 2. 创建虚拟环境
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate     # Windows
```

#### 3. 安装依赖
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### 4. 配置环境
```bash
# 复制配置文件
cp .env.example .env

# 编辑配置文件
nano .env
```

#### 5. 初始化工作目录
```bash
mkdir -p workspace/{lede,configs,firmware,uploads,temp}
mkdir -p logs
```

#### 6. 启动服务
```bash
# 方式一：直接启动
cd backend
python app.py

# 方式二：使用启动脚本 (Windows)
start_backend.bat

# 方式三：使用启动脚本 (Linux/macOS)
./start_backend.sh
```

### 方式二：Docker部署（推荐）

#### 1. 安装Docker
```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# 重新登录或执行
newgrp docker
```

#### 2. 使用Docker Compose
```bash
# 克隆项目
git clone https://github.com/your-username/openwrt-compiler.git
cd openwrt-compiler

# 启动服务
docker-compose up -d
```

#### 3. 自定义Docker配置
创建 `docker-compose.override.yml`:
```yaml
version: '3.8'
services:
  openwrt-compiler:
    environment:
      - FLASK_ENV=production
      - MAX_PARALLEL_JOBS=8
    volumes:
      - /path/to/your/workspace:/app/workspace
    ports:
      - "8080:5000"
```

### 方式三：系统服务部署

#### 1. 创建系统用户
```bash
sudo useradd -r -s /bin/false openwrt-compiler
sudo mkdir -p /opt/openwrt-compiler
sudo chown openwrt-compiler:openwrt-compiler /opt/openwrt-compiler
```

#### 2. 部署应用
```bash
# 复制文件
sudo cp -r . /opt/openwrt-compiler/
sudo chown -R openwrt-compiler:openwrt-compiler /opt/openwrt-compiler/

# 安装依赖
cd /opt/openwrt-compiler
sudo -u openwrt-compiler python3 -m venv venv
sudo -u openwrt-compiler venv/bin/pip install -r requirements.txt
```

#### 3. 创建systemd服务
创建 `/etc/systemd/system/openwrt-compiler.service`:
```ini
[Unit]
Description=OpenWrt Compiler Service
After=network.target

[Service]
Type=simple
User=openwrt-compiler
Group=openwrt-compiler
WorkingDirectory=/opt/openwrt-compiler
Environment=PATH=/opt/openwrt-compiler/venv/bin
ExecStart=/opt/openwrt-compiler/venv/bin/python backend/app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### 4. 启动服务
```bash
sudo systemctl daemon-reload
sudo systemctl enable openwrt-compiler
sudo systemctl start openwrt-compiler
sudo systemctl status openwrt-compiler
```

## 🌐 反向代理配置

### Nginx配置

#### 1. 安装Nginx
```bash
# Ubuntu/Debian
sudo apt install nginx

# CentOS/RHEL
sudo yum install nginx
```

#### 2. 配置虚拟主机
创建 `/etc/nginx/sites-available/openwrt-compiler`:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 重定向到HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL配置
    ssl_certificate /path/to/your/cert.pem;
    ssl_certificate_key /path/to/your/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;

    # 静态文件
    location / {
        root /opt/openwrt-compiler/frontend;
        index index.html;
        try_files $uri $uri/ =404;
    }

    # API代理
    location /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket代理
    location /socket.io/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 文件上传大小限制
    client_max_body_size 100M;

    # 安全头
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
}
```

#### 3. 启用配置
```bash
sudo ln -s /etc/nginx/sites-available/openwrt-compiler /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Apache配置

创建 `/etc/apache2/sites-available/openwrt-compiler.conf`:
```apache
<VirtualHost *:80>
    ServerName your-domain.com
    Redirect permanent / https://your-domain.com/
</VirtualHost>

<VirtualHost *:443>
    ServerName your-domain.com
    
    SSLEngine on
    SSLCertificateFile /path/to/your/cert.pem
    SSLCertificateKeyFile /path/to/your/key.pem
    
    DocumentRoot /opt/openwrt-compiler/frontend
    
    ProxyPreserveHost On
    ProxyRequests Off
    
    # API代理
    ProxyPass /api/ http://127.0.0.1:5000/api/
    ProxyPassReverse /api/ http://127.0.0.1:5000/api/
    
    # WebSocket代理
    ProxyPass /socket.io/ ws://127.0.0.1:5000/socket.io/
    ProxyPassReverse /socket.io/ ws://127.0.0.1:5000/socket.io/
</VirtualHost>
```

## 🔒 安全配置

### 防火墙设置

#### UFW (Ubuntu)
```bash
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

#### firewalld (CentOS)
```bash
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

### SSL证书

#### 使用Let's Encrypt
```bash
# 安装certbot
sudo apt install certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d your-domain.com

# 自动续期
sudo crontab -e
# 添加: 0 12 * * * /usr/bin/certbot renew --quiet
```

### 访问控制

#### IP白名单
在Nginx配置中添加:
```nginx
location /api/ {
    allow 192.168.1.0/24;
    allow 10.0.0.0/8;
    deny all;
    
    proxy_pass http://127.0.0.1:5000;
}
```

#### 基本认证
```bash
# 创建密码文件
sudo htpasswd -c /etc/nginx/.htpasswd admin

# 在Nginx配置中添加
auth_basic "Restricted Access";
auth_basic_user_file /etc/nginx/.htpasswd;
```

## 📊 监控和日志

### 日志配置

#### 应用日志
在 `.env` 文件中配置:
```bash
LOG_LEVEL=INFO
LOG_FILE=/var/log/openwrt-compiler/app.log
LOG_MAX_SIZE=10485760
LOG_BACKUP_COUNT=5
```

#### 系统日志
```bash
# 查看应用日志
sudo journalctl -u openwrt-compiler -f

# 查看Nginx日志
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### 监控工具

#### 使用Prometheus + Grafana
1. 安装Prometheus
2. 配置应用指标收集
3. 设置Grafana仪表板

#### 简单监控脚本
创建 `monitor.sh`:
```bash
#!/bin/bash
while true; do
    if ! curl -f http://localhost:5000/api/health > /dev/null 2>&1; then
        echo "$(date): Service is down" >> /var/log/openwrt-compiler/monitor.log
        # 发送告警邮件或重启服务
    fi
    sleep 60
done
```

## 🔧 性能优化

### 系统优化

#### 内核参数
在 `/etc/sysctl.conf` 中添加:
```bash
# 网络优化
net.core.somaxconn = 65535
net.core.netdev_max_backlog = 5000
net.ipv4.tcp_max_syn_backlog = 65535

# 文件描述符限制
fs.file-max = 2097152
```

#### 用户限制
在 `/etc/security/limits.conf` 中添加:
```bash
openwrt-compiler soft nofile 65535
openwrt-compiler hard nofile 65535
```

### 应用优化

#### Gunicorn配置
创建 `gunicorn.conf.py`:
```python
bind = "127.0.0.1:5000"
workers = 4
worker_class = "eventlet"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 300
keepalive = 2
```

启动命令:
```bash
gunicorn -c gunicorn.conf.py backend.app:app
```

## 🚨 故障排除

### 常见问题

#### 1. 服务无法启动
```bash
# 检查端口占用
sudo netstat -tlnp | grep :5000

# 检查权限
ls -la /opt/openwrt-compiler/

# 检查依赖
pip list
```

#### 2. 编译失败
```bash
# 检查磁盘空间
df -h

# 检查内存使用
free -h

# 检查编译工具
which gcc make
```

#### 3. WebSocket连接失败
```bash
# 检查防火墙
sudo ufw status

# 检查代理配置
sudo nginx -t
```

### 日志分析

#### 查看错误日志
```bash
# 应用错误
grep ERROR /var/log/openwrt-compiler/app.log

# 系统错误
sudo journalctl -u openwrt-compiler --since "1 hour ago"
```

#### 性能分析
```bash
# CPU使用率
top -p $(pgrep -f "python.*app.py")

# 内存使用
ps aux | grep python

# 磁盘I/O
iotop -p $(pgrep -f "python.*app.py")
```

## 📝 维护任务

### 定期维护

#### 日志轮转
```bash
# 配置logrotate
sudo nano /etc/logrotate.d/openwrt-compiler
```

```
/var/log/openwrt-compiler/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 openwrt-compiler openwrt-compiler
    postrotate
        systemctl reload openwrt-compiler
    endscript
}
```

#### 清理临时文件
```bash
# 创建清理脚本
cat > /opt/openwrt-compiler/cleanup.sh << 'EOF'
#!/bin/bash
find /opt/openwrt-compiler/workspace/temp -type f -mtime +7 -delete
find /opt/openwrt-compiler/workspace/uploads -type f -mtime +1 -delete
EOF

# 添加到crontab
echo "0 2 * * * /opt/openwrt-compiler/cleanup.sh" | sudo crontab -
```

### 备份策略

#### 配置备份
```bash
# 备份配置文件
tar -czf backup-$(date +%Y%m%d).tar.gz \
  /opt/openwrt-compiler/.env \
  /opt/openwrt-compiler/workspace/configs/
```

#### 自动备份脚本
```bash
#!/bin/bash
BACKUP_DIR="/backup/openwrt-compiler"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# 备份配置
tar -czf $BACKUP_DIR/config_$DATE.tar.gz \
  /opt/openwrt-compiler/.env \
  /opt/openwrt-compiler/workspace/configs/

# 保留最近30天的备份
find $BACKUP_DIR -name "config_*.tar.gz" -mtime +30 -delete
```

---

**注意**: 请根据实际环境调整配置参数，确保系统安全和性能。
