"""
Git操作辅助工具
"""

import os
import subprocess
from pathlib import Path
from typing import Optional, Tuple, Callable
import git
from git import Repo, GitCommandError


class GitHelper:
    """Git操作辅助类"""
    
    def __init__(self, logger=None):
        """
        初始化Git辅助工具
        
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
    
    def clone_repository(self,
                        repo_url: str,
                        target_dir,
                        branch: str = None,
                        progress_callback: Optional[Callable] = None) -> Tuple[bool, str]:
        """
        克隆Git仓库
        
        Args:
            repo_url: 仓库URL
            target_dir: 目标目录
            branch: 分支名称（可选）
            progress_callback: 进度回调函数
        
        Returns:
            Tuple[bool, str]: (是否成功, 消息)
        """
        try:
            # 确保target_dir是Path对象
            if isinstance(target_dir, str):
                target_dir = Path(target_dir)

            # 检查目标目录
            if target_dir.exists():
                if target_dir.is_dir() and any(target_dir.iterdir()):
                    return False, f"目标目录 {target_dir} 已存在且不为空"
                elif target_dir.is_file():
                    return False, f"目标路径 {target_dir} 是一个文件"

            # 创建父目录
            target_dir.parent.mkdir(parents=True, exist_ok=True)
            
            self._log("info", f"开始克隆仓库: {repo_url}")
            self._log("info", f"目标目录: {target_dir}")
            
            # 克隆仓库
            clone_kwargs = {
                'progress': self._create_progress_handler(progress_callback) if progress_callback else None
            }
            
            if branch:
                clone_kwargs['branch'] = branch
                self._log("info", f"指定分支: {branch}")
            
            repo = Repo.clone_from(repo_url, target_dir, **clone_kwargs)
            
            self._log("info", f"仓库克隆成功: {repo.working_dir}")
            return True, "仓库克隆成功"
            
        except GitCommandError as e:
            error_msg = f"Git命令执行失败: {e}"
            self._log("error", error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"克隆仓库时发生错误: {e}"
            self._log("error", error_msg)
            return False, error_msg
    
    def _create_progress_handler(self, callback: Callable):
        """创建进度处理器"""
        class ProgressHandler(git.RemoteProgress):
            def __init__(self, callback_func):
                super().__init__()
                self.callback = callback_func
            
            def update(self, op_code, cur_count, max_count=None, message=''):
                if max_count:
                    progress = (cur_count / max_count) * 100
                    self.callback(progress, message)
        
        return ProgressHandler(callback)
    
    def pull_repository(self, repo_dir: Path) -> Tuple[bool, str]:
        """
        拉取仓库更新
        
        Args:
            repo_dir: 仓库目录
        
        Returns:
            Tuple[bool, str]: (是否成功, 消息)
        """
        try:
            if not repo_dir.exists():
                return False, f"仓库目录不存在: {repo_dir}"
            
            repo = Repo(repo_dir)
            
            if repo.bare:
                return False, "这是一个裸仓库，无法拉取"
            
            self._log("info", f"开始拉取仓库更新: {repo_dir}")
            
            # 拉取更新
            origin = repo.remotes.origin
            origin.pull()
            
            self._log("info", "仓库更新成功")
            return True, "仓库更新成功"
            
        except GitCommandError as e:
            error_msg = f"Git拉取失败: {e}"
            self._log("error", error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"拉取仓库时发生错误: {e}"
            self._log("error", error_msg)
            return False, error_msg
    
    def get_repository_info(self, repo_dir: Path) -> Optional[dict]:
        """
        获取仓库信息
        
        Args:
            repo_dir: 仓库目录
        
        Returns:
            dict: 仓库信息
        """
        try:
            if not repo_dir.exists():
                return None
            
            repo = Repo(repo_dir)
            
            # 获取当前分支
            current_branch = repo.active_branch.name if not repo.head.is_detached else "detached"
            
            # 获取最新提交
            latest_commit = repo.head.commit
            
            # 获取远程URL
            remote_url = repo.remotes.origin.url if repo.remotes else None
            
            return {
                "path": str(repo_dir),
                "branch": current_branch,
                "commit_hash": latest_commit.hexsha[:8],
                "commit_message": latest_commit.message.strip(),
                "commit_date": latest_commit.committed_datetime.isoformat(),
                "remote_url": remote_url,
                "is_dirty": repo.is_dirty()
            }
            
        except Exception as e:
            self._log("error", f"获取仓库信息失败: {e}")
            return None
    
    def check_repository_exists(self, repo_dir: Path) -> bool:
        """
        检查仓库是否存在
        
        Args:
            repo_dir: 仓库目录
        
        Returns:
            bool: 是否存在有效的Git仓库
        """
        try:
            if not repo_dir.exists():
                return False
            
            repo = Repo(repo_dir)
            return not repo.bare and repo.git_dir
            
        except Exception:
            return False
