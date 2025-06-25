# OpenWrt 编译器故障排除指南

本文档提供了常见问题的诊断和解决方案，帮助用户快速解决使用过程中遇到的问题。

## 🔍 问题诊断流程

### 1. 基础检查
```bash
# 检查系统状态
curl http://localhost:5000/api/health

# 检查服务进程
ps aux | grep python
ps aux | grep nginx

# 检查端口占用
netstat -tlnp | grep :5000
lsof -i :5000

# 检查磁盘空间
df -h
du -sh workspace/
```

### 2. 日志分析
```bash
# 查看应用日志
tail -f logs/app.log
grep ERROR logs/app.log

# 查看系统日志
sudo journalctl -u openwrt-compiler -f
sudo journalctl -u nginx -f

# 查看编译日志
tail -f workspace/logs/compile.log
```

### 3. 网络诊断
```bash
# 测试API连接
curl -v http://localhost:5000/api/status

# 测试WebSocket连接
wscat -c ws://localhost:5000/socket.io/?transport=websocket

# 检查防火墙
sudo ufw status
sudo iptables -L
```

## 🚨 常见问题及解决方案

### 1. 服务启动问题

#### 问题：服务无法启动
**症状**：
- 运行`python app.py`后立即退出
- 浏览器无法访问界面
- 端口5000无响应

**可能原因**：
- 端口被占用
- Python依赖缺失
- 配置文件错误
- 权限不足

**解决方案**：
```bash
# 1. 检查端口占用
sudo lsof -i :5000
# 如果有进程占用，杀死进程
sudo kill -9 <PID>

# 2. 检查Python依赖
pip list
pip install -r requirements.txt

# 3. 检查配置文件
cat .env
# 确保配置文件格式正确

# 4. 检查权限
ls -la workspace/
sudo chown -R $USER:$USER workspace/

# 5. 使用详细模式启动
python app.py --debug --verbose
```

#### 问题：虚拟环境问题
**症状**：
- 提示模块未找到
- Python版本不匹配

**解决方案**：
```bash
# 重新创建虚拟环境
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. 前端界面问题

#### 问题：页面无法加载
**症状**：
- 双击HTML文件无反应
- 页面显示空白
- 控制台报错

**解决方案**：
```bash
# 1. 检查文件路径
ls -la frontend/index.html

# 2. 使用HTTP服务器
cd frontend
python -m http.server 8080
# 然后访问 http://localhost:8080

# 3. 检查浏览器控制台
# 按F12打开开发者工具，查看Console和Network标签页
```

#### 问题：WebSocket连接失败
**症状**：
- 界面显示"连接断开"
- 实时日志不更新
- 编译进度不显示

**解决方案**：
```bash
# 1. 检查后端服务
curl http://localhost:5000/api/status

# 2. 检查WebSocket端点
curl -v http://localhost:5000/socket.io/

# 3. 检查防火墙设置
sudo ufw allow 5000

# 4. 修改前端配置
# 编辑 frontend/assets/js/app.js
# 确保 wsUrl 配置正确
```

### 3. 编译相关问题

#### 问题：Git克隆失败
**症状**：
- 克隆按钮无响应
- 提示网络错误
- Git仓库地址无效

**解决方案**：
```bash
# 1. 检查网络连接
ping github.com
curl -I https://github.com/coolsnowwolf/lede.git

# 2. 检查Git配置
git --version
git config --list

# 3. 手动克隆测试
cd workspace
git clone https://github.com/coolsnowwolf/lede.git

# 4. 配置Git代理（如需要）
git config --global http.proxy http://proxy.example.com:8080
git config --global https.proxy https://proxy.example.com:8080
```

#### 问题：编译失败
**症状**：
- 编译过程中断
- 提示依赖缺失
- 磁盘空间不足

**解决方案**：
```bash
# 1. 检查磁盘空间
df -h
# 确保至少有50GB可用空间

# 2. 检查编译依赖
sudo apt update
sudo apt install -y build-essential libncurses5-dev libncursesw5-dev \
  zlib1g-dev gawk git gettext libssl-dev xsltproc rsync wget unzip

# 3. 清理编译环境
cd workspace/lede
make clean
make dirclean

# 4. 检查配置文件
ls -la .config
# 确保配置文件存在且有效

# 5. 手动编译测试
make menuconfig
make V=s
```

#### 问题：Feeds更新失败
**症状**：
- Feeds更新卡住
- 提示网络超时
- 软件包列表为空

**解决方案**：
```bash
# 1. 手动更新Feeds
cd workspace/lede
./scripts/feeds update -a
./scripts/feeds install -a

# 2. 检查feeds.conf
cat feeds.conf.default
# 确保源地址可访问

# 3. 使用国内镜像
# 编辑 feeds.conf.default
sed -i 's|https://github.com|https://gitee.com|g' feeds.conf.default
```

### 4. 文件管理问题

#### 问题：文件上传失败
**症状**：
- 上传按钮无响应
- 提示文件过大
- 上传进度卡住

**解决方案**：
```bash
# 1. 检查文件大小限制
# 编辑 backend/config.py
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

# 2. 检查上传目录权限
ls -la workspace/uploads/
sudo chown -R $USER:$USER workspace/uploads/

# 3. 检查Nginx配置（如使用）
# 在nginx.conf中添加
client_max_body_size 100M;

# 4. 清理临时文件
rm -rf workspace/uploads/*
```

#### 问题：固件下载失败
**症状**：
- 下载链接无效
- 文件损坏
- 下载中断

**解决方案**：
```bash
# 1. 检查固件文件
ls -la workspace/firmware/
md5sum workspace/firmware/*.img

# 2. 检查文件权限
chmod 644 workspace/firmware/*

# 3. 验证文件完整性
# 使用API验证
curl -X POST http://localhost:5000/api/files/firmware/filename/validate \
  -H "Content-Type: application/json" \
  -d '{"md5": "expected_md5_hash"}'
```

### 5. 性能问题

#### 问题：编译速度慢
**症状**：
- 编译时间过长
- CPU使用率低
- 内存不足

**解决方案**：
```bash
# 1. 调整编译线程数
# 编辑编译选项，设置线程数为CPU核心数
nproc  # 查看CPU核心数

# 2. 启用编译缓存
export USE_CCACHE=1
export CCACHE_DIR=~/.ccache
ccache -M 50G  # 设置缓存大小

# 3. 增加内存
# 检查内存使用
free -h
# 如果内存不足，考虑增加swap
sudo fallocate -l 8G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 4. 使用SSD存储
# 将workspace目录移动到SSD
```

#### 问题：界面响应慢
**症状**：
- 页面加载缓慢
- 操作延迟
- WebSocket消息延迟

**解决方案**：
```bash
# 1. 检查网络延迟
ping localhost
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:5000/api/status

# 2. 优化前端资源
# 压缩CSS/JS文件
# 启用浏览器缓存

# 3. 调整后端配置
# 增加worker进程数
# 使用Gunicorn
gunicorn -w 4 -k eventlet backend.app:app

# 4. 使用反向代理
# 配置Nginx缓存静态资源
```

## 🔧 调试工具

### 1. 后端调试
```python
# 启用调试模式
import logging
logging.basicConfig(level=logging.DEBUG)

# 使用pdb调试
import pdb; pdb.set_trace()

# 性能分析
import cProfile
profiler = cProfile.Profile()
profiler.enable()
# ... 代码 ...
profiler.disable()
profiler.print_stats()
```

### 2. 前端调试
```javascript
// 启用详细日志
localStorage.setItem('debug', 'true');

// 监控API调用
const originalFetch = window.fetch;
window.fetch = function(...args) {
    console.log('API调用:', args);
    return originalFetch.apply(this, args);
};

// WebSocket调试
socket.on('connect', () => console.log('WebSocket已连接'));
socket.on('disconnect', () => console.log('WebSocket已断开'));
socket.on('error', (error) => console.error('WebSocket错误:', error));
```

### 3. 系统监控
```bash
# 实时监控脚本
#!/bin/bash
while true; do
    echo "=== $(date) ==="
    echo "CPU使用率:"
    top -bn1 | grep "Cpu(s)"
    echo "内存使用:"
    free -h
    echo "磁盘使用:"
    df -h | grep -E "(/$|/workspace)"
    echo "网络连接:"
    netstat -an | grep :5000
    echo "进程状态:"
    ps aux | grep python | grep -v grep
    echo "===================="
    sleep 30
done
```

## 📞 获取帮助

### 1. 日志收集
在报告问题时，请提供以下信息：
```bash
# 系统信息
uname -a
python --version
pip list

# 应用日志
tail -100 logs/app.log

# 系统日志
sudo journalctl -u openwrt-compiler --since "1 hour ago"

# 配置信息
cat .env (隐藏敏感信息)
```

### 2. 问题报告模板
```markdown
## 问题描述
简要描述遇到的问题

## 复现步骤
1. 第一步
2. 第二步
3. 第三步

## 预期行为
描述期望的正确行为

## 实际行为
描述实际发生的情况

## 环境信息
- 操作系统: 
- Python版本: 
- 浏览器版本: 
- 应用版本: 

## 日志信息
```
相关的错误日志
```

## 其他信息
任何其他相关信息
```

### 3. 联系方式
- **GitHub Issues**: [提交问题](https://github.com/your-repo/issues)
- **GitHub Discussions**: [讨论交流](https://github.com/your-repo/discussions)
- **邮箱**: support@example.com
- **QQ群**: 123456789

---

**如果以上方案都无法解决问题，请提供详细的错误信息和日志，我们会尽快协助解决。**
