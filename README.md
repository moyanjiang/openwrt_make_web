# OpenWrt编译器 - Docker本地部署版

🚀 **OpenWrt固件在线编译系统 - Docker本地化部署方案**

[![Docker](https://img.shields.io/badge/Docker-20.10+-blue.svg)](https://www.docker.com/)
[![Docker Compose](https://img.shields.io/badge/Docker%20Compose-2.0+-blue.svg)](https://docs.docker.com/compose/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![OpenWrt](https://img.shields.io/badge/Target-OpenWrt-orange.svg)](https://openwrt.org/)

## 🎯 项目特色

### � Docker本地化部署
- **� 无外部依赖** - 本地构建Docker镜像，不依赖Docker Hub
- **📦 自动拉取项目** - 启动脚本自动从GitHub拉取最新代码
- **🔧 一键部署** - 全自动化安装和配置流程
- **🌐 完整服务编排** - 主服务 + Nginx代理 + Redis缓存
- **🛠️ 便捷管理** - 提供完整的管理脚本集

### �️ 容器化架构
- **主应用容器** - OpenWrt编译器核心服务
- **Nginx代理容器** - 反向代理和负载均衡
- **Redis缓存容器** - 会话存储和数据缓存
- **数据卷管理** - 持久化存储工作空间和日志
- **网络隔离** - 独立的Docker网络环境

### ⚡ 性能优化
- **ccache编译加速** - 显著提升重复编译速度
- **多用户支持** - 用户隔离的编译环境
- **实时日志** - WebSocket实时日志查看
- **智能缓存** - Redis缓存加速数据访问
- **资源限制** - 合理的CPU和内存限制

## 🚀 快速部署

### 方式一：一键Docker部署（推荐）
```bash
# 下载并运行Docker本地部署脚本
curl -fsSL https://raw.githubusercontent.com/moyanjiang/openwrt_make_web/main/install-docker-local.sh | bash

# 或者使用自定义配置
curl -fsSL https://raw.githubusercontent.com/moyanjiang/openwrt_make_web/main/install-docker-local.sh | bash -s -- -p 8080
```

### 方式二：手动Docker部署
```bash
# 1. 克隆项目
git clone https://github.com/moyanjiang/openwrt_make_web.git
cd openwrt_make_web

# 2. 运行Docker部署脚本
chmod +x install-docker-local.sh
./install-docker-local.sh

# 3. 验证安装
./test-docker-local.sh
```

### 部署选项

| 选项 | 说明 | 默认值 |
|------|------|--------|
| `-p, --port` | 服务端口 | 9963 |
| `-d, --dir` | 安装目录 | /opt/openwrt-compiler |
| `-r, --repo` | Git仓库地址 | 官方仓库 |
| `--no-start` | 安装后不自动启动 | - |
| `--force` | 强制安装，跳过确认 | - |
| `--debug` | 启用调试模式 | - |

## � Docker环境要求

### 最低要求
- **操作系统**: Ubuntu 18.04+, Debian 10+, CentOS 7+
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
```

## 🛠️ 服务管理

### 使用管理脚本
```bash
# 进入安装目录
cd /opt/openwrt-compiler

# 服务管理
./start.sh                 # 启动所有Docker服务
./stop.sh                  # 停止所有Docker服务
./restart.sh               # 重启所有Docker服务
./status.sh                # 查看服务状态

# 日志管理
./logs.sh                  # 查看所有服务日志
./logs.sh -f               # 实时查看日志
```

### 使用Docker Compose
```bash
# 进入安装目录
cd /opt/openwrt-compiler

# 服务管理
docker-compose up -d       # 启动服务
docker-compose down        # 停止服务
docker-compose restart     # 重启服务
docker-compose ps          # 查看容器状态

# 日志查看
docker-compose logs -f     # 实时查看所有日志
docker-compose logs openwrt-compiler  # 查看指定服务日志

# 容器管理
docker exec -it openwrt-compiler /bin/bash  # 进入主容器
docker-compose build --no-cache             # 重建镜像
```

## 🎯 使用方法

### 1. 访问Web界面
安装完成后，打开浏览器访问：
- **主服务**: http://localhost:9963
- **Nginx代理**: http://localhost (如果启用)

### 2. 用户注册
首次访问需要注册用户账号，第一个注册的用户自动成为管理员。

### 3. 开始编译
1. **选择设备** - 搜索并选择目标设备型号
2. **配置选项** - 使用Web版menuconfig配置编译选项
3. **选择软件包** - 选择需要的软件包和插件
4. **开始编译** - 点击开始编译按钮
5. **实时监控** - 查看编译进度和日志
6. **下载固件** - 编译完成后下载固件文件

## 🏗️ Docker架构

### 容器架构图
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Nginx代理     │    │  主应用容器      │    │   Redis缓存     │
│   nginx:alpine  │◄──►│  openwrt-       │◄──►│  redis:7-alpine │
│   端口: 80/443  │    │  compiler       │    │   端口: 6379    │
│                 │    │   端口: 9963    │    │   (内部访问)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   数据卷管理     │
                    │  workspace/     │
                    │  logs/          │
                    │  data/          │
                    │  config/        │
                    └─────────────────┘
```

### 服务组成
- **openwrt-compiler**: 主应用容器，基于Ubuntu 22.04构建
- **nginx-proxy**: Nginx反向代理，提供负载均衡和SSL终止
- **redis-cache**: Redis缓存服务，用于会话存储和数据缓存
- **数据卷**: 持久化存储用户数据、日志和配置文件

## ⚙️ Docker配置说明

### 环境变量 (.env)
```bash
# 基础配置
PORT=9963
DEBUG=false
TZ=Asia/Shanghai
MODE=docker-local

# 服务配置
HOST=0.0.0.0
WORKERS=4
MAX_COMPILE_JOBS=2

# 编译配置
DEFAULT_THREADS=$(nproc)
ENABLE_CCACHE=true
CCACHE_SIZE=10G
ENABLE_ISTORE=true

# 邮箱配置（可选）
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-password

# iStore配置
ISTORE_REPO=https://github.com/linkease/istore.git

# 安全配置
SECRET_KEY=your-secret-key
SESSION_TIMEOUT=3600
```

## � Docker故障排除

### 常见问题

#### 1. Docker权限问题
```bash
# 添加用户到docker组
sudo usermod -aG docker $USER
newgrp docker

# 或使用sudo运行
sudo ./install-docker-local.sh
```

#### 2. 端口被占用
```bash
# 检查端口占用
netstat -tlnp | grep :9963

# 使用其他端口安装
./install-docker-local.sh -p 8080
```

#### 3. 镜像构建失败
```bash
# 清理Docker缓存
docker system prune -f

# 重新构建镜像
cd /opt/openwrt-compiler
docker-compose build --no-cache
```

#### 4. 服务启动失败
```bash
# 查看容器状态
docker-compose ps

# 查看详细日志
cd /opt/openwrt-compiler
./logs.sh

# 重启服务
./restart.sh
```

#### 5. 容器无法访问
```bash
# 检查网络连接
docker network ls

# 测试容器连通性
docker exec -it openwrt-compiler ping redis-cache

# 重建网络
docker-compose down && docker-compose up -d
```

### 日志查看
```bash
# 安装日志
cat /tmp/openwrt-docker-install.log

# 应用日志
cd /opt/openwrt-compiler && ./logs.sh

# 特定服务日志
docker-compose logs openwrt-compiler
docker-compose logs nginx-proxy
docker-compose logs redis-cache

# 实时日志
docker-compose logs -f
```

## � 性能监控

### 资源监控
```bash
# 查看容器资源使用
docker stats

# 查看系统状态
cd /opt/openwrt-compiler && ./status.sh

# 查看磁盘使用
docker system df
```

## 🔄 升级维护

### 应用升级
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

### 数据备份
```bash
# 备份用户数据
cd /opt/openwrt-compiler
tar -czf openwrt-backup-$(date +%Y%m%d).tar.gz \
    workspace/users data logs .env

# 备份Docker镜像
docker save openwrt-compiler:latest | gzip > openwrt-image-backup.tar.gz
```

## 📁 Docker部署目录结构

```
/opt/openwrt-compiler/
├── Dockerfile                # Docker镜像构建文件
├── docker-compose.yml        # 服务编排配置
├── .env                      # 环境变量配置
├── backend/                  # 后端Python代码
├── frontend/                 # 前端Web界面
├── config/                   # 配置文件
│   ├── nginx.conf           # Nginx代理配置
│   └── redis.conf           # Redis缓存配置
├── workspace/                # 工作空间（数据卷）
│   ├── users/               # 用户隔离目录
│   └── shared/              # 共享缓存目录
├── logs/                     # 日志目录（数据卷）
├── data/                     # 数据目录（数据卷）
├── install-docker-local.sh   # Docker本地部署脚本
├── test-docker-local.sh      # 安装测试脚本
├── start.sh                  # 启动脚本
├── stop.sh                   # 停止脚本
├── restart.sh                # 重启脚本
├── status.sh                 # 状态检查脚本
└── logs.sh                   # 日志查看脚本
```

## 🌟 特性亮点

- ✅ **Docker本地化部署** - 无需依赖外部Docker仓库
- ✅ **自动拉取项目** - 启动脚本自动获取最新代码
- ✅ **一键安装部署** - 全自动化安装和配置
- ✅ **完整服务编排** - 主服务+代理+缓存架构
- ✅ **便捷服务管理** - 丰富的管理脚本
- ✅ **容器化隔离** - 安全的运行环境
- ✅ **数据持久化** - 完善的数据卷管理
- ✅ **性能优化** - ccache加速和Redis缓存

## 📞 技术支持

### 获取帮助
- **项目地址**: https://github.com/moyanjiang/openwrt_make_web
- **问题反馈**: 请在GitHub Issues中提交
- **功能建议**: 欢迎提交Pull Request
- **文档**: 查看项目Wiki和文档

### 提交问题时请提供
1. **系统信息**: `uname -a && docker --version`
2. **安装日志**: `cat /tmp/openwrt-docker-install.log`
3. **服务状态**: `cd /opt/openwrt-compiler && ./status.sh`
4. **错误日志**: `cd /opt/openwrt-compiler && ./logs.sh`

## 🤝 贡献

欢迎提交Issue和Pull Request来改进项目！

## 📄 许可证

本项目采用 [MIT License](LICENSE) 开源协议。

## 🙏 致谢

- [OpenWrt](https://openwrt.org/) - 开源路由器固件项目
- [LEDE](https://github.com/coolsnowwolf/lede) - Lean's OpenWrt源码
- [Docker](https://www.docker.com/) - 容器化平台

---

🎉 **享受Docker化的OpenWrt固件编译之旅！**

[![Docker](https://img.shields.io/badge/Powered%20by-Docker-blue.svg)](https://www.docker.com/)
[![OpenWrt](https://img.shields.io/badge/Target-OpenWrt-orange.svg)](https://openwrt.org/)