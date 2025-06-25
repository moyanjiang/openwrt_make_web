@echo off
chcp 65001 >nul
echo 🚀 OpenWrt编译器 - 安装Python依赖
echo =====================================
echo.

echo 📦 正在安装Python依赖包...
venv\Scripts\pip.exe install -r requirements.txt

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ 依赖包安装成功！
    echo.
    echo 📋 下一步操作:
    echo    1. 双击 start_backend.bat 启动后端服务
    echo    2. 双击 frontend\index.html 打开前端界面
    echo.
) else (
    echo.
    echo ❌ 依赖包安装失败！
    echo 请检查网络连接或Python环境配置
    echo.
)

pause
