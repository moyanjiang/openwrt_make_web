# OpenWrt编译器 Docker部署指南

本文档详细介绍如何使用Docker部署OpenWrt编译器，支持开发环境和生产环境。

## 🏗️ 架构概览

### 服务架构
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   前端服务      │    │   后端API       │    │   Redis缓存     │
│   (Nginx)       │    │   (Flask)       │    │   (Redis)       │
│   端口: 9963    │    │   端口: 5000    │    │   端口: 6379    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   反向代理      │
                    │   (Nginx)       │
                    │   端口: 80/443  │
                    └─────────────────┘
```

### 端口配置
- **前端服务**: 9963 (Nginx静态文件服务)
- **后端API**: 5000 (Flask应用)
- **Redis缓存**: 6379 (内部通信)
- **反向代理**: 80/443 (生产环境)

## 🚀 快速开始

### 1. 环境准备

```bash
# 安装Docker和Docker Compose
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# 安装Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 重新登录以应用用户组更改
newgrp docker
```

### 2. 克隆项目

```bash
git clone https://github.com/your-username/openwrt-compiler.git
cd openwrt-compiler
```

### 3. 配置环境变量

```bash
# 复制环境变量示例文件
cp .env.example .env

# 编辑配置文件
nano .env
```

### 4. 启动服务

#### 开发环境
```bash
# 使用部署脚本
chmod +x scripts/docker-deploy.sh
./scripts/docker-deploy.sh dev

# 或直接使用docker-compose
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

#### 生产环境
```bash
# 使用部署脚本
./scripts/docker-deploy.sh prod

# 或直接使用docker-compose
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## 📋 详细配置

### 环境变量配置

#### 基础配置
```bash
# 应用环境
FLASK_ENV=production
FRONTEND_PORT=9963
DOWNLOAD_BASE_URL=http://localhost:9963
```

#### 邮箱通知配置
```bash
# Gmail配置
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com
```

#### 安全配置
```bash
# 生产环境请使用强密码
JWT_SECRET_KEY=your-super-secret-jwt-key
SECRET_KEY=your-super-secret-session-key
```

### Docker Compose配置

#### 开发环境特性
- 源码热重载
- 调试端口暴露
- 开发工具容器
- 邮件测试服务

#### 生产环境特性
- 资源限制
- 健康检查
- 日志管理
- 监控服务

## 🛠️ 部署脚本使用

### 基本命令
```bash
# 启动开发环境
./scripts/docker-deploy.sh dev

# 启动生产环境
./scripts/docker-deploy.sh prod

# 停止所有服务
./scripts/docker-deploy.sh stop

# 重启服务
./scripts/docker-deploy.sh restart

# 查看服务状态
./scripts/docker-deploy.sh status

# 查看日志
./scripts/docker-deploy.sh logs [service_name]

# 清理Docker资源
./scripts/docker-deploy.sh clean

# 备份数据
./scripts/docker-deploy.sh backup

# 恢复数据
./scripts/docker-deploy.sh restore backup/20240101_120000
```

### 高级选项
```bash
# 强制重新构建
./scripts/docker-deploy.sh dev --no-cache

# 强制清理所有资源
./scripts/docker-deploy.sh clean --force

# 详细输出
./scripts/docker-deploy.sh dev --verbose
```

## 🌐 访问地址

### 开发环境
- **前端界面**: http://localhost:9963
- **后端API**: http://localhost:5000
- **Redis管理**: http://localhost:8080 (Adminer)
- **邮件测试**: http://localhost:8025 (MailHog)

### 生产环境
- **主站点**: http://localhost:9963
- **Nginx代理**: http://localhost:80
- **监控面板**: http://localhost:3000 (Grafana)
- **指标收集**: http://localhost:9090 (Prometheus)

## 🔧 服务管理

### 查看服务状态
```bash
# 查看所有容器状态
docker-compose ps

# 查看资源使用情况
docker stats

# 查看服务日志
docker-compose logs -f [service_name]
```

### 进入容器
```bash
# 进入后端容器
docker-compose exec backend bash

# 进入前端容器
docker-compose exec frontend sh

# 进入Redis容器
docker-compose exec redis redis-cli
```

### 数据管理
```bash
# 备份工作空间
docker run --rm -v openwrt-compiler_workspace_data:/data -v $(pwd):/backup alpine tar czf /backup/workspace-backup.tar.gz -C /data .

# 恢复工作空间
docker run --rm -v openwrt-compiler_workspace_data:/data -v $(pwd):/backup alpine tar xzf /backup/workspace-backup.tar.gz -C /data
```

## 🔍 故障排除

### 常见问题

#### 1. 端口冲突
```bash
# 检查端口占用
netstat -tulpn | grep :9963
netstat -tulpn | grep :5000

# 修改端口配置
# 编辑 .env 文件中的 FRONTEND_PORT
```

#### 2. 权限问题
```bash
# 检查目录权限
ls -la workspace/ logs/

# 修复权限
sudo chown -R $USER:$USER workspace/ logs/
chmod 755 workspace/ logs/
```

#### 3. 内存不足
```bash
# 检查系统资源
free -h
df -h

# 调整Docker资源限制
# 编辑 docker-compose.prod.yml 中的 resources 配置
```

#### 4. 网络问题
```bash
# 检查Docker网络
docker network ls
docker network inspect openwrt-compiler_openwrt-network

# 重建网络
docker-compose down
docker network prune
docker-compose up -d
```

### 日志分析
```bash
# 查看应用日志
docker-compose logs backend | grep ERROR
docker-compose logs frontend | grep ERROR

# 查看系统日志
journalctl -u docker.service
```

## 📊 监控和维护

### 健康检查
```bash
# 检查服务健康状态
curl http://localhost:5000/api/health
curl http://localhost:9963/

# 查看健康检查日志
docker inspect --format='{{json .State.Health}}' openwrt-compiler-backend
```

### 性能监控
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin123)

### 定期维护
```bash
# 清理未使用的镜像
docker image prune -f

# 清理未使用的卷
docker volume prune -f

# 更新镜像
docker-compose pull
docker-compose up -d
```

## 🔒 安全建议

### 生产环境安全
1. **更改默认密码**: 修改所有默认密码
2. **启用HTTPS**: 配置SSL证书
3. **防火墙配置**: 限制端口访问
4. **定期更新**: 保持镜像和依赖最新

### SSL证书配置
```bash
# 生成自签名证书（开发用）
openssl req -x509 -newkey rsa:4096 -keyout docker/ssl/key.pem -out docker/ssl/cert.pem -days 365 -nodes

# 使用Let's Encrypt（生产用）
certbot certonly --standalone -d your-domain.com
cp /etc/letsencrypt/live/your-domain.com/fullchain.pem docker/ssl/cert.pem
cp /etc/letsencrypt/live/your-domain.com/privkey.pem docker/ssl/key.pem
```

## 📚 更多资源

- [Docker官方文档](https://docs.docker.com/)
- [Docker Compose文档](https://docs.docker.com/compose/)
- [Nginx配置指南](https://nginx.org/en/docs/)
- [项目GitHub仓库](https://github.com/your-username/openwrt-compiler)

---

**🎯 通过Docker部署，享受一致的开发和生产环境！**
