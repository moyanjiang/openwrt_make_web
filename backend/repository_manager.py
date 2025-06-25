"""
Git仓库管理器
处理LEDE源码克隆、更新、iStore集成等功能
"""

import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from enum import Enum

from utils.logger import setup_logger
from utils.process_manager import ProcessManager, ProcessStatus


class RepositoryStatus(Enum):
    """仓库状态枚举"""
    NOT_CLONED = "not_cloned"
    CLONING = "cloning"
    READY = "ready"
    UPDATING = "updating"
    ERROR = "error"


class RepositoryManager:
    """Git仓库管理器"""
    
    def __init__(self, config, logger=None, websocket_handler=None):
        self.config = config
        self.logger = logger or setup_logger(__name__)
        self.websocket_handler = websocket_handler
        self.process_manager = ProcessManager(logger)
        
        # 仓库配置
        self.lede_repo_url = config.LEDE_REPO_URL
        self.lede_branch = config.LEDE_BRANCH
        self.istore_repo_url = config.ISTORE_REPO_URL
        self.istore_branch = config.ISTORE_BRANCH
        
        # 状态跟踪
        self.status = RepositoryStatus.NOT_CLONED
        self.current_operation = None
    
    def clone_repository(self, username: str = None, force_rebuild: bool = False, 
                        enable_istore: bool = True, progress_callback: Callable = None) -> Dict[str, Any]:
        """克隆LEDE仓库"""
        try:
            # 确定工作目录
            if username:
                work_dir = Path(self.config.WORKSPACE_DIR) / "users" / username / "lede"
            else:
                work_dir = Path(self.config.LEDE_DIR)
            
            self.logger.info(f"开始克隆LEDE仓库到: {work_dir}")
            self.status = RepositoryStatus.CLONING
            self.current_operation = "cloning"
            
            # 检查是否需要重新克隆
            if work_dir.exists():
                if force_rebuild:
                    self.logger.info("强制重建，删除现有仓库")
                    shutil.rmtree(work_dir, ignore_errors=True)
                else:
                    # 检查是否为有效的git仓库
                    if self._is_valid_git_repo(work_dir):
                        self.logger.info("仓库已存在且有效，跳过克隆")
                        self.status = RepositoryStatus.READY
                        return {
                            "success": True,
                            "message": "仓库已存在",
                            "path": str(work_dir),
                            "status": "ready"
                        }
                    else:
                        self.logger.warning("现有目录不是有效的git仓库，删除重建")
                        shutil.rmtree(work_dir, ignore_errors=True)
            
            # 确保父目录存在
            work_dir.parent.mkdir(parents=True, exist_ok=True)
            
            # 克隆仓库
            clone_result = self._execute_git_clone(work_dir, progress_callback)
            if not clone_result["success"]:
                self.status = RepositoryStatus.ERROR
                return clone_result
            
            # 自动集成iStore
            if enable_istore:
                istore_result = self._integrate_istore(work_dir, progress_callback)
                if not istore_result["success"]:
                    self.logger.warning(f"iStore集成失败: {istore_result['message']}")
                    # 不影响主流程，继续执行
            
            # 自动更新feeds
            update_result = self._update_feeds(work_dir, enable_istore, progress_callback)
            if not update_result["success"]:
                self.logger.warning(f"Feeds更新失败: {update_result['message']}")
                # 不影响主流程，继续执行
            
            self.status = RepositoryStatus.READY
            self.current_operation = None
            
            return {
                "success": True,
                "message": "仓库克隆完成",
                "path": str(work_dir),
                "status": "ready",
                "istore_enabled": enable_istore
            }
            
        except Exception as e:
            error_msg = f"克隆仓库时发生错误: {e}"
            self.logger.error(error_msg)
            self.status = RepositoryStatus.ERROR
            self.current_operation = None
            
            return {
                "success": False,
                "message": error_msg,
                "status": "error"
            }
    
    def _execute_git_clone(self, work_dir: Path, progress_callback: Callable = None) -> Dict[str, Any]:
        """执行git克隆"""
        try:
            # 使用git clone命令
            cmd = f"git clone --depth 1 --branch {self.lede_branch} {self.lede_repo_url} {work_dir.name}"
            
            def output_callback(process_id, line):
                if progress_callback:
                    progress_callback("clone", line)
                if self.websocket_handler:
                    self.websocket_handler.broadcast_message('clone_progress', {
                        'message': line,
                        'stage': 'clone'
                    })
            
            process_id = "git_clone"
            success = self.process_manager.start_process(
                process_id=process_id,
                command=cmd,
                cwd=work_dir.parent,
                output_callback=output_callback,
                timeout=1800  # 30分钟超时
            )
            
            if not success:
                return {"success": False, "message": "启动git clone进程失败"}
            
            # 等待克隆完成
            while True:
                status = self.process_manager.get_process_status(process_id)
                if status in [ProcessStatus.COMPLETED, ProcessStatus.FAILED, 
                             ProcessStatus.CANCELLED, ProcessStatus.TIMEOUT]:
                    break
                
                # 发送心跳
                if self.websocket_handler:
                    self.websocket_handler.broadcast_message('clone_heartbeat', {
                        'status': 'cloning',
                        'timestamp': str(Path().ctime())
                    })
                
                import time
                time.sleep(2)
            
            if status == ProcessStatus.COMPLETED:
                self.logger.info("Git克隆完成")
                return {"success": True, "message": "Git克隆完成"}
            else:
                error_msg = f"Git克隆失败，状态: {status.value}"
                self.logger.error(error_msg)
                return {"success": False, "message": error_msg}
                
        except Exception as e:
            error_msg = f"执行git clone时发生错误: {e}"
            self.logger.error(error_msg)
            return {"success": False, "message": error_msg}
    
    def _integrate_istore(self, work_dir: Path, progress_callback: Callable = None) -> Dict[str, Any]:
        """集成iStore商店"""
        try:
            self.logger.info("开始集成iStore商店")
            
            if progress_callback:
                progress_callback("istore", "正在集成iStore商店...")
            
            feeds_config = work_dir / "feeds.conf.default"
            
            # 检查是否已添加iStore源
            istore_added = False
            if feeds_config.exists():
                with open(feeds_config, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'istore' in content:
                        istore_added = True
                        self.logger.info("iStore源已存在")
            
            # 添加iStore源
            if not istore_added:
                with open(feeds_config, 'a', encoding='utf-8') as f:
                    f.write('\n# iStore商店\n')
                    f.write(f'src-git istore {self.istore_repo_url};{self.istore_branch}\n')
                self.logger.info("iStore源已添加到feeds.conf.default")
            
            return {"success": True, "message": "iStore集成完成"}
            
        except Exception as e:
            error_msg = f"集成iStore时发生错误: {e}"
            self.logger.error(error_msg)
            return {"success": False, "message": error_msg}
    
    def _update_feeds(self, work_dir: Path, enable_istore: bool = True, 
                     progress_callback: Callable = None) -> Dict[str, Any]:
        """更新feeds"""
        try:
            self.logger.info("开始更新feeds")
            
            if progress_callback:
                progress_callback("feeds", "正在更新feeds...")
            
            def output_callback(process_id, line):
                if progress_callback:
                    progress_callback("feeds", line)
                if self.websocket_handler:
                    self.websocket_handler.broadcast_message('feeds_progress', {
                        'message': line,
                        'stage': 'feeds'
                    })
            
            # 执行feeds更新命令
            commands = [
                "./scripts/feeds update -a",
                "./scripts/feeds install -a"
            ]
            
            if enable_istore:
                commands.extend([
                    "./scripts/feeds update istore",
                    "./scripts/feeds install -d y -p istore luci-app-store"
                ])
            
            for i, command in enumerate(commands):
                process_id = f"feeds_update_{i}"
                self.logger.info(f"执行命令: {command}")
                
                success = self.process_manager.start_process(
                    process_id=process_id,
                    command=command,
                    cwd=work_dir,
                    output_callback=output_callback,
                    timeout=1800  # 30分钟超时
                )
                
                if not success:
                    return {"success": False, "message": f"启动命令失败: {command}"}
                
                # 等待命令完成
                while True:
                    status = self.process_manager.get_process_status(process_id)
                    if status in [ProcessStatus.COMPLETED, ProcessStatus.FAILED, 
                                 ProcessStatus.CANCELLED, ProcessStatus.TIMEOUT]:
                        break
                    import time
                    time.sleep(1)
                
                if status != ProcessStatus.COMPLETED:
                    error_msg = f"命令执行失败: {command}, 状态: {status.value}"
                    self.logger.error(error_msg)
                    return {"success": False, "message": error_msg}
            
            self.logger.info("Feeds更新完成")
            return {"success": True, "message": "Feeds更新完成"}
            
        except Exception as e:
            error_msg = f"更新feeds时发生错误: {e}"
            self.logger.error(error_msg)
            return {"success": False, "message": error_msg}
    
    def update_repository(self, username: str = None, enable_istore: bool = True, 
                         progress_callback: Callable = None) -> Dict[str, Any]:
        """更新现有仓库"""
        try:
            # 确定工作目录
            if username:
                work_dir = Path(self.config.WORKSPACE_DIR) / "users" / username / "lede"
            else:
                work_dir = Path(self.config.LEDE_DIR)
            
            if not self._is_valid_git_repo(work_dir):
                return {
                    "success": False,
                    "message": "仓库不存在或无效，请先克隆仓库"
                }
            
            self.logger.info(f"开始更新仓库: {work_dir}")
            self.status = RepositoryStatus.UPDATING
            self.current_operation = "updating"
            
            # Git pull更新
            pull_result = self._execute_git_pull(work_dir, progress_callback)
            if not pull_result["success"]:
                self.status = RepositoryStatus.ERROR
                return pull_result
            
            # 更新iStore（如果启用）
            if enable_istore:
                istore_result = self._integrate_istore(work_dir, progress_callback)
                if not istore_result["success"]:
                    self.logger.warning(f"iStore更新失败: {istore_result['message']}")
            
            # 更新feeds
            update_result = self._update_feeds(work_dir, enable_istore, progress_callback)
            if not update_result["success"]:
                self.logger.warning(f"Feeds更新失败: {update_result['message']}")
            
            self.status = RepositoryStatus.READY
            self.current_operation = None
            
            return {
                "success": True,
                "message": "仓库更新完成",
                "path": str(work_dir),
                "status": "ready"
            }
            
        except Exception as e:
            error_msg = f"更新仓库时发生错误: {e}"
            self.logger.error(error_msg)
            self.status = RepositoryStatus.ERROR
            self.current_operation = None
            
            return {
                "success": False,
                "message": error_msg,
                "status": "error"
            }
    
    def _execute_git_pull(self, work_dir: Path, progress_callback: Callable = None) -> Dict[str, Any]:
        """执行git pull"""
        try:
            cmd = "git pull origin " + self.lede_branch
            
            def output_callback(process_id, line):
                if progress_callback:
                    progress_callback("pull", line)
                if self.websocket_handler:
                    self.websocket_handler.broadcast_message('update_progress', {
                        'message': line,
                        'stage': 'pull'
                    })
            
            process_id = "git_pull"
            success = self.process_manager.start_process(
                process_id=process_id,
                command=cmd,
                cwd=work_dir,
                output_callback=output_callback,
                timeout=600  # 10分钟超时
            )
            
            if not success:
                return {"success": False, "message": "启动git pull进程失败"}
            
            # 等待更新完成
            while True:
                status = self.process_manager.get_process_status(process_id)
                if status in [ProcessStatus.COMPLETED, ProcessStatus.FAILED, 
                             ProcessStatus.CANCELLED, ProcessStatus.TIMEOUT]:
                    break
                import time
                time.sleep(1)
            
            if status == ProcessStatus.COMPLETED:
                self.logger.info("Git更新完成")
                return {"success": True, "message": "Git更新完成"}
            else:
                error_msg = f"Git更新失败，状态: {status.value}"
                self.logger.error(error_msg)
                return {"success": False, "message": error_msg}
                
        except Exception as e:
            error_msg = f"执行git pull时发生错误: {e}"
            self.logger.error(error_msg)
            return {"success": False, "message": error_msg}
    
    def rebuild_repository(self, username: str = None, enable_istore: bool = True, 
                          progress_callback: Callable = None) -> Dict[str, Any]:
        """重构仓库（完全重新克隆）"""
        return self.clone_repository(username, force_rebuild=True, 
                                   enable_istore=enable_istore, 
                                   progress_callback=progress_callback)
    
    def _is_valid_git_repo(self, path: Path) -> bool:
        """检查是否为有效的git仓库"""
        try:
            if not path.exists():
                return False
            
            git_dir = path / ".git"
            return git_dir.exists()
            
        except Exception:
            return False
    
    def get_repository_info(self, username: str = None) -> Dict[str, Any]:
        """获取仓库信息"""
        try:
            # 确定工作目录
            if username:
                work_dir = Path(self.config.WORKSPACE_DIR) / "users" / username / "lede"
            else:
                work_dir = Path(self.config.LEDE_DIR)
            
            if not self._is_valid_git_repo(work_dir):
                return {
                    "exists": False,
                    "status": "not_cloned",
                    "message": "仓库未克隆"
                }
            
            # 获取git信息
            try:
                # 获取当前分支
                result = subprocess.run(
                    ["git", "branch", "--show-current"],
                    cwd=work_dir,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                current_branch = result.stdout.strip() if result.returncode == 0 else "unknown"
                
                # 获取最后提交信息
                result = subprocess.run(
                    ["git", "log", "-1", "--format=%H|%s|%an|%ad", "--date=short"],
                    cwd=work_dir,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    commit_info = result.stdout.strip().split('|')
                    last_commit = {
                        "hash": commit_info[0][:8] if len(commit_info) > 0 else "",
                        "message": commit_info[1] if len(commit_info) > 1 else "",
                        "author": commit_info[2] if len(commit_info) > 2 else "",
                        "date": commit_info[3] if len(commit_info) > 3 else ""
                    }
                else:
                    last_commit = {}
                
                return {
                    "exists": True,
                    "status": self.status.value,
                    "path": str(work_dir),
                    "branch": current_branch,
                    "last_commit": last_commit,
                    "repo_url": self.lede_repo_url
                }
                
            except subprocess.TimeoutExpired:
                return {
                    "exists": True,
                    "status": "timeout",
                    "message": "获取仓库信息超时"
                }
                
        except Exception as e:
            self.logger.error(f"获取仓库信息时发生错误: {e}")
            return {
                "exists": False,
                "status": "error",
                "message": str(e)
            }
