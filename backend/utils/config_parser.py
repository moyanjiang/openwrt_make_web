"""
OpenWrt配置文件解析工具
"""

import re
import os
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path


class ConfigParser:
    """OpenWrt配置文件解析器"""
    
    def __init__(self, logger=None):
        """
        初始化配置解析器
        
        Args:
            logger: 日志记录器
        """
        self.logger = logger
        self.config_data: Dict[str, Any] = {}
        self.comments: Dict[str, str] = {}  # 存储注释
        self.order: List[str] = []  # 保持配置项顺序
    
    def _log(self, level: str, message: str):
        """记录日志"""
        if self.logger:
            getattr(self.logger, level.lower())(message)
        else:
            print(f"[{level.upper()}] {message}")
    
    def parse_config_file(self, config_path: Path) -> bool:
        """
        解析.config文件
        
        Args:
            config_path: 配置文件路径
        
        Returns:
            bool: 是否解析成功
        """
        try:
            if not config_path.exists():
                self._log("error", f"配置文件不存在: {config_path}")
                return False
            
            self._log("info", f"开始解析配置文件: {config_path}")
            
            self.config_data.clear()
            self.comments.clear()
            self.order.clear()
            
            with open(config_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            for line_num, line in enumerate(lines, 1):
                line = line.rstrip('\n\r')
                
                # 跳过空行
                if not line.strip():
                    continue
                
                # 处理注释行
                if line.startswith('#'):
                    self._parse_comment_line(line)
                    continue
                
                # 处理配置行
                if '=' in line:
                    self._parse_config_line(line, line_num)
                else:
                    self._log("warning", f"无法解析第{line_num}行: {line}")
            
            self._log("info", f"配置文件解析完成，共{len(self.config_data)}个配置项")
            return True
            
        except Exception as e:
            self._log("error", f"解析配置文件失败: {e}")
            return False
    
    def _parse_comment_line(self, line: str):
        """
        解析注释行
        
        Args:
            line: 注释行内容
        """
        # 检查是否是被注释掉的配置项
        comment_match = re.match(r'^#\s*(\w+)\s+is not set', line)
        if comment_match:
            config_key = comment_match.group(1)
            self.config_data[config_key] = False
            self.comments[config_key] = line
            self.order.append(config_key)
        else:
            # 普通注释，暂时忽略
            pass
    
    def _parse_config_line(self, line: str, line_num: int):
        """
        解析配置行
        
        Args:
            line: 配置行内容
            line_num: 行号
        """
        try:
            # 匹配配置项格式: CONFIG_KEY=value
            config_match = re.match(r'^([^=]+)=(.*)$', line)
            if not config_match:
                self._log("warning", f"第{line_num}行格式不正确: {line}")
                return
            
            key = config_match.group(1).strip()
            value = config_match.group(2).strip()
            
            # 解析值的类型
            parsed_value = self._parse_config_value(value)
            
            self.config_data[key] = parsed_value
            self.order.append(key)
            
        except Exception as e:
            self._log("error", f"解析第{line_num}行失败: {e}")
    
    def _parse_config_value(self, value: str) -> Any:
        """
        解析配置值
        
        Args:
            value: 原始值字符串
        
        Returns:
            Any: 解析后的值
        """
        # 去除首尾空格
        value = value.strip()
        
        # 布尔值 - y表示启用
        if value == 'y':
            return True
        elif value == 'n':
            return False
        
        # 字符串值 - 被双引号包围
        if value.startswith('"') and value.endswith('"'):
            return value[1:-1]  # 去除引号
        
        # 数字值
        if value.isdigit():
            return int(value)
        
        # 十六进制值
        if value.startswith('0x'):
            try:
                return int(value, 16)
            except ValueError:
                pass
        
        # 默认作为字符串处理
        return value
    
    def get_config_value(self, key: str, default=None) -> Any:
        """
        获取配置值
        
        Args:
            key: 配置键
            default: 默认值
        
        Returns:
            Any: 配置值
        """
        return self.config_data.get(key, default)
    
    def set_config_value(self, key: str, value: Any):
        """
        设置配置值
        
        Args:
            key: 配置键
            value: 配置值
        """
        self.config_data[key] = value
        
        # 如果是新键，添加到顺序列表
        if key not in self.order:
            self.order.append(key)
    
    def remove_config(self, key: str) -> bool:
        """
        移除配置项
        
        Args:
            key: 配置键
        
        Returns:
            bool: 是否成功移除
        """
        if key in self.config_data:
            del self.config_data[key]
            if key in self.order:
                self.order.remove(key)
            if key in self.comments:
                del self.comments[key]
            return True
        return False
    
    def get_all_configs(self) -> Dict[str, Any]:
        """
        获取所有配置
        
        Returns:
            dict: 所有配置项
        """
        return self.config_data.copy()
    
    def get_config_keys(self) -> List[str]:
        """
        获取所有配置键
        
        Returns:
            list: 配置键列表
        """
        return list(self.order)
    
    def save_config_file(self, config_path: Path) -> bool:
        """
        保存配置文件
        
        Args:
            config_path: 配置文件路径
        
        Returns:
            bool: 是否保存成功
        """
        try:
            self._log("info", f"保存配置文件: {config_path}")
            
            # 创建父目录
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_path, 'w', encoding='utf-8') as f:
                # 写入文件头注释
                f.write("#\n")
                f.write("# Automatically generated file; DO NOT EDIT.\n")
                f.write("# OpenWrt Configuration\n")
                f.write("#\n\n")
                
                # 按顺序写入配置项
                for key in self.order:
                    value = self.config_data[key]
                    
                    if value is False:
                        # 被禁用的配置项
                        f.write(f"# {key} is not set\n")
                    else:
                        # 启用的配置项
                        formatted_value = self._format_config_value(value)
                        f.write(f"{key}={formatted_value}\n")
            
            self._log("info", "配置文件保存成功")
            return True
            
        except Exception as e:
            self._log("error", f"保存配置文件失败: {e}")
            return False
    
    def _format_config_value(self, value: Any) -> str:
        """
        格式化配置值
        
        Args:
            value: 配置值
        
        Returns:
            str: 格式化后的字符串
        """
        if value is True:
            return 'y'
        elif value is False:
            return 'n'
        elif isinstance(value, str):
            # 如果包含空格或特殊字符，需要加引号
            if ' ' in value or any(c in value for c in ['#', '=', '\n', '\r']):
                return f'"{value}"'
            return value
        elif isinstance(value, int):
            return str(value)
        else:
            return str(value)
