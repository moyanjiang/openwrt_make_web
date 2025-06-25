"""
文件操作辅助工具
"""

import os
import hashlib
import shutil
import mimetypes
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, BinaryIO
import time


class FileHelper:
    """文件操作辅助类"""
    
    def __init__(self, logger=None):
        """
        初始化文件辅助工具
        
        Args:
            logger: 日志记录器
        """
        self.logger = logger
    
    def _log(self, level: str, message: str):
        """记录日志"""
        if self.logger:
            getattr(self.logger, level.lower())(message)
        else:
            print(f"[{level.upper()}] {message}")
    
    def calculate_md5(self, file_path: Path, chunk_size: int = 8192) -> str:
        """
        计算文件MD5校验值
        
        Args:
            file_path: 文件路径
            chunk_size: 读取块大小
        
        Returns:
            str: MD5校验值
        """
        try:
            md5_hash = hashlib.md5()
            
            with open(file_path, 'rb') as f:
                while chunk := f.read(chunk_size):
                    md5_hash.update(chunk)
            
            return md5_hash.hexdigest()
            
        except Exception as e:
            self._log("error", f"计算MD5失败 {file_path}: {e}")
            return ""
    
    def calculate_sha256(self, file_path: Path, chunk_size: int = 8192) -> str:
        """
        计算文件SHA256校验值
        
        Args:
            file_path: 文件路径
            chunk_size: 读取块大小
        
        Returns:
            str: SHA256校验值
        """
        try:
            sha256_hash = hashlib.sha256()
            
            with open(file_path, 'rb') as f:
                while chunk := f.read(chunk_size):
                    sha256_hash.update(chunk)
            
            return sha256_hash.hexdigest()
            
        except Exception as e:
            self._log("error", f"计算SHA256失败 {file_path}: {e}")
            return ""
    
    def get_file_info(self, file_path: Path) -> Dict[str, Any]:
        """
        获取文件信息
        
        Args:
            file_path: 文件路径
        
        Returns:
            dict: 文件信息
        """
        try:
            if not file_path.exists():
                return {}
            
            stat = file_path.stat()
            
            # 获取MIME类型
            mime_type, _ = mimetypes.guess_type(str(file_path))
            
            return {
                "name": file_path.name,
                "path": str(file_path),
                "size": stat.st_size,
                "size_human": self.format_file_size(stat.st_size),
                "created_time": stat.st_ctime,
                "modified_time": stat.st_mtime,
                "accessed_time": stat.st_atime,
                "mime_type": mime_type or "application/octet-stream",
                "extension": file_path.suffix.lower(),
                "is_file": file_path.is_file(),
                "is_dir": file_path.is_dir()
            }
            
        except Exception as e:
            self._log("error", f"获取文件信息失败 {file_path}: {e}")
            return {}
    
    def format_file_size(self, size_bytes: int) -> str:
        """
        格式化文件大小
        
        Args:
            size_bytes: 字节大小
        
        Returns:
            str: 格式化后的大小
        """
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"
    
    def get_directory_size(self, directory: Path) -> int:
        """
        获取目录总大小
        
        Args:
            directory: 目录路径
        
        Returns:
            int: 目录大小（字节）
        """
        try:
            total_size = 0
            
            for file_path in directory.rglob("*"):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
            
            return total_size
            
        except Exception as e:
            self._log("error", f"获取目录大小失败 {directory}: {e}")
            return 0
    
    def clean_old_files(self, directory: Path, max_age_days: int = 7, 
                       file_patterns: List[str] = None) -> int:
        """
        清理过期文件
        
        Args:
            directory: 目录路径
            max_age_days: 最大保留天数
            file_patterns: 文件模式列表（如 ['*.tmp', '*.log']）
        
        Returns:
            int: 清理的文件数量
        """
        try:
            if not directory.exists():
                return 0
            
            current_time = time.time()
            max_age_seconds = max_age_days * 24 * 3600
            cleaned_count = 0
            
            # 如果没有指定模式，清理所有文件
            if not file_patterns:
                file_patterns = ["*"]
            
            for pattern in file_patterns:
                for file_path in directory.glob(pattern):
                    if file_path.is_file():
                        file_age = current_time - file_path.stat().st_mtime
                        
                        if file_age > max_age_seconds:
                            try:
                                file_path.unlink()
                                cleaned_count += 1
                                self._log("debug", f"清理过期文件: {file_path}")
                            except Exception as e:
                                self._log("error", f"删除文件失败 {file_path}: {e}")
            
            if cleaned_count > 0:
                self._log("info", f"清理了 {cleaned_count} 个过期文件")
            
            return cleaned_count
            
        except Exception as e:
            self._log("error", f"清理过期文件失败: {e}")
            return 0
    
    def safe_copy_file(self, src: Path, dst: Path, 
                      chunk_size: int = 1024*1024) -> bool:
        """
        安全复制文件（支持大文件）
        
        Args:
            src: 源文件路径
            dst: 目标文件路径
            chunk_size: 复制块大小
        
        Returns:
            bool: 是否复制成功
        """
        try:
            if not src.exists():
                self._log("error", f"源文件不存在: {src}")
                return False
            
            # 创建目标目录
            dst.parent.mkdir(parents=True, exist_ok=True)
            
            # 分块复制文件
            with open(src, 'rb') as src_file, open(dst, 'wb') as dst_file:
                while chunk := src_file.read(chunk_size):
                    dst_file.write(chunk)
            
            # 验证文件大小
            if src.stat().st_size != dst.stat().st_size:
                self._log("error", f"文件复制大小不匹配: {src} -> {dst}")
                dst.unlink(missing_ok=True)
                return False
            
            self._log("debug", f"文件复制成功: {src} -> {dst}")
            return True
            
        except Exception as e:
            self._log("error", f"文件复制失败: {e}")
            # 清理可能的不完整文件
            if dst.exists():
                dst.unlink(missing_ok=True)
            return False
    
    def validate_file_integrity(self, file_path: Path, 
                              expected_md5: str = None,
                              expected_sha256: str = None) -> bool:
        """
        验证文件完整性
        
        Args:
            file_path: 文件路径
            expected_md5: 期望的MD5值
            expected_sha256: 期望的SHA256值
        
        Returns:
            bool: 文件是否完整
        """
        try:
            if not file_path.exists():
                return False
            
            if expected_md5:
                actual_md5 = self.calculate_md5(file_path)
                if actual_md5.lower() != expected_md5.lower():
                    self._log("error", f"MD5校验失败: {file_path}")
                    return False
            
            if expected_sha256:
                actual_sha256 = self.calculate_sha256(file_path)
                if actual_sha256.lower() != expected_sha256.lower():
                    self._log("error", f"SHA256校验失败: {file_path}")
                    return False
            
            return True
            
        except Exception as e:
            self._log("error", f"文件完整性验证失败: {e}")
            return False
    
    def get_available_space(self, path: Path) -> int:
        """
        获取可用磁盘空间
        
        Args:
            path: 路径
        
        Returns:
            int: 可用空间（字节）
        """
        try:
            stat = shutil.disk_usage(path)
            return stat.free
            
        except Exception as e:
            self._log("error", f"获取磁盘空间失败: {e}")
            return 0
