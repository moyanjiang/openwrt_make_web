# OpenWrt编译器网页乱码和内网穿透修复指南

## 🚨 问题描述

您遇到的问题：
- **网页显示乱码** - 中文字符无法正常显示
- **内网穿透报错** - http://openwrt.xdaidai.com 访问异常

## 🔧 问题原因分析

### 1. 字符编码问题
- Docker容器内缺少中文locale支持
- HTML文件缺少UTF-8编码声明
- Nginx代理未正确处理字符编码
- Python应用未设置正确的编码环境

### 2. 内网穿透问题
- 代理配置不正确
- 服务端口映射错误
- 健康检查失败
- 网络连接超时

## 🛠️ 修复方案

### 方案一：使用修复脚本（推荐）

#### 1. 运行修复脚本
```bash
# 运行完整修复脚本
./fix-encoding-and-proxy.sh

# 或者直接启动修复版
./start-fixed.sh
```

#### 2. 验证修复结果
```bash
# 检查服务状态
docker-compose -f docker-compose.fixed.yml ps

# 测试编码
curl http://localhost/test-encoding

# 检查健康状态
curl http://localhost/health
```

### 方案二：手动修复

#### 1. 修复字符编码

**设置环境变量：**
```bash
export LANG=zh_CN.UTF-8
export LC_ALL=zh_CN.UTF-8
export PYTHONIOENCODING=utf-8
```

**更新Docker配置：**
```yaml
# 在docker-compose.yml中添加
environment:
  - LANG=zh_CN.UTF-8
  - LC_ALL=zh_CN.UTF-8
  - PYTHONIOENCODING=utf-8
```

**修复HTML文件：**
```html
<!-- 在HTML文件<head>中添加 -->
<meta charset="UTF-8">
```

#### 2. 修复内网穿透

**检查端口映射：**
```bash
# 确保端口正确映射
docker ps | grep openwrt
netstat -tlnp | grep :80
```

**更新Nginx配置：**
```nginx
# 添加字符编码支持
charset utf-8;
proxy_set_header Accept-Charset "utf-8";
```

## 📋 修复文件说明

### 新增修复文件

1. **fix-encoding-and-proxy.sh** - 完整修复脚本
2. **start-fixed.sh** - 修复版启动脚本
3. **Dockerfile.fixed** - 修复版Docker镜像
4. **docker-compose.fixed.yml** - 修复版服务编排
5. **config/nginx-fixed.conf** - 修复版Nginx配置
6. **config/redis-fixed.conf** - 修复版Redis配置

### 修复内容

#### Dockerfile.fixed 修复点：
- ✅ 安装中文locale支持
- ✅ 设置UTF-8环境变量
- ✅ 安装中文字体
- ✅ 创建编码修复的启动脚本

#### nginx-fixed.conf 修复点：
- ✅ 设置charset utf-8
- ✅ 添加编码相关HTTP头
- ✅ 优化代理配置
- ✅ 支持内网穿透

#### docker-compose.fixed.yml 修复点：
- ✅ 完整的环境变量配置
- ✅ 正确的端口映射
- ✅ 健康检查配置
- ✅ 网络隔离

## 🚀 快速修复步骤

### 步骤1：停止现有服务
```bash
docker-compose down
docker rm -f $(docker ps -aq --filter "name=openwrt")
```

### 步骤2：运行修复版
```bash
# 方法1：使用修复脚本
./start-fixed.sh

# 方法2：手动启动
docker-compose -f docker-compose.fixed.yml up -d
```

### 步骤3：验证修复
```bash
# 检查服务状态
docker-compose -f docker-compose.fixed.yml ps

# 测试本地访问
curl http://localhost/health

# 测试编码
curl http://localhost/test-encoding
```

### 步骤4：配置内网穿透
确保您的内网穿透工具（如frp）配置正确：

```ini
# frp客户端配置示例
[web]
type = http
local_ip = 127.0.0.1
local_port = 80
custom_domains = openwrt.xdaidai.com
```

## 🔍 故障排除

### 问题1：容器启动失败
```bash
# 查看详细日志
docker-compose -f docker-compose.fixed.yml logs

# 检查镜像构建
docker-compose -f docker-compose.fixed.yml build --no-cache
```

### 问题2：编码仍然乱码
```bash
# 检查容器内编码
docker exec -it openwrt-compiler-fixed locale

# 检查Python编码
docker exec -it openwrt-compiler-fixed python3 -c "import sys; print(sys.getdefaultencoding())"
```

### 问题3：内网穿透无法访问
```bash
# 检查端口监听
netstat -tlnp | grep :80

# 检查防火墙
sudo ufw status

# 测试本地连接
curl -I http://localhost
```

### 问题4：服务健康检查失败
```bash
# 手动测试健康检查
curl http://localhost:5000/api/health

# 查看应用日志
docker logs openwrt-compiler-fixed
```

## 📊 验证清单

修复完成后，请验证以下项目：

- [ ] 容器正常启动
- [ ] 端口80和5000正常监听
- [ ] 健康检查返回正常
- [ ] 中文字符显示正常
- [ ] 内网穿透域名可访问
- [ ] API接口响应正常

## 🌐 访问地址

修复完成后的访问地址：

- **本地访问**: http://localhost
- **内网穿透**: http://openwrt.xdaidai.com
- **编码测试**: http://localhost/test-encoding
- **健康检查**: http://localhost/health
- **API状态**: http://localhost/api/status

## 📞 技术支持

如果修复后仍有问题，请提供以下信息：

1. **系统信息**:
   ```bash
   uname -a
   docker --version
   docker-compose --version
   ```

2. **服务状态**:
   ```bash
   docker-compose -f docker-compose.fixed.yml ps
   docker logs openwrt-compiler-fixed
   ```

3. **网络状态**:
   ```bash
   netstat -tlnp | grep -E ":(80|5000|443)"
   curl -I http://localhost/health
   ```

4. **错误日志**:
   ```bash
   docker-compose -f docker-compose.fixed.yml logs --tail=50
   ```

## ✨ 修复完成

按照以上步骤操作后，您的OpenWrt编译器应该能够：
- ✅ 正确显示中文字符
- ✅ 通过内网穿透正常访问
- ✅ 提供稳定的编译服务

如有其他问题，请参考项目文档或提交Issue。
