# OpenWrt编译器 - 快速开始指南

## 🚀 一键安装

### 方法一：在线安装（推荐）

```bash
curl -fsSL https://raw.githubusercontent.com/moyanjiang/openwrt_make_web/main/install.sh | bash
```

### 方法二：下载后安装

```bash
# 下载安装脚本
wget https://raw.githubusercontent.com/moyanjiang/openwrt_make_web/main/install.sh
chmod +x install.sh

# 运行安装
./install.sh
```

### 方法三：自定义端口安装

```bash
# 使用端口8080
./install.sh -p 8080

# 安装到指定目录
./install.sh -d /home/openwrt -p 8080
```

## 📋 安装要求

- **系统**: Linux (Ubuntu/Debian/CentOS)
- **内存**: 4GB+
- **磁盘**: 50GB+
- **网络**: 稳定互联网连接

## 🎯 使用步骤

### 1. 安装完成后访问

```
http://your-server-ip:9963
```

### 2. 注册用户

- 首次访问注册账号
- 第一个用户自动成为管理员

### 3. 开始编译

1. 选择设备型号
2. 选择软件包
3. 点击开始编译
4. 等待完成并下载

## 🔧 常用命令

```bash
# 查看状态
cd /opt/openwrt-compiler && docker-compose ps

# 重启服务
cd /opt/openwrt-compiler && docker-compose restart

# 查看日志
cd /opt/openwrt-compiler && docker-compose logs -f

# 停止服务
cd /opt/openwrt-compiler && docker-compose down

# 启动服务
cd /opt/openwrt-compiler && docker-compose up -d
```

## ⚙️ 邮箱配置（可选）

编辑 `/opt/openwrt-compiler/.env` 文件：

```bash
# Gmail配置
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# QQ邮箱配置
MAIL_SERVER=smtp.qq.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-qq@qq.com
MAIL_PASSWORD=your-authorization-code
```

配置后重启服务：
```bash
cd /opt/openwrt-compiler && docker-compose restart
```

## 🔍 故障排除

### 端口被占用
```bash
# 检查端口
netstat -tulpn | grep :9963

# 使用其他端口
./install.sh -p 8080
```

### Docker权限问题
```bash
sudo usermod -aG docker $USER
newgrp docker
```

### 内存不足
```bash
# 检查资源
free -h
df -h

# 清理Docker
docker system prune -f
```

## 📞 获取帮助

- 查看完整文档: [README.md](README.md)
- 提交问题: [GitHub Issues](https://github.com/moyanjiang/openwrt_make_web/issues)
- 安装脚本帮助: `./install.sh --help`

---

**🎯 简单三步，开始编译！**
