# OpenWrt编译器Docker本地部署指南

## 🎯 Docker本地模式特性

Docker本地模式是专为解决Docker网络仓库依赖问题而设计的部署方案：

### ✅ 核心优势
- **🚫 无外部依赖** - 本地构建Docker镜像，不依赖Docker Hub
- **📦 自动拉取** - 启动脚本自动拉取项目代码
- **🐳 容器化部署** - 完整的Docker服务编排
- **🔧 一键安装** - 全自动化安装流程
- **🌐 服务编排** - 主服务 + Nginx代理 + Redis缓存

### 🏗️ 架构设计
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Nginx代理     │    │  主应用容器      │    │   Redis缓存     │
│   端口: 80      │◄──►│  OpenWrt编译器   │◄──►│   会话存储      │
│   反向代理      │    │   端口: 9963     │    │   端口: 6379    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   数据卷管理     │
                    │  workspace/     │
                    │  logs/          │
                    │  data/          │
                    └─────────────────┘
```

## 🚀 快速部署

### 方法一：一键安装（推荐）

```bash
# 运行Docker本地安装脚本
./install-docker-local.sh

# 或使用自定义配置
./install-docker-local.sh -p 8080 -d /home/openwrt
```

### 方法二：手动安装

```bash
# 1. 检查Docker环境
docker --version
docker-compose --version
docker info

# 2. 运行安装脚本
./install-docker-local.sh --debug

# 3. 验证安装
cd /opt/openwrt-compiler
./status.sh
```

## 📋 安装选项

### 命令行参数

```bash
./install-docker-local.sh [选项]

选项:
  -p, --port PORT         设置服务端口 (默认: 9963)
  -d, --dir DIR          设置安装目录 (默认: /opt/openwrt-compiler)
  -r, --repo URL         设置Git仓库地址
  --no-start             安装后不自动启动服务
  --force                强制安装，跳过确认
  --debug                启用调试模式
  -h, --help             显示帮助信息
```

### 配置示例

```bash
# 基础安装
./install-docker-local.sh

# 自定义端口
./install-docker-local.sh -p 8080

# 自定义目录
./install-docker-local.sh -d /home/openwrt-compiler

# 强制安装（跳过确认）
./install-docker-local.sh --force

# 调试模式
./install-docker-local.sh --debug --no-start
```

## 🔧 系统要求

### 最低要求
- **操作系统**: Debian 10+, Ubuntu 18.04+
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **内存**: 4GB RAM
- **磁盘**: 50GB 可用空间
- **CPU**: 2核心

### 推荐配置
- **内存**: 8GB+ RAM
- **磁盘**: 100GB+ SSD
- **CPU**: 4核心+
- **网络**: 稳定的互联网连接

### Docker环境准备

```bash
# Ubuntu/Debian安装Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# 安装Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 启动Docker服务
sudo systemctl start docker
sudo systemctl enable docker

# 验证安装
docker --version
docker-compose --version
docker info
```

## 📁 部署后目录结构

```
/opt/openwrt-compiler/
├── Dockerfile                # Docker镜像构建文件
├── docker-compose.yml        # 服务编排配置
├── .env                      # 环境变量配置
├── backend/                  # 后端Python代码
├── frontend/                 # 前端Web文件
├── config/                   # 配置文件
│   ├── nginx.conf           # Nginx配置
│   └── redis.conf           # Redis配置
├── workspace/                # 工作空间
│   ├── users/               # 用户目录
│   └── shared/              # 共享缓存
├── logs/                     # 日志目录
│   ├── compile/             # 编译日志
│   ├── system/              # 系统日志
│   └── nginx/               # Nginx日志
├── data/                     # 数据目录
├── start.sh                 # 启动脚本
├── stop.sh                  # 停止脚本
├── restart.sh               # 重启脚本
├── status.sh                # 状态检查
└── logs.sh                  # 日志查看
```

## 🛠️ 服务管理

### 使用管理脚本

```bash
# 进入安装目录
cd /opt/openwrt-compiler

# 启动服务
./start.sh

# 停止服务
./stop.sh

# 重启服务
./restart.sh

# 查看状态
./status.sh

# 查看日志
./logs.sh           # 查看所有日志
./logs.sh -f        # 实时查看日志
```

### 使用Docker Compose

```bash
# 进入安装目录
cd /opt/openwrt-compiler

# 启动服务
docker-compose up -d

# 停止服务
docker-compose down

# 重启服务
docker-compose restart

# 查看状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 重建镜像
docker-compose build --no-cache
```

### 容器管理

```bash
# 查看容器
docker ps

# 进入主容器
docker exec -it openwrt-compiler /bin/bash

# 进入Nginx容器
docker exec -it openwrt-nginx /bin/sh

# 进入Redis容器
docker exec -it openwrt-redis /bin/sh

# 查看容器日志
docker logs openwrt-compiler -f
```

## 🌐 访问方式

### 直接访问
- **主服务**: http://localhost:9963
- **网络访问**: http://YOUR_IP:9963

### 代理访问
- **Nginx代理**: http://localhost
- **健康检查**: http://localhost/health

### API接口
- **健康检查**: http://localhost:9963/api/health
- **系统状态**: http://localhost:9963/api/status
- **设备列表**: http://localhost:9963/api/devices

## 🔍 故障排除

### 常见问题

#### 1. Docker权限问题
```bash
# 添加用户到docker组
sudo usermod -aG docker $USER
newgrp docker

# 或使用sudo运行
sudo ./install-docker-local.sh
```

#### 2. 端口冲突
```bash
# 检查端口占用
netstat -tlnp | grep :9963

# 使用其他端口
./install-docker-local.sh -p 8080
```

#### 3. 镜像构建失败
```bash
# 清理Docker缓存
docker system prune -f

# 重新构建
cd /opt/openwrt-compiler
docker-compose build --no-cache
```

#### 4. 服务启动失败
```bash
# 查看详细日志
cd /opt/openwrt-compiler
./logs.sh

# 检查容器状态
docker-compose ps

# 重启服务
./restart.sh
```

#### 5. 网络连接问题
```bash
# 检查Docker网络
docker network ls

# 重建网络
docker-compose down
docker-compose up -d
```

### 日志查看

```bash
# 安装日志
cat /tmp/openwrt-docker-install.log

# 应用日志
cd /opt/openwrt-compiler
./logs.sh

# 特定服务日志
docker-compose logs openwrt-compiler
docker-compose logs nginx-proxy
docker-compose logs redis-cache

# 实时日志
docker-compose logs -f
```

## 📊 性能监控

### 资源监控
```bash
# 查看容器资源使用
docker stats

# 查看系统状态
cd /opt/openwrt-compiler
./status.sh

# 查看磁盘使用
docker system df
```

### 性能优化
```bash
# 清理未使用的镜像
docker image prune -f

# 清理未使用的容器
docker container prune -f

# 清理未使用的卷
docker volume prune -f

# 完整清理
docker system prune -a -f
```

## 🔄 升级和维护

### 升级应用
```bash
cd /opt/openwrt-compiler

# 停止服务
./stop.sh

# 拉取最新代码
git pull origin main

# 重建镜像
docker-compose build --no-cache

# 启动服务
./start.sh
```

### 备份数据
```bash
# 备份用户数据
cd /opt/openwrt-compiler
tar -czf openwrt-backup-$(date +%Y%m%d).tar.gz \
    workspace/users data logs .env

# 备份Docker镜像
docker save openwrt-compiler:latest | gzip > openwrt-image-backup.tar.gz
```

### 恢复数据
```bash
# 恢复用户数据
tar -xzf openwrt-backup-YYYYMMDD.tar.gz

# 恢复Docker镜像
docker load < openwrt-image-backup.tar.gz
```

## 📞 技术支持

如有问题，请提供以下信息：

1. **系统信息**:
   ```bash
   uname -a
   docker --version
   docker-compose --version
   ```

2. **服务状态**:
   ```bash
   cd /opt/openwrt-compiler && ./status.sh
   ```

3. **错误日志**:
   ```bash
   cat /tmp/openwrt-docker-install.log
   cd /opt/openwrt-compiler && ./logs.sh
   ```

---

🎉 **Docker本地模式部署完成，享受容器化的OpenWrt编译体验！**
