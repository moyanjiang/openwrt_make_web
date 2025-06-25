"""
文件服务管理器
"""

import os
import time
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any, BinaryIO, Generator
from datetime import datetime, timedelta
from flask import Response, request, send_file, abort
import tempfile

from utils.file_helper import FileHelper


class FileManager:
    """文件服务管理器"""
    
    def __init__(self, config, logger=None):
        """
        初始化文件管理器
        
        Args:
            config: 应用配置
            logger: 日志记录器
        """
        self.config = config
        self.logger = logger
        self.file_helper = FileHelper(logger)
        
        # 文件存储路径
        self.workspace_dir = Path(config.WORKSPACE_DIR)
        self.firmware_dir = self.workspace_dir / "firmware"
        self.configs_dir = self.workspace_dir / "configs"
        self.uploads_dir = self.workspace_dir / "uploads"
        self.temp_dir = self.workspace_dir / "temp"
        
        # 创建必要目录
        self._ensure_directories()
        
        # 文件管理配置
        self.max_file_size = getattr(config, 'MAX_FILE_SIZE', 100 * 1024 * 1024)  # 100MB
        self.max_upload_size = getattr(config, 'MAX_UPLOAD_SIZE', 10 * 1024 * 1024)  # 10MB
        self.cleanup_interval = getattr(config, 'CLEANUP_INTERVAL', 24 * 3600)  # 24小时
        self.temp_file_max_age = getattr(config, 'TEMP_FILE_MAX_AGE', 1)  # 1天
        
        # 支持的文件类型
        self.allowed_firmware_extensions = {'.bin', '.img', '.tar.gz', '.squashfs'}
        self.allowed_config_extensions = {'.config', '.json', '.txt'}
        
        # 清理线程
        self._cleanup_thread = None
        self._running = False
        
        # 文件锁
        self._file_locks = {}
        self._lock = threading.Lock()
    
    def _log(self, level: str, message: str):
        """记录日志"""
        if self.logger:
            getattr(self.logger, level.lower())(message)
        else:
            print(f"[{level.upper()}] {message}")
    
    def _ensure_directories(self):
        """确保必要目录存在"""
        directories = [
            self.firmware_dir,
            self.configs_dir,
            self.uploads_dir,
            self.temp_dir
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            self._log("debug", f"确保目录存在: {directory}")
    
    def start(self):
        """启动文件管理器"""
        if self._running:
            return
        
        self._running = True
        
        # 启动清理线程
        self._cleanup_thread = threading.Thread(
            target=self._cleanup_worker,
            daemon=True
        )
        self._cleanup_thread.start()
        
        self._log("info", "文件管理器已启动")
    
    def stop(self):
        """停止文件管理器"""
        self._running = False
        
        if self._cleanup_thread:
            self._cleanup_thread.join(timeout=5)
        
        self._log("info", "文件管理器已停止")
    
    def _cleanup_worker(self):
        """清理工作线程"""
        while self._running:
            try:
                # 清理临时文件
                self.file_helper.clean_old_files(
                    self.temp_dir,
                    max_age_days=self.temp_file_max_age
                )
                
                # 清理上传目录中的临时文件
                self.file_helper.clean_old_files(
                    self.uploads_dir,
                    max_age_days=7,
                    file_patterns=['*.tmp', '*.part']
                )
                
                # 等待下次清理
                time.sleep(self.cleanup_interval)
                
            except Exception as e:
                self._log("error", f"清理工作线程错误: {e}")
                time.sleep(60)  # 出错后等待1分钟再重试
    
    def get_firmware_list(self) -> Dict[str, Any]:
        """
        获取固件文件列表
        
        Returns:
            dict: 固件文件列表
        """
        try:
            firmware_files = []
            
            if self.firmware_dir.exists():
                for file_path in self.firmware_dir.iterdir():
                    if file_path.is_file() and file_path.suffix in self.allowed_firmware_extensions:
                        file_info = self.file_helper.get_file_info(file_path)
                        
                        if file_info:
                            # 添加额外信息
                            file_info.update({
                                "download_url": f"/api/files/firmware/{file_path.name}",
                                "md5": self.file_helper.calculate_md5(file_path),
                                "type": "firmware"
                            })
                            firmware_files.append(file_info)
            
            # 按修改时间排序（最新的在前）
            firmware_files.sort(key=lambda x: x.get("modified_time", 0), reverse=True)
            
            return {
                "success": True,
                "files": firmware_files,
                "total": len(firmware_files),
                "message": "获取固件列表成功"
            }
            
        except Exception as e:
            error_msg = f"获取固件列表失败: {e}"
            self._log("error", error_msg)
            return {
                "success": False,
                "files": [],
                "total": 0,
                "message": error_msg
            }
    
    def get_config_list(self) -> Dict[str, Any]:
        """
        获取配置文件列表
        
        Returns:
            dict: 配置文件列表
        """
        try:
            config_files = []
            
            if self.configs_dir.exists():
                for file_path in self.configs_dir.iterdir():
                    if file_path.is_file() and file_path.suffix in self.allowed_config_extensions:
                        file_info = self.file_helper.get_file_info(file_path)
                        
                        if file_info:
                            # 添加额外信息
                            file_info.update({
                                "download_url": f"/api/files/configs/{file_path.name}",
                                "upload_url": f"/api/files/configs/{file_path.name}",
                                "type": "config"
                            })
                            config_files.append(file_info)
            
            # 按修改时间排序（最新的在前）
            config_files.sort(key=lambda x: x.get("modified_time", 0), reverse=True)
            
            return {
                "success": True,
                "files": config_files,
                "total": len(config_files),
                "message": "获取配置列表成功"
            }
            
        except Exception as e:
            error_msg = f"获取配置列表失败: {e}"
            self._log("error", error_msg)
            return {
                "success": False,
                "files": [],
                "total": 0,
                "message": error_msg
            }
    
    def get_storage_info(self) -> Dict[str, Any]:
        """
        获取存储空间信息
        
        Returns:
            dict: 存储空间信息
        """
        try:
            # 获取磁盘空间信息
            available_space = self.file_helper.get_available_space(self.workspace_dir)
            
            # 获取各目录大小
            firmware_size = self.file_helper.get_directory_size(self.firmware_dir)
            configs_size = self.file_helper.get_directory_size(self.configs_dir)
            uploads_size = self.file_helper.get_directory_size(self.uploads_dir)
            temp_size = self.file_helper.get_directory_size(self.temp_dir)
            
            total_used = firmware_size + configs_size + uploads_size + temp_size
            
            return {
                "success": True,
                "storage": {
                    "available_space": available_space,
                    "available_space_human": self.file_helper.format_file_size(available_space),
                    "used_space": total_used,
                    "used_space_human": self.file_helper.format_file_size(total_used),
                    "firmware_size": firmware_size,
                    "firmware_size_human": self.file_helper.format_file_size(firmware_size),
                    "configs_size": configs_size,
                    "configs_size_human": self.file_helper.format_file_size(configs_size),
                    "uploads_size": uploads_size,
                    "uploads_size_human": self.file_helper.format_file_size(uploads_size),
                    "temp_size": temp_size,
                    "temp_size_human": self.file_helper.format_file_size(temp_size)
                },
                "message": "获取存储信息成功"
            }
            
        except Exception as e:
            error_msg = f"获取存储信息失败: {e}"
            self._log("error", error_msg)
            return {
                "success": False,
                "storage": {},
                "message": error_msg
            }
    
    def _get_file_lock(self, file_path: str) -> threading.Lock:
        """
        获取文件锁

        Args:
            file_path: 文件路径

        Returns:
            threading.Lock: 文件锁
        """
        with self._lock:
            if file_path not in self._file_locks:
                self._file_locks[file_path] = threading.Lock()
            return self._file_locks[file_path]

    def download_file(self, file_type: str, filename: str,
                     support_range: bool = True) -> Response:
        """
        下载文件（支持断点续传）

        Args:
            file_type: 文件类型 ('firmware' 或 'config')
            filename: 文件名
            support_range: 是否支持范围请求

        Returns:
            Flask Response: 文件响应
        """
        try:
            # 确定文件路径
            if file_type == 'firmware':
                file_path = self.firmware_dir / filename
                if file_path.suffix not in self.allowed_firmware_extensions:
                    abort(400, "不支持的固件文件类型")
            elif file_type == 'config':
                file_path = self.configs_dir / filename
                if file_path.suffix not in self.allowed_config_extensions:
                    abort(400, "不支持的配置文件类型")
            else:
                abort(400, "无效的文件类型")

            # 检查文件是否存在
            if not file_path.exists():
                abort(404, "文件不存在")

            # 获取文件锁
            file_lock = self._get_file_lock(str(file_path))

            with file_lock:
                # 获取文件信息
                file_size = file_path.stat().st_size

                # 处理范围请求（断点续传）
                range_header = request.headers.get('Range')

                if support_range and range_header:
                    return self._handle_range_request(file_path, file_size, range_header)
                else:
                    # 普通下载
                    return send_file(
                        file_path,
                        as_attachment=True,
                        download_name=filename,
                        mimetype='application/octet-stream'
                    )

        except Exception as e:
            self._log("error", f"文件下载失败 {filename}: {e}")
            abort(500, "文件下载失败")

    def _handle_range_request(self, file_path: Path, file_size: int,
                            range_header: str) -> Response:
        """
        处理范围请求（断点续传）

        Args:
            file_path: 文件路径
            file_size: 文件大小
            range_header: Range头

        Returns:
            Response: 部分内容响应
        """
        try:
            # 解析Range头
            range_match = range_header.replace('bytes=', '').split('-')
            start = int(range_match[0]) if range_match[0] else 0
            end = int(range_match[1]) if range_match[1] else file_size - 1

            # 验证范围
            if start >= file_size or end >= file_size or start > end:
                abort(416, "请求范围无效")

            content_length = end - start + 1

            def generate_file_chunk():
                """生成文件块"""
                with open(file_path, 'rb') as f:
                    f.seek(start)
                    remaining = content_length

                    while remaining > 0:
                        chunk_size = min(8192, remaining)
                        chunk = f.read(chunk_size)

                        if not chunk:
                            break

                        remaining -= len(chunk)
                        yield chunk

            # 创建部分内容响应
            response = Response(
                generate_file_chunk(),
                206,  # Partial Content
                headers={
                    'Content-Range': f'bytes {start}-{end}/{file_size}',
                    'Accept-Ranges': 'bytes',
                    'Content-Length': str(content_length),
                    'Content-Type': 'application/octet-stream'
                }
            )

            return response

        except Exception as e:
            self._log("error", f"处理范围请求失败: {e}")
            abort(500, "处理范围请求失败")

    def upload_config_file(self, file_data: BinaryIO, filename: str,
                          overwrite: bool = False) -> Dict[str, Any]:
        """
        上传配置文件

        Args:
            file_data: 文件数据
            filename: 文件名
            overwrite: 是否覆盖现有文件

        Returns:
            dict: 上传结果
        """
        try:
            # 验证文件名和扩展名
            file_path = Path(filename)
            if file_path.suffix not in self.allowed_config_extensions:
                return {
                    "success": False,
                    "message": f"不支持的文件类型: {file_path.suffix}"
                }

            # 目标文件路径
            target_path = self.configs_dir / filename

            # 检查文件是否已存在
            if target_path.exists() and not overwrite:
                return {
                    "success": False,
                    "message": "文件已存在，请选择覆盖或使用不同的文件名"
                }

            # 获取文件锁
            file_lock = self._get_file_lock(str(target_path))

            with file_lock:
                # 创建临时文件
                temp_path = self.temp_dir / f"{filename}.tmp"

                try:
                    # 写入临时文件
                    with open(temp_path, 'wb') as temp_file:
                        total_size = 0

                        while chunk := file_data.read(8192):
                            # 检查文件大小限制
                            total_size += len(chunk)
                            if total_size > self.max_upload_size:
                                return {
                                    "success": False,
                                    "message": f"文件大小超过限制 ({self.file_helper.format_file_size(self.max_upload_size)})"
                                }

                            temp_file.write(chunk)

                    # 移动到目标位置
                    if target_path.exists():
                        target_path.unlink()  # 删除现有文件

                    temp_path.rename(target_path)

                    # 获取文件信息
                    file_info = self.file_helper.get_file_info(target_path)

                    self._log("info", f"配置文件上传成功: {filename}")

                    return {
                        "success": True,
                        "message": "文件上传成功",
                        "file_info": file_info
                    }

                finally:
                    # 清理临时文件
                    if temp_path.exists():
                        temp_path.unlink()

        except Exception as e:
            error_msg = f"文件上传失败: {e}"
            self._log("error", error_msg)
            return {
                "success": False,
                "message": error_msg
            }

    def delete_file(self, file_type: str, filename: str) -> Dict[str, Any]:
        """
        删除文件

        Args:
            file_type: 文件类型 ('firmware' 或 'config')
            filename: 文件名

        Returns:
            dict: 删除结果
        """
        try:
            # 确定文件路径
            if file_type == 'firmware':
                file_path = self.firmware_dir / filename
            elif file_type == 'config':
                file_path = self.configs_dir / filename
            else:
                return {
                    "success": False,
                    "message": "无效的文件类型"
                }

            # 检查文件是否存在
            if not file_path.exists():
                return {
                    "success": False,
                    "message": "文件不存在"
                }

            # 获取文件锁
            file_lock = self._get_file_lock(str(file_path))

            with file_lock:
                # 删除文件
                file_path.unlink()

                self._log("info", f"文件删除成功: {filename}")

                return {
                    "success": True,
                    "message": "文件删除成功"
                }

        except Exception as e:
            error_msg = f"文件删除失败: {e}"
            self._log("error", error_msg)
            return {
                "success": False,
                "message": error_msg
            }

    def get_file_info(self, file_type: str, filename: str) -> Dict[str, Any]:
        """
        获取文件详细信息

        Args:
            file_type: 文件类型
            filename: 文件名

        Returns:
            dict: 文件信息
        """
        try:
            # 确定文件路径
            if file_type == 'firmware':
                file_path = self.firmware_dir / filename
            elif file_type == 'config':
                file_path = self.configs_dir / filename
            else:
                return {
                    "success": False,
                    "message": "无效的文件类型"
                }

            # 检查文件是否存在
            if not file_path.exists():
                return {
                    "success": False,
                    "message": "文件不存在"
                }

            # 获取文件信息
            file_info = self.file_helper.get_file_info(file_path)

            if file_info:
                # 添加校验值
                file_info.update({
                    "md5": self.file_helper.calculate_md5(file_path),
                    "sha256": self.file_helper.calculate_sha256(file_path),
                    "type": file_type
                })

                return {
                    "success": True,
                    "file_info": file_info,
                    "message": "获取文件信息成功"
                }
            else:
                return {
                    "success": False,
                    "message": "获取文件信息失败"
                }

        except Exception as e:
            error_msg = f"获取文件信息失败: {e}"
            self._log("error", error_msg)
            return {
                "success": False,
                "message": error_msg
            }

    def cleanup_temp_files(self) -> Dict[str, Any]:
        """
        手动清理临时文件

        Returns:
            dict: 清理结果
        """
        try:
            # 清理临时目录
            temp_cleaned = self.file_helper.clean_old_files(
                self.temp_dir,
                max_age_days=0  # 清理所有临时文件
            )

            # 清理上传目录中的临时文件
            upload_cleaned = self.file_helper.clean_old_files(
                self.uploads_dir,
                max_age_days=0,
                file_patterns=['*.tmp', '*.part']
            )

            total_cleaned = temp_cleaned + upload_cleaned

            self._log("info", f"手动清理了 {total_cleaned} 个临时文件")

            return {
                "success": True,
                "cleaned_files": total_cleaned,
                "message": f"清理了 {total_cleaned} 个临时文件"
            }

        except Exception as e:
            error_msg = f"清理临时文件失败: {e}"
            self._log("error", error_msg)
            return {
                "success": False,
                "message": error_msg
            }

    def validate_file(self, file_type: str, filename: str,
                     expected_md5: str = None, expected_sha256: str = None) -> Dict[str, Any]:
        """
        验证文件完整性

        Args:
            file_type: 文件类型
            filename: 文件名
            expected_md5: 期望的MD5值
            expected_sha256: 期望的SHA256值

        Returns:
            dict: 验证结果
        """
        try:
            # 确定文件路径
            if file_type == 'firmware':
                file_path = self.firmware_dir / filename
            elif file_type == 'config':
                file_path = self.configs_dir / filename
            else:
                return {
                    "success": False,
                    "message": "无效的文件类型"
                }

            # 检查文件是否存在
            if not file_path.exists():
                return {
                    "success": False,
                    "message": "文件不存在"
                }

            # 验证文件完整性
            is_valid = self.file_helper.validate_file_integrity(
                file_path, expected_md5, expected_sha256
            )

            if is_valid:
                return {
                    "success": True,
                    "valid": True,
                    "message": "文件完整性验证通过"
                }
            else:
                return {
                    "success": True,
                    "valid": False,
                    "message": "文件完整性验证失败"
                }

        except Exception as e:
            error_msg = f"文件验证失败: {e}"
            self._log("error", error_msg)
            return {
                "success": False,
                "message": error_msg
            }
