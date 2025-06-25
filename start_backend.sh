#!/bin/bash
# OpenWrt编译器后端启动脚本 (Linux/macOS)

echo "🚀 OpenWrt编译器 - 启动后端服务"
echo "================================"
echo

# 检查虚拟环境
if [ ! -f "venv/bin/python" ]; then
    echo "❌ 虚拟环境未找到！"
    echo "请先运行 install_deps.sh 安装依赖"
    echo
    exit 1
fi

# 检查后端应用文件
if [ ! -f "backend/app.py" ]; then
    echo "❌ 后端应用文件未找到！"
    echo "请确保项目结构完整"
    echo
    exit 1
fi

echo "📡 正在启动Flask后端服务..."
echo "🌐 服务地址: http://localhost:5000"
echo "📝 按 Ctrl+C 停止服务"
echo

# 激活虚拟环境并启动服务
source venv/bin/activate
cd backend
python app.py

echo
echo "🛑 后端服务已停止"
