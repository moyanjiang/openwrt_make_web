# OpenWrt 编译器 - 重构版

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Debian](https://img.shields.io/badge/Debian-11+-red.svg)](https://www.debian.org/)

全面重构的OpenWrt固件在线编译系统，专为Debian系统优化，提供完整的多用户支持、邮件通知、用户计时统计等高级功能。

## 🆕 重构版新特性

### 🎯 核心功能重构
- **用户计时系统**: 详细记录每个用户的编译时间、登录时间等统计信息
- **邮件通知系统**: 编译完成后自动发送邮件通知，包含固件下载链接
- **Git仓库优化**: 使用 `git clone https://github.com/coolsnowwolf/lede`，自动集成iStore
- **仓库管理增强**: 独立的更新、重构功能，支持选择是否包含iStore
- **编译流程优化**: 添加 `make download -j8` 预下载步骤
- **用户环境隔离**: 每个用户完全独立的编译环境和配置

### 🔧 技术架构升级
- **模块化设计**: 完全重构的后端架构，清晰的模块分离
- **RESTful API**: 标准化的API接口设计
- **WebSocket实时通信**: 实时编译进度和日志推送
- **JWT认证系统**: 安全的用户认证和会话管理
- **邮件服务集成**: SMTP邮件发送支持

## 🚀 快速开始

### 📋 系统要求

- **操作系统**: Debian 11+ 或 Ubuntu 20.04+
- **内存**: 建议16GB以上（多用户编译）
- **磁盘空间**: 建议200GB以上
- **网络**: 稳定的互联网连接
- **邮箱服务**: SMTP邮箱账户（可选）

### ⚡ 一键安装

```bash
# 克隆项目
git clone https://github.com/your-username/openwrt-compiler.git
cd openwrt-compiler

# 运行重构版安装脚本
sudo python3 setup.py
```

### 🔧 环境变量配置

创建 `.env` 文件配置邮箱服务：

```bash
# 邮箱配置
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com

# 下载基础URL
DOWNLOAD_BASE_URL=http://your-domain.com:5000
```

## 🎨 用户界面重构

### 1. 用户认证系统
- **注册/登录**: 现代化的认证界面
- **JWT令牌**: 安全的会话管理
- **首个用户**: 自动成为管理员

### 2. 仓库管理界面
- **实时状态**: 显示仓库当前状态和最后提交信息
- **一键操作**: 克隆、更新、重构仓库
- **iStore选项**: 可选择是否集成iStore商店
- **操作进度**: 实时显示操作进度和日志

### 3. 用户统计面板
- **编译统计**: 总次数、成功率、平均时间
- **时间统计**: 总编译时间、登录次数
- **历史记录**: 最近编译历史和状态

### 4. 增强编译控制
- **编译摘要**: 显示选择的设备和软件包
- **邮件通知**: 可选择编译完成邮件通知
- **实时进度**: 分阶段显示编译进度
- **计时器**: 实时显示编译耗时

## 🔧 使用指南

### 1. 用户管理
```bash
# 用户注册
POST /api/auth/register
{
  "username": "user1",
  "email": "user1@example.com",
  "password": "password123"
}

# 用户登录
POST /api/auth/login
{
  "username": "user1",
  "password": "password123"
}
```

### 2. 仓库管理
```bash
# 克隆仓库（包含iStore）
POST /api/repository/clone
{
  "force_rebuild": false,
  "enable_istore": true
}

# 更新仓库
POST /api/repository/update
{
  "enable_istore": true
}

# 重构仓库
POST /api/repository/rebuild
{
  "enable_istore": true
}
```

### 3. 编译流程
```bash
# 开始编译
POST /api/compile/start
{
  "username": "user1",
  "device_id": "x86_64",
  "device_name": "x86_64通用",
  "packages": ["luci-app-store", "luci-app-ddns"],
  "compile_threads": "auto",
  "enable_email_notification": true
}
```

### 4. 用户统计
```bash
# 获取用户统计
GET /api/users/{username}/statistics

# 获取编译历史
GET /api/users/{username}/compile-history?limit=10
```

## 📊 编译流程优化

### 新的编译步骤
1. **准备环境**: 检查仓库状态，清理之前的编译文件
2. **下载依赖**: 执行 `make download -j8` 预下载所有依赖包
3. **配置编译**: 应用设备配置和软件包选择
4. **执行编译**: 多线程编译固件
5. **打包固件**: 收集编译结果，生成下载链接

### iStore自动集成
```bash
# 自动添加到 feeds.conf.default
echo 'src-git istore https://github.com/linkease/istore;main' >> feeds.conf.default

# 自动更新和安装
./scripts/feeds update istore
./scripts/feeds install -d y -p istore luci-app-store
```

## 📧 邮件通知系统

### 编译成功通知
- **HTML格式**: 美观的邮件模板
- **下载链接**: 直接点击下载固件文件
- **编译信息**: 设备型号、编译时间、文件大小
- **有效期提醒**: 固件文件保留7天

### 编译失败通知
- **错误信息**: 详细的失败原因
- **日志摘要**: 关键错误日志
- **重试建议**: 常见问题解决方案

## 📁 重构后目录结构

```
openwrt-compiler/
├── backend/                    # 🐍 重构后端服务
│   ├── user_manager.py        # 用户管理（增强版）
│   ├── repository_manager.py  # Git仓库管理器
│   ├── email_notifier.py      # 邮件通知系统
│   ├── repository_controller.py # 仓库控制器
│   ├── device_manager.py      # 设备管理器
│   ├── web_menuconfig.py      # Web配置界面
│   └── compiler.py            # 编译管理器（重构版）
├── frontend/                   # 🌐 重构前端界面
│   ├── assets/js/
│   │   ├── user-manager.js    # 用户管理组件
│   │   ├── repository-manager.js # 仓库管理组件
│   │   ├── user-statistics.js # 用户统计组件
│   │   ├── device-search.js   # 设备搜索组件
│   │   └── package-selector.js # 软件包选择器
│   └── assets/css/
│       └── debian-theme.css   # 重构主题样式
├── workspace/                  # 🔧 用户工作区
│   └── users/                 # 用户独立环境
│       ├── user1/             # 用户1的完整环境
│       │   ├── lede/          # LEDE源码
│       │   ├── configs/       # 配置文件
│       │   ├── firmware/      # 固件输出
│       │   └── temp/          # 临时文件
│       └── user2/             # 用户2的完整环境
└── logs/                       # 📝 系统日志
```

## 🔐 安全特性增强

- **JWT认证**: 安全的令牌认证系统
- **用户隔离**: 完全独立的用户环境
- **权限控制**: 管理员和普通用户权限分离
- **输入验证**: 严格的参数验证和过滤
- **日志审计**: 完整的操作日志记录

## 📊 监控和统计

### 用户统计
- **编译统计**: 总次数、成功率、失败次数
- **时间统计**: 总编译时间、平均编译时间
- **活动统计**: 登录次数、最后活动时间
- **历史记录**: 详细的编译历史记录

### 系统监控
- **资源使用**: CPU、内存、磁盘使用情况
- **编译队列**: 当前编译任务状态
- **用户活动**: 在线用户和活动统计

## 🚀 生产部署

### Docker部署
```bash
# 使用Docker Compose
docker-compose -f docker-compose.yml -f docker-compose.production.yml up -d
```

### Nginx配置
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    # 静态文件
    location /static/ {
        alias /opt/openwrt-compiler/frontend/assets/;
        expires 1y;
    }
    
    # API代理
    location /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    
    # WebSocket代理
    location /socket.io/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## 📄 许可证

本项目采用 [MIT License](LICENSE) 开源协议。

## 🙏 致谢

- [Debian Project](https://www.debian.org/) - 优秀的Linux发行版
- [OpenWrt](https://openwrt.org/) - 开源路由器固件项目
- [LEDE](https://github.com/coolsnowwolf/lede) - Lean's OpenWrt源码
- [iStore](https://github.com/linkease/istore) - OpenWrt软件商店

---

**🎯 全面重构，专业级OpenWrt编译体验！**
