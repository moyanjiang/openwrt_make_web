#!/bin/bash

# 获取端口配置
PORT=${PORT:-9963}

echo "🚀 启动OpenWrt编译器"
echo "📍 服务端口: $PORT"
echo "🌐 访问地址: http://localhost:$PORT"

# 更新Nginx配置中的端口
sed "s/PORT_PLACEHOLDER/$PORT/g" /etc/nginx/sites-available/openwrt-compiler > /etc/nginx/sites-enabled/default

# 删除默认Nginx配置
rm -f /etc/nginx/sites-enabled/default.nginx-debian

# 测试Nginx配置
nginx -t

# 创建必要目录并设置权限
mkdir -p /app/workspace/users /app/logs
chown -R openwrt:openwrt /app/workspace /app/logs

echo "✅ 配置完成，启动服务..."

# 启动Supervisor
exec /usr/bin/supervisord -c /etc/supervisor/supervisord.conf
