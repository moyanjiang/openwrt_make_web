#!/usr/bin/env python3
"""
测试Python环境和虚拟环境设置
"""

import sys
import os

def test_python_version():
    """测试Python版本"""
    version = sys.version_info
    print(f"Python版本: {version.major}.{version.minor}.{version.micro}")
    
    if version.major >= 3 and version.minor >= 8:
        print("✅ Python版本符合要求 (3.8+)")
        return True
    else:
        print("❌ Python版本不符合要求，需要3.8+")
        return False

def test_virtual_env():
    """测试虚拟环境"""
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ 运行在虚拟环境中")
        print(f"虚拟环境路径: {sys.prefix}")
        return True
    else:
        print("⚠️  未在虚拟环境中运行")
        return False

def test_project_structure():
    """测试项目结构"""
    required_dirs = [
        'backend',
        'frontend',
        'workspace',
        'workspace/lede',
        'workspace/configs',
        'workspace/output',
        'docs'
    ]
    
    required_files = [
        'requirements.txt',
        'README.md',
        '.gitignore'
    ]
    
    print("检查项目结构...")
    
    all_good = True
    
    for directory in required_dirs:
        if os.path.exists(directory):
            print(f"✅ 目录存在: {directory}")
        else:
            print(f"❌ 目录缺失: {directory}")
            all_good = False
    
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ 文件存在: {file}")
        else:
            print(f"❌ 文件缺失: {file}")
            all_good = False
    
    return all_good

def main():
    """主函数"""
    print("🧪 OpenWrt编译器环境测试")
    print("=" * 40)
    
    python_ok = test_python_version()
    venv_ok = test_virtual_env()
    structure_ok = test_project_structure()
    
    print("\n📊 测试结果:")
    print(f"Python版本: {'✅' if python_ok else '❌'}")
    print(f"虚拟环境: {'✅' if venv_ok else '⚠️'}")
    print(f"项目结构: {'✅' if structure_ok else '❌'}")
    
    if python_ok and structure_ok:
        print("\n🎉 环境设置基本完成！")
        if not venv_ok:
            print("💡 建议在虚拟环境中运行以获得最佳体验")
    else:
        print("\n❌ 环境设置存在问题，请检查上述错误")

if __name__ == "__main__":
    main()
