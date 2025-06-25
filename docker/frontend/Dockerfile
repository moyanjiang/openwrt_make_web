# OpenWrt编译器前端Dockerfile
FROM nginx:1.25-alpine

# 设置环境变量
ENV NGINX_PORT=9963

# 安装必要工具
RUN apk add --no-cache \
    python3 \
    py3-pip \
    curl

# 创建应用目录
WORKDIR /app

# 复制前端文件
COPY frontend/ ./frontend/

# 复制Nginx配置
COPY docker/frontend/nginx.conf /etc/nginx/nginx.conf
COPY docker/frontend/default.conf /etc/nginx/conf.d/default.conf

# 设置权限
RUN chown -R nginx:nginx /app/frontend && \
    chmod +x /app/frontend/server.py

# 创建启动脚本
RUN cat > /app/start.sh << 'EOF'
#!/bin/sh
echo "🚀 启动OpenWrt编译器前端服务"
echo "📍 Nginx端口: $NGINX_PORT"
echo "🔗 访问地址: http://localhost:$NGINX_PORT"

# 替换Nginx配置中的端口
sed -i "s/listen 9963/listen $NGINX_PORT/g" /etc/nginx/conf.d/default.conf

# 启动Nginx
exec nginx -g 'daemon off;'
EOF

RUN chmod +x /app/start.sh

# 暴露端口
EXPOSE 9963

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:9963/ || exit 1

# 启动命令
CMD ["/app/start.sh"]
