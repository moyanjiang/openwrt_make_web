# OpenWrt编译器本地模式部署指南

## 🎯 本地模式特性

本地模式是专为解决Docker网络依赖问题而设计的部署方案：

### ✅ 优势特性
- **无Docker依赖** - 直接使用系统Python环境
- **快速部署** - 无需下载Docker镜像
- **资源占用低** - 原生进程运行
- **易于调试** - 直接访问日志和文件
- **系统集成** - 支持systemd服务管理

### 🔧 技术架构
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Nginx代理     │    │  Python应用     │    │   文件系统      │
│   (可选)        │◄──►│  Flask服务      │◄──►│   工作空间      │
│   端口: 80      │    │   端口: 9963    │    │   用户数据      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 快速部署

### 方法一：一键安装（推荐）

```bash
# 下载并运行本地安装脚本
./install-local.sh

# 或使用自定义配置
./install-local.sh -p 8080 -d /home/openwrt
```

### 方法二：手动安装

```bash
# 1. 检查系统要求
python3 --version  # 需要 3.8+
free -h           # 建议 4GB+ 内存
df -h             # 建议 50GB+ 磁盘

# 2. 安装系统依赖
sudo apt update
sudo apt install -y python3 python3-pip python3-venv git build-essential

# 3. 克隆项目
git clone https://github.com/moyanjiang/openwrt_make_web.git
cd openwrt_make_web

# 4. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 5. 安装依赖
pip install -r requirements.txt

# 6. 启动服务
cd backend
python3 app.py --host 0.0.0.0 --port 9963
```

## 📋 安装选项

### 命令行参数

```bash
./install-local.sh [选项]

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
./install-local.sh

# 自定义端口
./install-local.sh -p 8080

# 自定义目录
./install-local.sh -d /home/openwrt-compiler

# 强制安装（跳过确认）
./install-local.sh --force

# 调试模式
./install-local.sh --debug
```

## 🔧 系统要求

### 最低要求
- **操作系统**: Debian 10+, Ubuntu 18.04+
- **Python**: 3.8+
- **内存**: 4GB RAM
- **磁盘**: 50GB 可用空间
- **CPU**: 2核心

### 推荐配置
- **内存**: 8GB+ RAM
- **磁盘**: 100GB+ SSD
- **CPU**: 4核心+
- **网络**: 稳定的互联网连接

### 系统依赖
```bash
# Debian/Ubuntu
sudo apt install -y \
    python3 python3-pip python3-venv python3-dev \
    build-essential git curl wget unzip \
    libncurses5-dev zlib1g-dev gawk gettext \
    libssl-dev xsltproc rsync ccache nginx

# CentOS/RHEL
sudo yum install -y \
    python3 python3-pip python3-devel \
    gcc gcc-c++ make git curl wget unzip \
    ncurses-devel zlib-devel gawk gettext \
    openssl-devel libxslt rsync ccache nginx
```

## 📁 目录结构

安装完成后的目录结构：

```
/opt/openwrt-compiler/
├── backend/              # 后端Python代码
│   ├── app.py           # 主应用文件
│   ├── compiler.py      # 编译管理
│   └── utils/           # 工具模块
├── frontend/             # 前端文件
├── workspace/            # 工作空间
│   ├── users/           # 用户目录
│   └── shared/          # 共享缓存
├── logs/                 # 日志目录
├── data/                 # 数据目录
├── venv/                 # Python虚拟环境
├── .env                  # 环境配置
├── start.sh             # 启动脚本
├── stop.sh              # 停止脚本
├── restart.sh           # 重启脚本
└── status.sh            # 状态检查
```

## 🛠️ 服务管理

### 手动管理

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
tail -f logs/app.log
```

### 系统服务管理

如果安装了systemd服务：

```bash
# 启动服务
sudo systemctl start openwrt-compiler

# 停止服务
sudo systemctl stop openwrt-compiler

# 重启服务
sudo systemctl restart openwrt-compiler

# 查看状态
sudo systemctl status openwrt-compiler

# 开机启动
sudo systemctl enable openwrt-compiler

# 禁用开机启动
sudo systemctl disable openwrt-compiler

# 查看日志
sudo journalctl -u openwrt-compiler -f
```

## 🌐 访问方式

### 直接访问
- **本地**: http://localhost:9963
- **网络**: http://YOUR_IP:9963

### Nginx代理访问
如果配置了Nginx代理：
- **HTTP**: http://localhost
- **域名**: http://your-domain.com

## 🔍 故障排除

### 常见问题

#### 1. 端口被占用
```bash
# 检查端口占用
netstat -tlnp | grep :9963

# 更换端口
./install-local.sh -p 8080
```

#### 2. Python版本过低
```bash
# 检查Python版本
python3 --version

# 升级Python（Ubuntu）
sudo apt update
sudo apt install python3.9
```

#### 3. 依赖安装失败
```bash
# 更新pip
pip install --upgrade pip

# 使用国内源
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
```

#### 4. 服务启动失败
```bash
# 检查日志
tail -f /opt/openwrt-compiler/logs/app.log

# 检查虚拟环境
source /opt/openwrt-compiler/venv/bin/activate
python3 -c "import flask; print('Flask OK')"

# 手动启动调试
cd /opt/openwrt-compiler/backend
python3 app.py --debug
```

#### 5. 权限问题
```bash
# 修复权限
sudo chown -R $USER:$USER /opt/openwrt-compiler
chmod +x /opt/openwrt-compiler/*.sh
```

### 日志查看

```bash
# 应用日志
tail -f /opt/openwrt-compiler/logs/app.log

# 安装日志
cat /tmp/openwrt-install-local.log

# 系统服务日志
sudo journalctl -u openwrt-compiler -f

# 编译日志
tail -f /opt/openwrt-compiler/logs/compile/*.log
```

## 📊 性能优化

### 编译优化
```bash
# 启用ccache
export CCACHE_DIR=/opt/openwrt-compiler/workspace/shared/ccache
ccache --set-config=max_size=10G

# 设置编译线程数
export MAKE_JOBS=$(nproc)
```

### 系统优化
```bash
# 增加文件描述符限制
echo "* soft nofile 65536" | sudo tee -a /etc/security/limits.conf
echo "* hard nofile 65536" | sudo tee -a /etc/security/limits.conf

# 优化内存使用
echo "vm.swappiness=10" | sudo tee -a /etc/sysctl.conf
```

## 🔄 升级和维护

### 升级应用
```bash
cd /opt/openwrt-compiler
git pull origin main
source venv/bin/activate
pip install -r requirements.txt --upgrade
./restart.sh
```

### 备份数据
```bash
# 备份用户数据
tar -czf openwrt-backup-$(date +%Y%m%d).tar.gz \
    workspace/users data logs .env

# 恢复数据
tar -xzf openwrt-backup-YYYYMMDD.tar.gz
```

### 清理缓存
```bash
# 清理编译缓存
rm -rf workspace/shared/cache/*

# 清理ccache
ccache --clear

# 清理日志
find logs -name "*.log" -mtime +7 -delete
```

## 📞 技术支持

如有问题，请提供以下信息：

1. **系统信息**:
   ```bash
   uname -a
   python3 --version
   cat /etc/os-release
   ```

2. **服务状态**:
   ```bash
   cd /opt/openwrt-compiler && ./status.sh
   ```

3. **错误日志**:
   ```bash
   tail -50 /opt/openwrt-compiler/logs/app.log
   ```

---

🎉 **本地模式部署完成，享受无Docker依赖的OpenWrt编译体验！**
