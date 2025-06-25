"""
OpenWrt配置文件管理器
"""

import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

from utils.config_parser import ConfigParser


class ConfigManager:
    """OpenWrt配置文件管理器"""
    
    def __init__(self, config, logger=None):
        """
        初始化配置管理器
        
        Args:
            config: 应用配置
            logger: 日志记录器
        """
        self.config = config
        self.logger = logger
        
        # 初始化路径
        self.configs_dir = Path(self.config.CONFIGS_DIR)
        self.templates_dir = Path(self.config.BASE_DIR) / "backend" / "templates"
        self.lede_dir = Path(self.config.LEDE_DIR)
        
        # 创建必要目录
        self.configs_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化配置解析器
        self.parser = ConfigParser(logger)
        
        # 缓存模板
        self._templates_cache = {}
        self._load_templates()
    
    def _log(self, level: str, message: str):
        """记录日志"""
        if self.logger:
            getattr(self.logger, level.lower())(message)
        else:
            print(f"[{level.upper()}] {message}")
    
    def _load_templates(self):
        """加载配置模板"""
        try:
            if not self.templates_dir.exists():
                self._log("warning", f"模板目录不存在: {self.templates_dir}")
                return
            
            self._log("info", "加载配置模板...")
            
            for template_file in self.templates_dir.glob("*.json"):
                try:
                    with open(template_file, 'r', encoding='utf-8') as f:
                        template_data = json.load(f)
                    
                    template_id = template_file.stem
                    self._templates_cache[template_id] = template_data
                    
                    self._log("debug", f"加载模板: {template_id}")
                    
                except Exception as e:
                    self._log("error", f"加载模板失败 {template_file}: {e}")
            
            self._log("info", f"共加载 {len(self._templates_cache)} 个配置模板")
            
        except Exception as e:
            self._log("error", f"加载模板时发生错误: {e}")
    
    def get_templates(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有配置模板
        
        Returns:
            dict: 模板字典
        """
        return {
            template_id: {
                "id": template_id,
                "name": template_data.get("name", template_id),
                "description": template_data.get("description", ""),
                "target": template_data.get("target", ""),
                "features": template_data.get("features", [])
            }
            for template_id, template_data in self._templates_cache.items()
        }
    
    def get_template_config(self, template_id: str) -> Optional[Dict[str, Any]]:
        """
        获取模板配置
        
        Args:
            template_id: 模板ID
        
        Returns:
            dict: 模板配置数据
        """
        if template_id in self._templates_cache:
            return self._templates_cache[template_id].copy()
        return None
    
    def apply_template(self, template_id: str, config_name: str = None) -> Dict[str, Any]:
        """
        应用配置模板
        
        Args:
            template_id: 模板ID
            config_name: 配置名称（可选）
        
        Returns:
            dict: 操作结果
        """
        try:
            template_data = self.get_template_config(template_id)
            if not template_data:
                return {
                    "success": False,
                    "message": f"模板不存在: {template_id}"
                }
            
            # 生成配置名称
            if not config_name:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                config_name = f"{template_id}_{timestamp}"
            
            # 创建配置解析器实例
            parser = ConfigParser(self.logger)
            
            # 设置模板配置
            template_config = template_data.get("config", {})
            for key, value in template_config.items():
                parser.set_config_value(key, value)
            
            # 保存配置文件
            config_path = self.configs_dir / f"{config_name}.config"
            success = parser.save_config_file(config_path)
            
            if success:
                # 保存元数据
                metadata = {
                    "name": config_name,
                    "template_id": template_id,
                    "template_name": template_data.get("name", template_id),
                    "description": template_data.get("description", ""),
                    "target": template_data.get("target", ""),
                    "created_time": datetime.now().isoformat(),
                    "modified_time": datetime.now().isoformat()
                }
                
                metadata_path = self.configs_dir / f"{config_name}.meta.json"
                with open(metadata_path, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, indent=2, ensure_ascii=False)
                
                self._log("info", f"配置模板应用成功: {config_name}")
                
                return {
                    "success": True,
                    "message": "配置模板应用成功",
                    "config_name": config_name,
                    "config_path": str(config_path)
                }
            else:
                return {
                    "success": False,
                    "message": "保存配置文件失败"
                }
                
        except Exception as e:
            error_msg = f"应用配置模板失败: {e}"
            self._log("error", error_msg)
            return {
                "success": False,
                "message": error_msg
            }
    
    def load_config(self, config_name: str) -> Dict[str, Any]:
        """
        加载配置文件
        
        Args:
            config_name: 配置名称
        
        Returns:
            dict: 操作结果
        """
        try:
            config_path = self.configs_dir / f"{config_name}.config"
            
            if not config_path.exists():
                return {
                    "success": False,
                    "message": f"配置文件不存在: {config_name}"
                }
            
            # 解析配置文件
            parser = ConfigParser(self.logger)
            success = parser.parse_config_file(config_path)
            
            if not success:
                return {
                    "success": False,
                    "message": "解析配置文件失败"
                }
            
            # 加载元数据
            metadata = self._load_config_metadata(config_name)
            
            return {
                "success": True,
                "message": "配置加载成功",
                "config_name": config_name,
                "config_data": parser.get_all_configs(),
                "metadata": metadata
            }
            
        except Exception as e:
            error_msg = f"加载配置失败: {e}"
            self._log("error", error_msg)
            return {
                "success": False,
                "message": error_msg
            }
    
    def save_config(self, config_name: str, config_data: Dict[str, Any], 
                   metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        保存配置文件
        
        Args:
            config_name: 配置名称
            config_data: 配置数据
            metadata: 元数据（可选）
        
        Returns:
            dict: 操作结果
        """
        try:
            # 创建配置解析器
            parser = ConfigParser(self.logger)
            
            # 设置配置数据
            for key, value in config_data.items():
                parser.set_config_value(key, value)
            
            # 保存配置文件
            config_path = self.configs_dir / f"{config_name}.config"
            success = parser.save_config_file(config_path)
            
            if not success:
                return {
                    "success": False,
                    "message": "保存配置文件失败"
                }
            
            # 更新元数据
            if metadata is None:
                metadata = self._load_config_metadata(config_name) or {}
            
            metadata.update({
                "name": config_name,
                "modified_time": datetime.now().isoformat()
            })
            
            # 保存元数据
            metadata_path = self.configs_dir / f"{config_name}.meta.json"
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            self._log("info", f"配置保存成功: {config_name}")
            
            return {
                "success": True,
                "message": "配置保存成功",
                "config_name": config_name,
                "config_path": str(config_path)
            }
            
        except Exception as e:
            error_msg = f"保存配置失败: {e}"
            self._log("error", error_msg)
            return {
                "success": False,
                "message": error_msg
            }

    def _load_config_metadata(self, config_name: str) -> Optional[Dict[str, Any]]:
        """
        加载配置元数据

        Args:
            config_name: 配置名称

        Returns:
            dict: 元数据
        """
        try:
            metadata_path = self.configs_dir / f"{config_name}.meta.json"

            if not metadata_path.exists():
                return None

            with open(metadata_path, 'r', encoding='utf-8') as f:
                return json.load(f)

        except Exception as e:
            self._log("error", f"加载元数据失败 {config_name}: {e}")
            return None

    def list_configs(self) -> Dict[str, Any]:
        """
        列出所有配置文件

        Returns:
            dict: 配置列表
        """
        try:
            configs = []

            for config_file in self.configs_dir.glob("*.config"):
                config_name = config_file.stem

                # 加载元数据
                metadata = self._load_config_metadata(config_name)

                # 获取文件信息
                stat = config_file.stat()

                config_info = {
                    "name": config_name,
                    "file_size": stat.st_size,
                    "created_time": metadata.get("created_time") if metadata else None,
                    "modified_time": metadata.get("modified_time") if metadata else None,
                    "template_id": metadata.get("template_id") if metadata else None,
                    "template_name": metadata.get("template_name") if metadata else None,
                    "description": metadata.get("description", "") if metadata else "",
                    "target": metadata.get("target", "") if metadata else ""
                }

                configs.append(config_info)

            # 按修改时间排序
            configs.sort(key=lambda x: x.get("modified_time", ""), reverse=True)

            return {
                "success": True,
                "message": "获取配置列表成功",
                "configs": configs,
                "total": len(configs)
            }

        except Exception as e:
            error_msg = f"获取配置列表失败: {e}"
            self._log("error", error_msg)
            return {
                "success": False,
                "message": error_msg,
                "configs": [],
                "total": 0
            }

    def delete_config(self, config_name: str) -> Dict[str, Any]:
        """
        删除配置文件

        Args:
            config_name: 配置名称

        Returns:
            dict: 操作结果
        """
        try:
            config_path = self.configs_dir / f"{config_name}.config"
            metadata_path = self.configs_dir / f"{config_name}.meta.json"

            if not config_path.exists():
                return {
                    "success": False,
                    "message": f"配置文件不存在: {config_name}"
                }

            # 删除配置文件
            config_path.unlink()

            # 删除元数据文件
            if metadata_path.exists():
                metadata_path.unlink()

            self._log("info", f"配置删除成功: {config_name}")

            return {
                "success": True,
                "message": "配置删除成功"
            }

        except Exception as e:
            error_msg = f"删除配置失败: {e}"
            self._log("error", error_msg)
            return {
                "success": False,
                "message": error_msg
            }

    def copy_config(self, source_name: str, target_name: str) -> Dict[str, Any]:
        """
        复制配置文件

        Args:
            source_name: 源配置名称
            target_name: 目标配置名称

        Returns:
            dict: 操作结果
        """
        try:
            source_config_path = self.configs_dir / f"{source_name}.config"
            target_config_path = self.configs_dir / f"{target_name}.config"

            if not source_config_path.exists():
                return {
                    "success": False,
                    "message": f"源配置文件不存在: {source_name}"
                }

            if target_config_path.exists():
                return {
                    "success": False,
                    "message": f"目标配置文件已存在: {target_name}"
                }

            # 复制配置文件
            shutil.copy2(source_config_path, target_config_path)

            # 复制并更新元数据
            source_metadata = self._load_config_metadata(source_name)
            if source_metadata:
                target_metadata = source_metadata.copy()
                target_metadata.update({
                    "name": target_name,
                    "created_time": datetime.now().isoformat(),
                    "modified_time": datetime.now().isoformat()
                })

                metadata_path = self.configs_dir / f"{target_name}.meta.json"
                with open(metadata_path, 'w', encoding='utf-8') as f:
                    json.dump(target_metadata, f, indent=2, ensure_ascii=False)

            self._log("info", f"配置复制成功: {source_name} -> {target_name}")

            return {
                "success": True,
                "message": "配置复制成功",
                "target_name": target_name
            }

        except Exception as e:
            error_msg = f"复制配置失败: {e}"
            self._log("error", error_msg)
            return {
                "success": False,
                "message": error_msg
            }

    def backup_config(self, config_name: str) -> Dict[str, Any]:
        """
        备份配置文件

        Args:
            config_name: 配置名称

        Returns:
            dict: 操作结果
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{config_name}_backup_{timestamp}"

            result = self.copy_config(config_name, backup_name)

            if result["success"]:
                result["message"] = "配置备份成功"
                result["backup_name"] = backup_name

            return result

        except Exception as e:
            error_msg = f"备份配置失败: {e}"
            self._log("error", error_msg)
            return {
                "success": False,
                "message": error_msg
            }

    def export_config_json(self, config_name: str) -> Dict[str, Any]:
        """
        导出配置为JSON格式

        Args:
            config_name: 配置名称

        Returns:
            dict: 操作结果
        """
        try:
            # 加载配置
            result = self.load_config(config_name)
            if not result["success"]:
                return result

            # 准备导出数据
            export_data = {
                "name": config_name,
                "exported_time": datetime.now().isoformat(),
                "metadata": result.get("metadata", {}),
                "config": result["config_data"]
            }

            # 保存JSON文件
            json_path = self.configs_dir / f"{config_name}.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

            self._log("info", f"配置导出成功: {config_name}")

            return {
                "success": True,
                "message": "配置导出成功",
                "json_path": str(json_path),
                "export_data": export_data
            }

        except Exception as e:
            error_msg = f"导出配置失败: {e}"
            self._log("error", error_msg)
            return {
                "success": False,
                "message": error_msg
            }

    def import_config_json(self, json_path: Path, config_name: str = None) -> Dict[str, Any]:
        """
        从JSON文件导入配置

        Args:
            json_path: JSON文件路径
            config_name: 配置名称（可选）

        Returns:
            dict: 操作结果
        """
        try:
            if not json_path.exists():
                return {
                    "success": False,
                    "message": f"JSON文件不存在: {json_path}"
                }

            # 读取JSON文件
            with open(json_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)

            # 验证JSON格式
            if "config" not in import_data:
                return {
                    "success": False,
                    "message": "JSON文件格式不正确，缺少config字段"
                }

            # 生成配置名称
            if not config_name:
                original_name = import_data.get("name", "imported")
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                config_name = f"{original_name}_imported_{timestamp}"

            # 保存配置
            config_data = import_data["config"]
            metadata = import_data.get("metadata", {})
            metadata.update({
                "imported_time": datetime.now().isoformat(),
                "original_name": import_data.get("name", "")
            })

            result = self.save_config(config_name, config_data, metadata)

            if result["success"]:
                result["message"] = "配置导入成功"

            return result

        except Exception as e:
            error_msg = f"导入配置失败: {e}"
            self._log("error", error_msg)
            return {
                "success": False,
                "message": error_msg
            }

    def validate_config(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证配置项

        Args:
            config_data: 配置数据

        Returns:
            dict: 验证结果
        """
        try:
            warnings = []
            errors = []

            # 检查必需的配置项
            required_configs = [
                "CONFIG_TARGET_BOARD",
                "CONFIG_TARGET_SUBTARGET"
            ]

            for required in required_configs:
                if required not in config_data or not config_data[required]:
                    errors.append(f"缺少必需配置项: {required}")

            # 检查冲突的配置项
            conflicts = [
                ("CONFIG_PACKAGE_dnsmasq", "CONFIG_PACKAGE_dnsmasq-full"),
                ("CONFIG_PACKAGE_wpad-basic", "CONFIG_PACKAGE_wpad-openssl")
            ]

            for config1, config2 in conflicts:
                if (config_data.get(config1) and config_data.get(config2)):
                    warnings.append(f"配置冲突: {config1} 和 {config2} 不应同时启用")

            # 检查依赖关系
            dependencies = {
                "CONFIG_PACKAGE_luci-ssl": ["CONFIG_PACKAGE_luci"],
                "CONFIG_PACKAGE_luci-app-firewall": ["CONFIG_PACKAGE_luci"],
                "CONFIG_PACKAGE_block-mount": ["CONFIG_PACKAGE_kmod-usb-storage"]
            }

            for config, deps in dependencies.items():
                if config_data.get(config):
                    for dep in deps:
                        if not config_data.get(dep):
                            warnings.append(f"依赖缺失: {config} 需要 {dep}")

            return {
                "success": True,
                "valid": len(errors) == 0,
                "warnings": warnings,
                "errors": errors,
                "message": "配置验证完成"
            }

        except Exception as e:
            error_msg = f"配置验证失败: {e}"
            self._log("error", error_msg)
            return {
                "success": False,
                "message": error_msg
            }

    def apply_to_lede(self, config_name: str) -> Dict[str, Any]:
        """
        将配置应用到LEDE源码目录

        Args:
            config_name: 配置名称

        Returns:
            dict: 操作结果
        """
        try:
            config_path = self.configs_dir / f"{config_name}.config"

            if not config_path.exists():
                return {
                    "success": False,
                    "message": f"配置文件不存在: {config_name}"
                }

            if not self.lede_dir.exists():
                return {
                    "success": False,
                    "message": "LEDE源码目录不存在"
                }

            # 目标配置文件路径
            target_config_path = self.lede_dir / ".config"

            # 备份现有配置
            if target_config_path.exists():
                backup_path = self.lede_dir / ".config.backup"
                shutil.copy2(target_config_path, backup_path)
                self._log("info", "已备份现有配置文件")

            # 复制配置文件
            shutil.copy2(config_path, target_config_path)

            self._log("info", f"配置已应用到LEDE: {config_name}")

            return {
                "success": True,
                "message": "配置已应用到LEDE源码目录",
                "target_path": str(target_config_path)
            }

        except Exception as e:
            error_msg = f"应用配置到LEDE失败: {e}"
            self._log("error", error_msg)
            return {
                "success": False,
                "message": error_msg
            }
