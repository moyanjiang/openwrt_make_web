"""
设备管理模块
支持设备搜索、配置管理等功能
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from utils.logger import setup_logger


@dataclass
class DeviceInfo:
    """设备信息"""
    id: str
    name: str
    target: str
    cpu: str
    category: str
    keywords: List[str]
    description: str = ""
    default_config: Dict[str, Any] = None


class DeviceManager:
    """设备管理器"""
    
    def __init__(self, config, logger=None):
        self.config = config
        self.logger = logger or setup_logger(__name__)
        self.device_db_file = Path("backend/config_templates/device_database.json")
        self.devices = {}
        self._load_device_database()
    
    def _load_device_database(self):
        """加载设备数据库"""
        try:
            with open(self.device_db_file, 'r', encoding='utf-8') as f:
                db = json.load(f)
                
            self.devices = {}
            for category_id, category in db.get("categories", {}).items():
                for device_id, device_data in category.get("devices", {}).items():
                    device = DeviceInfo(
                        id=device_id,
                        name=device_data["name"],
                        target=device_data["target"],
                        cpu=device_data["cpu"],
                        category=category_id,
                        keywords=device_data.get("keywords", []),
                        description=device_data.get("description", ""),
                        default_config=device_data.get("default_config", {})
                    )
                    self.devices[device_id] = device
                    
            self.logger.info(f"加载了 {len(self.devices)} 个设备配置")
            
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.logger.error(f"加载设备数据库失败: {e}")
            self.devices = {}
    
    def search_devices(self, query: str, limit: int = 20) -> List[DeviceInfo]:
        """搜索设备"""
        if not query:
            return list(self.devices.values())[:limit]
        
        query = query.lower().strip()
        results = []
        
        for device in self.devices.values():
            score = 0
            
            # 名称匹配
            if query in device.name.lower():
                score += 10
            
            # CPU匹配
            if query in device.cpu.lower():
                score += 8
            
            # 关键词匹配
            for keyword in device.keywords:
                if query in keyword.lower():
                    score += 5
                    break
            
            # 目标匹配
            if query in device.target.lower():
                score += 3
            
            # 描述匹配
            if query in device.description.lower():
                score += 2
            
            if score > 0:
                results.append((score, device))
        
        # 按分数排序
        results.sort(key=lambda x: x[0], reverse=True)
        return [device for _, device in results[:limit]]
    
    def get_device(self, device_id: str) -> Optional[DeviceInfo]:
        """获取设备信息"""
        return self.devices.get(device_id)
    
    def get_devices_by_category(self, category: str) -> List[DeviceInfo]:
        """按分类获取设备"""
        return [device for device in self.devices.values() 
                if device.category == category]
    
    def get_categories(self) -> Dict[str, List[DeviceInfo]]:
        """获取所有分类"""
        categories = {}
        for device in self.devices.values():
            if device.category not in categories:
                categories[device.category] = []
            categories[device.category].append(device)
        return categories
    
    def generate_device_config(self, device_id: str, 
                             enable_istore: bool = True,
                             custom_packages: List[str] = None) -> Dict[str, Any]:
        """生成设备配置"""
        device = self.get_device(device_id)
        if not device:
            raise ValueError(f"设备 {device_id} 不存在")
        
        # 基础配置
        config = {
            "CONFIG_TARGET_" + device.target.split('/')[0]: "y",
            "CONFIG_TARGET_" + device.target.replace('/', '_'): "y",
        }
        
        # 添加设备默认配置
        if device.default_config:
            config.update(device.default_config)
        
        # 基础软件包
        base_packages = [
            "luci",
            "luci-ssl",
            "luci-theme-bootstrap",
            "curl",
            "wget",
            "htop",
            "nano",
            "openssh-sftp-server"
        ]
        
        for package in base_packages:
            config[f"CONFIG_PACKAGE_{package}"] = "y"
        
        # iStore商店
        if enable_istore:
            istore_packages = [
                "luci-app-store",
                "luci-lib-taskd",
                "luci-lib-xterm",
                "taskd",
                "luci-lib-docker"
            ]
            for package in istore_packages:
                config[f"CONFIG_PACKAGE_{package}"] = "y"
        
        # 自定义软件包
        if custom_packages:
            for package in custom_packages:
                config[f"CONFIG_PACKAGE_{package}"] = "y"
        
        return config
    
    def get_package_categories(self) -> Dict[str, List[Dict[str, Any]]]:
        """获取软件包分类"""
        return {
            "drivers": {
                "name": "驱动程序",
                "description": "硬件驱动和内核模块",
                "packages": [
                    {"name": "kmod-usb-storage", "description": "USB存储设备支持"},
                    {"name": "kmod-usb2", "description": "USB 2.0支持"},
                    {"name": "kmod-usb3", "description": "USB 3.0支持"},
                    {"name": "kmod-fs-ext4", "description": "EXT4文件系统支持"},
                    {"name": "kmod-fs-ntfs", "description": "NTFS文件系统支持"},
                    {"name": "kmod-nls-cp437", "description": "代码页437支持"},
                    {"name": "kmod-nls-iso8859-1", "description": "ISO8859-1字符集支持"},
                    {"name": "kmod-nls-utf8", "description": "UTF-8字符集支持"}
                ]
            },
            "network": {
                "name": "网络功能",
                "description": "网络相关功能和协议",
                "packages": [
                    {"name": "luci-app-ddns", "description": "动态DNS"},
                    {"name": "luci-app-upnp", "description": "UPnP服务"},
                    {"name": "luci-app-wol", "description": "网络唤醒"},
                    {"name": "luci-app-nlbwmon", "description": "网络带宽监控"},
                    {"name": "luci-app-sqm", "description": "智能队列管理"},
                    {"name": "luci-app-mwan3", "description": "多WAN负载均衡"}
                ]
            },
            "vpn": {
                "name": "VPN服务",
                "description": "各种VPN协议支持",
                "packages": [
                    {"name": "luci-app-openvpn", "description": "OpenVPN"},
                    {"name": "luci-app-wireguard", "description": "WireGuard"},
                    {"name": "luci-app-zerotier", "description": "ZeroTier"},
                    {"name": "luci-app-n2n", "description": "N2N P2P VPN"},
                    {"name": "luci-app-softethervpn", "description": "SoftEther VPN"}
                ]
            },
            "storage": {
                "name": "存储服务",
                "description": "文件共享和存储服务",
                "packages": [
                    {"name": "luci-app-samba4", "description": "Samba文件共享"},
                    {"name": "luci-app-minidlna", "description": "DLNA媒体服务器"},
                    {"name": "luci-app-aria2", "description": "Aria2下载器"},
                    {"name": "luci-app-transmission", "description": "Transmission BT下载"},
                    {"name": "luci-app-hd-idle", "description": "硬盘休眠"}
                ]
            },
            "system": {
                "name": "系统工具",
                "description": "系统管理和监控工具",
                "packages": [
                    {"name": "luci-app-ttyd", "description": "Web终端"},
                    {"name": "luci-app-watchcat", "description": "网络监控重启"},
                    {"name": "luci-app-autoreboot", "description": "定时重启"},
                    {"name": "luci-app-ramfree", "description": "内存释放"},
                    {"name": "luci-app-cpufreq", "description": "CPU频率调节"}
                ]
            },
            "advanced": {
                "name": "高级功能",
                "description": "高级用户功能",
                "packages": [
                    {"name": "luci-app-docker", "description": "Docker容器"},
                    {"name": "luci-app-dockerman", "description": "Docker管理界面"},
                    {"name": "luci-app-frpc", "description": "FRP内网穿透客户端"},
                    {"name": "luci-app-frps", "description": "FRP内网穿透服务端"},
                    {"name": "luci-app-adguardhome", "description": "AdGuard Home广告拦截"}
                ]
            }
        }
    
    def validate_config(self, config: Dict[str, Any]) -> Dict[str, List[str]]:
        """验证配置"""
        errors = []
        warnings = []
        
        # 检查必需的目标配置
        target_configs = [k for k in config.keys() if k.startswith("CONFIG_TARGET_")]
        if not target_configs:
            errors.append("缺少目标平台配置")
        
        # 检查冲突的配置
        if config.get("CONFIG_PACKAGE_luci-ssl") == "y" and config.get("CONFIG_PACKAGE_luci") != "y":
            warnings.append("启用luci-ssl需要先启用luci")
        
        return {
            "errors": errors,
            "warnings": warnings
        }
