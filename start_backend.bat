@echo off
chcp 65001 >nul
echo 🚀 OpenWrt编译器 - 启动后端服务
echo ================================
echo.

if not exist "venv\Scripts\python.exe" (
    echo ❌ 虚拟环境未找到！
    echo 请先运行 install_deps.bat 安装依赖
    echo.
    pause
    exit /b 1
)

if not exist "backend\app.py" (
    echo ❌ 后端应用文件未找到！
    echo 请确保项目结构完整
    echo.
    pause
    exit /b 1
)

echo 📡 正在启动Flask后端服务...
echo 🌐 服务地址: http://localhost:5000
echo 📝 按 Ctrl+C 停止服务
echo.

cd backend
..\venv\Scripts\python.exe app.py

echo.
echo 🛑 后端服务已停止
pause
