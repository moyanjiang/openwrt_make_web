#!/usr/bin/env python3
"""
OpenWrt Compiler Setup Script for Debian Systems
专为Debian系统优化的OpenWrt编译器安装脚本
"""

import os
import sys
import subprocess
import platform
import json
import getpass
import hashlib
from pathlib import Path

def run_command(cmd, cwd=None, check=True):
    """执行命令并返回结果"""
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd,
                              capture_output=True, text=True, check=check)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return False, "", e.stderr

def check_debian_system():
    """检查是否为Debian系统"""
    try:
        with open('/etc/os-release', 'r') as f:
            content = f.read()
            if 'debian' in content.lower() or 'ubuntu' in content.lower():
                print("✅ 检测到Debian/Ubuntu系统")
                return True
            else:
                print("❌ 此脚本专为Debian/Ubuntu系统设计")
                return False
    except FileNotFoundError:
        print("❌ 无法检测系统类型，请确保在Debian/Ubuntu系统上运行")
        return False

def check_root_privileges():
    """检查是否有root权限（用于安装系统依赖）"""
    if os.geteuid() == 0:
        return True

    # 检查sudo权限
    success, _, _ = run_command("sudo -n true", check=False)
    return success

def install_debian_dependencies():
    """安装Debian系统依赖"""
    print("📦 安装Debian系统依赖...")

    # 基础编译依赖
    debian_packages = [
        "build-essential", "libncurses5-dev", "libncursesw5-dev",
        "zlib1g-dev", "gawk", "git", "gettext", "libssl-dev",
        "xsltproc", "rsync", "wget", "unzip", "python3", "python3-pip",
        "python3-venv", "python3-dev", "subversion", "mercurial",
        "bzr", "ecj", "fastjar", "file", "g++", "java-propose-classpath",
        "libelf-dev", "libncurses5-dev", "libncursesw5-dev", "libssl-dev",
        "python3-distutils", "python3-setuptools", "python3-dev",
        "rsync", "unzip", "zlib1g-dev", "swig", "aria2", "libtinfo5",
        "libgmp3-dev", "libmpc-dev", "libmpfr-dev", "libgmp-dev",
        "libusb-1.0-0-dev", "libusb-dev", "zlib1g-dev", "liblzma-dev",
        "libsnmp-dev", "libevent-dev", "libavahi-client-dev",
        "libsqlite3-dev", "libpcre2-dev"
    ]

    # 更新包列表
    print("🔄 更新包列表...")
    success, _, error = run_command("sudo apt update")
    if not success:
        print(f"❌ 更新包列表失败: {error}")
        return False

    # 安装依赖包
    packages_str = " ".join(debian_packages)
    success, _, error = run_command(f"sudo apt install -y {packages_str}")
    if not success:
        print(f"❌ 安装系统依赖失败: {error}")
        return False

    print("✅ Debian系统依赖安装完成")
    return True

def create_user_management():
    """创建用户管理系统"""
    print("👤 设置用户管理系统...")

    users_dir = Path("workspace/users")
    users_dir.mkdir(parents=True, exist_ok=True)

    # 创建用户配置文件
    users_config = {
        "users": {},
        "default_settings": {
            "git_url": "https://github.com/coolsnowwolf/lede.git",
            "git_branch": "master",
            "enable_istore": True,
            "compile_threads": "auto",
            "enable_ccache": True
        }
    }

    users_config_file = users_dir / "users.json"
    if not users_config_file.exists():
        with open(users_config_file, 'w', encoding='utf-8') as f:
            json.dump(users_config, f, indent=2, ensure_ascii=False)

    print("✅ 用户管理系统创建完成")
    return True

def create_user_workspace(username):
    """为用户创建独立的工作空间"""
    user_dir = Path(f"workspace/users/{username}")
    user_dir.mkdir(parents=True, exist_ok=True)

    # 创建用户子目录
    subdirs = ["lede", "configs", "firmware", "output", "temp", "uploads"]
    for subdir in subdirs:
        (user_dir / subdir).mkdir(exist_ok=True)

    # 创建用户配置文件
    user_config = {
        "username": username,
        "created_at": str(Path().ctime()),
        "git_url": "https://github.com/coolsnowwolf/lede.git",
        "git_branch": "master",
        "enable_istore": True,
        "compile_settings": {
            "threads": "auto",
            "enable_ccache": True,
            "clean_build": False
        },
        "device_configs": {},
        "build_history": []
    }

    config_file = user_dir / "config.json"
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(user_config, f, indent=2, ensure_ascii=False)

    return user_dir

def check_python_version():
    """检查Python版本"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ 是必需的")
        print(f"当前版本: {version.major}.{version.minor}.{version.micro}")
        return False
    print(f"✅ Python版本检查通过: {version.major}.{version.minor}.{version.micro}")
    return True

def check_git():
    """检查Git是否安装"""
    success, output = run_command("git --version")
    if success:
        print(f"✅ Git检查通过: {output.strip()}")
        return True
    else:
        print("❌ Git未安装或不在PATH中")
        return False

def create_virtual_environment():
    """创建Python虚拟环境"""
    venv_path = "venv"
    
    if os.path.exists(venv_path):
        print("📁 虚拟环境已存在，跳过创建")
        return True
    
    print("🔧 创建Python虚拟环境...")
    success, output = run_command(f"{sys.executable} -m venv {venv_path}")
    
    if success:
        print("✅ 虚拟环境创建成功")
        return True
    else:
        print(f"❌ 虚拟环境创建失败: {output}")
        return False

def install_dependencies():
    """安装Python依赖"""
    print("📦 安装Python依赖包...")
    
    # 确定pip路径
    if platform.system() == "Windows":
        pip_path = os.path.join("venv", "Scripts", "pip")
    else:
        pip_path = os.path.join("venv", "bin", "pip")
    
    success, output = run_command(f"{pip_path} install -r requirements.txt")
    
    if success:
        print("✅ 依赖包安装成功")
        return True
    else:
        print(f"❌ 依赖包安装失败: {output}")
        return False

def create_directories():
    """创建必要的目录"""
    directories = [
        "backend/utils",
        "backend/templates",
        "backend/config_templates",
        "workspace/users",
        "workspace/shared",
        "workspace/shared/cache",
        "workspace/shared/downloads",
        "logs",
        "docs"
    ]

    print("📁 创建项目目录...")
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

    print("✅ 项目目录创建完成")
    return True

def create_device_database():
    """创建设备数据库"""
    print("📱 创建设备数据库...")

    device_db = {
        "categories": {
            "x86": {
                "name": "x86架构",
                "description": "通用x86架构设备",
                "devices": {
                    "x86_64": {
                        "name": "x86_64通用",
                        "target": "x86/64",
                        "cpu": "x86_64",
                        "keywords": ["x86", "64位", "通用", "虚拟机", "物理机"]
                    },
                    "x86_generic": {
                        "name": "x86通用32位",
                        "target": "x86/generic",
                        "cpu": "i386",
                        "keywords": ["x86", "32位", "通用", "老旧设备"]
                    }
                }
            },
            "arm": {
                "name": "ARM架构",
                "description": "ARM架构设备",
                "devices": {
                    "raspberry_pi_4": {
                        "name": "树莓派4B",
                        "target": "bcm27xx/bcm2711",
                        "cpu": "ARM Cortex-A72",
                        "keywords": ["树莓派", "raspberry", "pi", "4b", "bcm2711"]
                    },
                    "raspberry_pi_3": {
                        "name": "树莓派3B/3B+",
                        "target": "bcm27xx/bcm2710",
                        "cpu": "ARM Cortex-A53",
                        "keywords": ["树莓派", "raspberry", "pi", "3b", "bcm2710"]
                    }
                }
            },
            "mips": {
                "name": "MIPS架构",
                "description": "MIPS架构路由器",
                "devices": {
                    "xiaomi_r3g": {
                        "name": "小米路由器3G",
                        "target": "ramips/mt7621",
                        "cpu": "MT7621A",
                        "keywords": ["小米", "xiaomi", "r3g", "mt7621"]
                    },
                    "newifi_d2": {
                        "name": "新路由3 D2",
                        "target": "ramips/mt7621",
                        "cpu": "MT7621A",
                        "keywords": ["新路由", "newifi", "d2", "mt7621"]
                    }
                }
            }
        }
    }

    device_db_file = Path("backend/config_templates/device_database.json")
    device_db_file.parent.mkdir(parents=True, exist_ok=True)

    with open(device_db_file, 'w', encoding='utf-8') as f:
        json.dump(device_db, f, indent=2, ensure_ascii=False)

    print("✅ 设备数据库创建完成")
    return True

def create_systemd_service():
    """创建systemd服务文件"""
    print("🔧 创建systemd服务...")

    service_content = """[Unit]
Description=OpenWrt Compiler Backend Service
After=network.target

[Service]
Type=simple
User=openwrt
Group=openwrt
WorkingDirectory=/opt/openwrt-compiler
Environment=PATH=/opt/openwrt-compiler/venv/bin
ExecStart=/opt/openwrt-compiler/venv/bin/python backend/app.py --host 0.0.0.0 --port 5000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""

    service_file = Path("/etc/systemd/system/openwrt-compiler.service")
    try:
        with open(service_file, 'w') as f:
            f.write(service_content)

        # 重新加载systemd配置
        run_command("sudo systemctl daemon-reload")
        run_command("sudo systemctl enable openwrt-compiler")

        print("✅ systemd服务创建完成")
        return True
    except PermissionError:
        print("⚠️  需要root权限创建systemd服务")
        return False
    except Exception as e:
        print(f"❌ 创建systemd服务失败: {e}")
        return False

def print_next_steps():
    """打印后续步骤"""
    print("\n🎉 Debian版OpenWrt编译器环境设置完成！")
    print("\n📋 后续步骤:")

    print("1. 激活虚拟环境:")
    print("   source venv/bin/activate")

    print("\n2. 启动后端服务:")
    print("   cd backend")
    print("   python app.py --host 0.0.0.0 --port 5000")
    print("   或使用systemd服务: sudo systemctl start openwrt-compiler")

    print("\n3. 打开前端界面:")
    print("   浏览器访问: http://localhost:5000")
    print("   或双击 frontend/index.html 文件")

    print("\n4. 创建用户账户:")
    print("   首次访问时会提示创建管理员账户")

    print("\n🔧 新功能特性:")
    print("   ✅ 多用户支持，每用户独立编译环境")
    print("   ✅ 设备搜索功能，支持CPU/型号搜索")
    print("   ✅ Web版menuconfig配置界面")
    print("   ✅ 自动集成iStore商店")
    print("   ✅ 优化的软件包选择界面")
    print("   ✅ 完整的Debian系统集成")

    print("\n🚀 生产环境部署:")
    print("   sudo systemctl start openwrt-compiler")
    print("   sudo systemctl status openwrt-compiler")

    print("\n📖 更多信息请查看 README.md")

def main():
    """主函数"""
    print("🚀 OpenWrt编译器Debian版环境设置")
    print("=" * 50)

    # 检查系统要求
    if not check_debian_system():
        sys.exit(1)

    if not check_python_version():
        sys.exit(1)

    if not check_git():
        sys.exit(1)

    # 检查并安装系统依赖
    if not check_root_privileges():
        print("⚠️  需要sudo权限来安装系统依赖")
        print("请运行: sudo python3 setup.py")
        sys.exit(1)

    if not install_debian_dependencies():
        sys.exit(1)

    # 创建目录结构
    if not create_directories():
        sys.exit(1)

    # 创建设备数据库
    if not create_device_database():
        sys.exit(1)

    # 创建用户管理系统
    if not create_user_management():
        sys.exit(1)

    # 创建虚拟环境
    if not create_virtual_environment():
        sys.exit(1)

    # 安装依赖
    if not install_dependencies():
        sys.exit(1)

    # 创建systemd服务（可选）
    create_systemd_service()

    # 打印后续步骤
    print_next_steps()

if __name__ == "__main__":
    main()
