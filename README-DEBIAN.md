# OpenWrt 编译器 - Debian版

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Debian](https://img.shields.io/badge/Debian-11+-red.svg)](https://www.debian.org/)

专为Debian系统优化的OpenWrt固件在线编译系统，提供多用户支持、现代化Web界面和完整的编译管理功能。

## 🆕 Debian版新特性

### 🎯 核心改进
- **多用户系统**: 每个用户独立的编译环境和配置
- **设备搜索**: 支持CPU型号和设备名称智能搜索
- **Web版menuconfig**: 现代化的配置界面，告别传统命令行
- **简化软件包选择**: 驱动程序和插件库分类选择
- **自动iStore集成**: 一键启用iStore商店支持
- **Debian原生支持**: 完整的系统服务集成

### 🔧 技术升级
- **优化Git仓库管理**: 默认使用coolsnowwolf/lede，优化feeds更新流程
- **智能依赖管理**: 自动安装Debian编译依赖
- **systemd服务**: 支持系统服务管理
- **用户认证系统**: JWT令牌认证，安全的会话管理

## 🚀 快速开始

### 📋 系统要求

- **操作系统**: Debian 11+ 或 Ubuntu 20.04+
- **内存**: 建议8GB以上
- **磁盘空间**: 建议100GB以上
- **网络**: 稳定的互联网连接

### ⚡ 一键安装

```bash
# 克隆项目
git clone https://github.com/your-username/openwrt-compiler.git
cd openwrt-compiler

# 运行安装脚本（需要sudo权限）
sudo python3 setup.py
```

### 🔧 手动安装

1. **安装系统依赖**
```bash
sudo apt update
sudo apt install -y build-essential libncurses5-dev libncursesw5-dev \
    zlib1g-dev gawk git gettext libssl-dev xsltproc rsync wget unzip \
    python3 python3-pip python3-venv python3-dev subversion mercurial \
    bzr ecj fastjar file g++ java-propose-classpath libelf-dev \
    libncurses5-dev libncursesw5-dev libssl-dev python3-distutils \
    python3-setuptools rsync unzip zlib1g-dev swig aria2 libtinfo5
```

2. **创建虚拟环境**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. **启动服务**
```bash
cd backend
python app.py --host 0.0.0.0 --port 5000
```

## 🎨 用户界面

### 登录/注册界面
- 首次访问自动创建管理员账户
- 支持多用户注册和管理
- JWT令牌安全认证

### 设备选择界面
- 智能搜索：输入CPU型号或设备名称
- 热门设备快速选择
- 详细设备信息展示

### 软件包选择界面
- **简化视图**: 驱动程序 + 功能插件
- **高级配置**: 完整的软件包分类
- 实时搜索和过滤功能

### Web版配置界面
- 替代传统menuconfig
- 分类清晰的配置选项
- 实时配置验证

## 🔧 使用指南

### 1. 用户管理
```bash
# 首次访问会提示创建管理员账户
# 后续用户可以注册普通账户
# 每个用户拥有独立的编译环境
```

### 2. 设备选择
```bash
# 在设备搜索框中输入：
- 设备名称：如 "树莓派4B"
- CPU型号：如 "MT7621A"
- 关键词：如 "小米路由器"
```

### 3. 软件包配置
```bash
# 简化视图：
- 驱动程序：选择硬件驱动支持
- 功能插件：按分类选择应用

# 高级配置：
- 完整的软件包树
- 搜索和过滤功能
- 依赖关系检查
```

### 4. 编译流程
```bash
1. 选择设备 → 2. 配置软件包 → 3. 开始编译
# 支持iStore商店自动集成
# 实时编译日志显示
# 自动固件收集和下载
```

## 🛠️ 系统服务

### systemd服务管理
```bash
# 启动服务
sudo systemctl start openwrt-compiler

# 停止服务
sudo systemctl stop openwrt-compiler

# 查看状态
sudo systemctl status openwrt-compiler

# 开机自启
sudo systemctl enable openwrt-compiler
```

### 服务配置
服务文件位置：`/etc/systemd/system/openwrt-compiler.service`

## 📁 目录结构

```
openwrt-compiler/
├── backend/                    # 后端服务
│   ├── user_manager.py        # 用户管理
│   ├── device_manager.py      # 设备管理
│   ├── web_menuconfig.py      # Web配置界面
│   └── ...
├── frontend/                   # 前端界面
│   ├── assets/js/
│   │   ├── user-manager.js    # 用户管理组件
│   │   ├── device-search.js   # 设备搜索组件
│   │   └── package-selector.js # 软件包选择器
│   └── assets/css/
│       └── debian-theme.css   # Debian主题样式
├── workspace/                  # 工作区
│   └── users/                 # 用户工作空间
│       ├── user1/             # 用户1的环境
│       └── user2/             # 用户2的环境
└── setup.py                   # Debian优化安装脚本
```

## 🔐 安全特性

- **用户认证**: JWT令牌认证系统
- **权限隔离**: 每用户独立工作空间
- **输入验证**: 严格的参数验证
- **进程隔离**: 安全的命令执行环境

## 🚀 生产部署

### Nginx反向代理
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /socket.io/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### Docker部署
```bash
# 使用Docker Compose
docker-compose -f docker-compose.yml -f docker-compose.debian.yml up -d
```

## 📊 性能优化

- **编译缓存**: 自动启用ccache加速编译
- **并行编译**: 智能检测CPU核心数
- **增量编译**: 支持快速增量编译
- **资源监控**: 实时监控系统资源使用

## 🤝 贡献指南

1. Fork项目仓库
2. 创建功能分支 (`git checkout -b feature/debian-enhancement`)
3. 提交更改 (`git commit -m 'Add Debian-specific feature'`)
4. 推送到分支 (`git push origin feature/debian-enhancement`)
5. 创建Pull Request

## 📄 许可证

本项目采用 [MIT License](LICENSE) 开源协议。

## 🙏 致谢

- [Debian Project](https://www.debian.org/) - 优秀的Linux发行版
- [OpenWrt](https://openwrt.org/) - 开源路由器固件项目
- [LEDE](https://github.com/coolsnowwolf/lede) - Lean's OpenWrt源码
- [iStore](https://github.com/linkease/istore) - OpenWrt软件商店

---

**🎯 专为Debian用户优化，提供最佳的OpenWrt编译体验！**
