"""
Web版menuconfig配置管理器
将传统的menuconfig转换为现代化的Web界面
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict

from utils.logger import setup_logger


@dataclass
class ConfigOption:
    """配置选项"""
    name: str
    type: str  # bool, tristate, string, int, hex
    prompt: str
    help_text: str = ""
    default_value: Any = None
    depends_on: List[str] = None
    select: List[str] = None
    category: str = ""
    subcategory: str = ""


@dataclass
class ConfigCategory:
    """配置分类"""
    name: str
    title: str
    description: str = ""
    options: List[ConfigOption] = None
    subcategories: List['ConfigCategory'] = None


class WebMenuconfig:
    """Web版menuconfig管理器"""
    
    def __init__(self, config, logger=None):
        self.config = config
        self.logger = logger or setup_logger(__name__)
        self.config_options = {}
        self.categories = {}
        
    def parse_kconfig(self, lede_dir: Path) -> Dict[str, Any]:
        """解析Kconfig文件"""
        try:
            self._log("info", "开始解析Kconfig配置")
            
            # 主要的Kconfig文件
            main_kconfig = lede_dir / "Config.in"
            if not main_kconfig.exists():
                raise FileNotFoundError("找不到主Kconfig文件")
            
            # 解析配置选项
            self._parse_kconfig_file(main_kconfig, lede_dir)
            
            # 生成分类结构
            self._generate_categories()
            
            self._log("info", f"解析完成，共找到 {len(self.config_options)} 个配置选项")
            
            return {
                "success": True,
                "options_count": len(self.config_options),
                "categories": self.categories
            }
            
        except Exception as e:
            error_msg = f"解析Kconfig失败: {e}"
            self._log("error", error_msg)
            return {
                "success": False,
                "message": error_msg
            }
    
    def _parse_kconfig_file(self, kconfig_file: Path, base_dir: Path):
        """解析单个Kconfig文件"""
        try:
            with open(kconfig_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # 解析配置块
            config_blocks = re.findall(
                r'config\s+(\w+).*?(?=config\s+\w+|menuconfig\s+\w+|$)', 
                content, 
                re.DOTALL
            )
            
            for block in config_blocks:
                self._parse_config_block(block)
            
            # 解析包含的文件
            source_files = re.findall(r'source\s+"([^"]+)"', content)
            for source_file in source_files:
                source_path = base_dir / source_file
                if source_path.exists():
                    self._parse_kconfig_file(source_path, base_dir)
                    
        except Exception as e:
            self._log("warning", f"解析文件 {kconfig_file} 失败: {e}")
    
    def _parse_config_block(self, block: str):
        """解析配置块"""
        lines = block.strip().split('\n')
        if not lines:
            return
        
        # 提取配置名称
        config_match = re.match(r'config\s+(\w+)', lines[0])
        if not config_match:
            return
        
        config_name = config_match.group(1)
        
        # 解析配置属性
        option = ConfigOption(
            name=config_name,
            type="bool",  # 默认类型
            prompt="",
            depends_on=[],
            select=[]
        )
        
        for line in lines[1:]:
            line = line.strip()
            
            # 类型
            if line.startswith('bool'):
                option.type = "bool"
                if '"' in line:
                    option.prompt = re.search(r'"([^"]*)"', line).group(1)
            elif line.startswith('tristate'):
                option.type = "tristate"
                if '"' in line:
                    option.prompt = re.search(r'"([^"]*)"', line).group(1)
            elif line.startswith('string'):
                option.type = "string"
                if '"' in line:
                    option.prompt = re.search(r'"([^"]*)"', line).group(1)
            elif line.startswith('int'):
                option.type = "int"
                if '"' in line:
                    option.prompt = re.search(r'"([^"]*)"', line).group(1)
            elif line.startswith('hex'):
                option.type = "hex"
                if '"' in line:
                    option.prompt = re.search(r'"([^"]*)"', line).group(1)
            
            # 默认值
            elif line.startswith('default'):
                default_match = re.search(r'default\s+(.+)', line)
                if default_match:
                    option.default_value = default_match.group(1).strip()
            
            # 依赖
            elif line.startswith('depends on'):
                deps = re.search(r'depends on\s+(.+)', line)
                if deps:
                    option.depends_on.append(deps.group(1).strip())
            
            # 选择
            elif line.startswith('select'):
                select_match = re.search(r'select\s+(\w+)', line)
                if select_match:
                    option.select.append(select_match.group(1))
            
            # 帮助文本
            elif line.startswith('help') or line.startswith('---help---'):
                # 帮助文本通常在后续行中
                pass
        
        # 分类配置选项
        self._categorize_option(option)
        self.config_options[config_name] = option
    
    def _categorize_option(self, option: ConfigOption):
        """为配置选项分类"""
        name = option.name.upper()
        
        # 目标平台
        if name.startswith('CONFIG_TARGET_'):
            option.category = "target"
            option.subcategory = "platform"
        
        # 软件包
        elif name.startswith('CONFIG_PACKAGE_'):
            option.category = "packages"
            
            # 进一步分类软件包
            package_name = name.replace('CONFIG_PACKAGE_', '').lower()
            
            if package_name.startswith('luci-'):
                option.subcategory = "luci"
            elif package_name.startswith('kmod-'):
                option.subcategory = "drivers"
            elif 'vpn' in package_name or package_name in ['openvpn', 'wireguard', 'zerotier']:
                option.subcategory = "vpn"
            elif package_name in ['samba4', 'minidlna', 'aria2', 'transmission']:
                option.subcategory = "storage"
            elif package_name in ['ddns', 'upnp', 'wol', 'sqm']:
                option.subcategory = "network"
            else:
                option.subcategory = "other"
        
        # 内核配置
        elif name.startswith('CONFIG_KERNEL_'):
            option.category = "kernel"
        
        # 其他
        else:
            option.category = "system"
    
    def _generate_categories(self):
        """生成分类结构"""
        self.categories = {
            "target": {
                "name": "目标平台",
                "description": "选择编译目标平台和架构",
                "icon": "microchip",
                "subcategories": {
                    "platform": {
                        "name": "平台选择",
                        "options": []
                    }
                }
            },
            "packages": {
                "name": "软件包",
                "description": "选择要编译的软件包",
                "icon": "cube",
                "subcategories": {
                    "drivers": {
                        "name": "驱动程序",
                        "description": "硬件驱动和内核模块",
                        "options": []
                    },
                    "luci": {
                        "name": "LuCI界面",
                        "description": "Web管理界面组件",
                        "options": []
                    },
                    "network": {
                        "name": "网络功能",
                        "description": "网络相关功能和协议",
                        "options": []
                    },
                    "vpn": {
                        "name": "VPN服务",
                        "description": "各种VPN协议支持",
                        "options": []
                    },
                    "storage": {
                        "name": "存储服务",
                        "description": "文件共享和存储服务",
                        "options": []
                    },
                    "other": {
                        "name": "其他软件包",
                        "description": "其他功能软件包",
                        "options": []
                    }
                }
            },
            "kernel": {
                "name": "内核配置",
                "description": "Linux内核相关配置",
                "icon": "cog",
                "subcategories": {}
            },
            "system": {
                "name": "系统配置",
                "description": "系统级配置选项",
                "icon": "server",
                "subcategories": {}
            }
        }
        
        # 将配置选项分配到分类中
        for option in self.config_options.values():
            category = self.categories.get(option.category)
            if category and option.subcategory:
                subcategory = category["subcategories"].get(option.subcategory)
                if subcategory:
                    subcategory["options"].append(asdict(option))
    
    def generate_web_config(self, device_id: str = None) -> Dict[str, Any]:
        """生成Web配置界面数据"""
        try:
            # 基础配置结构
            web_config = {
                "device_selection": {
                    "title": "设备选择",
                    "description": "选择要编译的目标设备",
                    "type": "device_search",
                    "current_device": device_id
                },
                "basic_packages": {
                    "title": "基础软件包",
                    "description": "选择基础功能软件包",
                    "categories": [
                        {
                            "id": "drivers",
                            "name": "驱动程序",
                            "description": "硬件驱动支持",
                            "icon": "microchip",
                            "packages": self._get_driver_packages()
                        },
                        {
                            "id": "plugins",
                            "name": "插件库",
                            "description": "功能插件选择",
                            "icon": "puzzle-piece",
                            "packages": self._get_plugin_packages()
                        }
                    ]
                },
                "advanced_config": {
                    "title": "高级配置",
                    "description": "详细的配置选项",
                    "categories": self.categories
                }
            }
            
            return {
                "success": True,
                "config": web_config
            }
            
        except Exception as e:
            error_msg = f"生成Web配置失败: {e}"
            self._log("error", error_msg)
            return {
                "success": False,
                "message": error_msg
            }
    
    def _get_driver_packages(self) -> List[Dict[str, Any]]:
        """获取驱动程序包"""
        drivers = []
        for option in self.config_options.values():
            if (option.category == "packages" and 
                option.subcategory == "drivers" and
                option.name.startswith('CONFIG_PACKAGE_kmod-')):
                
                drivers.append({
                    "name": option.name,
                    "title": option.prompt or option.name,
                    "description": option.help_text,
                    "default": option.default_value == "y"
                })
        
        return sorted(drivers, key=lambda x: x["title"])
    
    def _get_plugin_packages(self) -> List[Dict[str, Any]]:
        """获取插件包"""
        plugins = []
        for option in self.config_options.values():
            if (option.category == "packages" and 
                option.subcategory in ["luci", "network", "vpn", "storage"] and
                option.name.startswith('CONFIG_PACKAGE_luci-app-')):
                
                plugins.append({
                    "name": option.name,
                    "title": option.prompt or option.name,
                    "description": option.help_text,
                    "category": option.subcategory,
                    "default": False
                })
        
        return sorted(plugins, key=lambda x: x["title"])
    
    def _log(self, level: str, message: str):
        """记录日志"""
        if self.logger:
            getattr(self.logger, level.lower())(message)
        else:
            print(f"[{level.upper()}] {message}")
