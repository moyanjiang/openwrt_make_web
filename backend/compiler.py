"""
OpenWrt编译管理器
"""

import os
import re
import time
import threading
from pathlib import Path
from typing import Optional, Dict, Any, Callable, List
from enum import Enum
from queue import Queue, Empty
import shutil

from utils.git_helper import GitHelper
from utils.process_manager import ProcessManager, ProcessStatus
from repository_manager import RepositoryManager
from email_notifier import EmailNotifier
from user_manager import UserManager


class CompileStatus(Enum):
    """编译状态枚举"""
    IDLE = "idle"
    PREPARING = "preparing"
    DOWNLOADING = "downloading"
    CONFIGURING = "configuring"
    COMPILING = "compiling"
    PACKAGING = "packaging"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CompileTask:
    """编译任务"""

    def __init__(self, task_id: str, username: str, config: Dict[str, Any]):
        self.task_id = task_id
        self.username = username
        self.config = config
        self.status = CompileStatus.IDLE
        self.progress = 0.0
        self.start_time = None
        self.end_time = None
        self.error_message = None
        self.output_lines = []
        self.firmware_files = []
        self.device_name = config.get("device_name", "未知设备")
        self.session_id = None  # 用户会话ID


class CompilerManager:
    """编译管理器"""
    
    def __init__(self, config, logger=None, socketio=None, websocket_handler=None,
                 user_manager=None):
        """
        初始化编译管理器

        Args:
            config: 应用配置
            logger: 日志记录器
            socketio: SocketIO实例
            websocket_handler: WebSocket处理器
            user_manager: 用户管理器
        """
        self.config = config
        self.logger = logger
        self.socketio = socketio
        self.websocket_handler = websocket_handler
        self.user_manager = user_manager

        # 初始化工具
        self.git_helper = GitHelper(logger)
        self.process_manager = ProcessManager(logger)
        self.repository_manager = RepositoryManager(config, logger, websocket_handler)
        self.email_notifier = EmailNotifier(config, logger)

        # 任务管理
        self.tasks: Dict[str, CompileTask] = {}
        self.current_task: Optional[CompileTask] = None
        self.task_queue = Queue()

        # 线程锁
        self._lock = threading.Lock()

        # 启动任务处理线程
        self._start_task_processor()
    
    def _log(self, level: str, message: str):
        """记录日志"""
        if self.logger:
            getattr(self.logger, level.lower())(message)
        else:
            print(f"[{level.upper()}] {message}")
    
    def _emit_event(self, event: str, data: Any):
        """发送SocketIO事件"""
        if self.websocket_handler:
            try:
                self.websocket_handler.broadcast_message(event, data)
            except Exception as e:
                self._log("error", f"发送WebSocket事件失败: {e}")
        elif self.socketio:
            try:
                self.socketio.emit(event, data)
            except Exception as e:
                self._log("error", f"发送SocketIO事件失败: {e}")
    
    def _start_task_processor(self):
        """启动任务处理线程"""
        def process_tasks():
            while True:
                try:
                    task = self.task_queue.get(timeout=1)
                    if task:
                        self._execute_task(task)
                        self.task_queue.task_done()
                except Empty:
                    continue
                except Exception as e:
                    self._log("error", f"任务处理线程错误: {e}")
        
        thread = threading.Thread(target=process_tasks, daemon=True)
        thread.start()
        self._log("info", "任务处理线程已启动")

    def start_compile(self, username: str, task_config: Dict[str, Any]) -> Dict[str, Any]:
        """开始编译任务"""
        try:
            task_id = f"compile_{username}_{int(time.time())}"

            # 创建编译任务
            task = CompileTask(task_id, username, task_config)

            # 开始用户编译会话
            if self.user_manager:
                session_id = self.user_manager.start_compile_session(
                    username, task_id, task_config
                )
                task.session_id = session_id

            self.tasks[task_id] = task
            self.task_queue.put(task)

            self._log("info", f"编译任务已创建: {task_id} (用户: {username})")

            return {
                "success": True,
                "task_id": task_id,
                "message": "编译任务已启动"
            }

        except Exception as e:
            error_msg = f"启动编译任务失败: {e}"
            self._log("error", error_msg)
            return {
                "success": False,
                "message": error_msg
            }

    def _execute_task(self, task: CompileTask):
        """执行编译任务"""
        try:
            self.current_task = task
            task.start_time = datetime.now()
            task.status = CompileStatus.PREPARING

            self._emit_task_event('compile_started', task)

            # 1. 准备工作环境
            prepare_result = self._prepare_workspace(task)
            if not prepare_result["success"]:
                self._handle_task_failure(task, prepare_result["message"])
                return

            # 2. 下载依赖包
            download_result = self._download_packages(task)
            if not download_result["success"]:
                self._handle_task_failure(task, download_result["message"])
                return

            # 3. 配置编译选项
            config_result = self._configure_build(task)
            if not config_result["success"]:
                self._handle_task_failure(task, config_result["message"])
                return

            # 4. 执行编译
            compile_result = self._execute_compile(task)
            if not compile_result["success"]:
                self._handle_task_failure(task, compile_result["message"])
                return

            # 5. 收集固件文件
            collect_result = self._collect_firmware(task)
            if not collect_result["success"]:
                self._handle_task_failure(task, collect_result["message"])
                return

            # 编译成功
            self._handle_task_success(task, collect_result)

        except Exception as e:
            error_msg = f"执行编译任务时发生错误: {e}"
            self._log("error", error_msg)
            self._handle_task_failure(task, error_msg)
        finally:
            self.current_task = None

    def _prepare_workspace(self, task: CompileTask) -> Dict[str, Any]:
        """准备工作环境"""
        try:
            self._log("info", f"准备工作环境: {task.username}")
            task.status = CompileStatus.PREPARING
            self._emit_task_event('compile_progress', task, "准备工作环境...")

            # 获取用户工作目录
            work_dir = Path(self.config.WORKSPACE_DIR) / "users" / task.username / "lede"

            # 检查仓库是否存在
            if not self.repository_manager._is_valid_git_repo(work_dir):
                return {
                    "success": False,
                    "message": "源码仓库不存在，请先克隆仓库"
                }

            # 清理之前的编译文件
            self._clean_previous_build(work_dir)

            return {
                "success": True,
                "work_dir": work_dir,
                "message": "工作环境准备完成"
            }

        except Exception as e:
            error_msg = f"准备工作环境失败: {e}"
            self._log("error", error_msg)
            return {
                "success": False,
                "message": error_msg
            }

    def _download_packages(self, task: CompileTask) -> Dict[str, Any]:
        """下载依赖包 (make download)"""
        try:
            self._log("info", f"开始下载依赖包: {task.task_id}")
            task.status = CompileStatus.DOWNLOADING
            self._emit_task_event('compile_progress', task, "下载依赖包...")

            work_dir = Path(self.config.WORKSPACE_DIR) / "users" / task.username / "lede"

            def output_callback(process_id, line):
                task.output_lines.append(line)
                self._emit_task_event('compile_log', task, line)

            # 执行 make download
            download_jobs = self.config.DOWNLOAD_JOBS
            command = f"make download -j{download_jobs}"

            process_id = f"download_{task.task_id}"
            success = self.process_manager.start_process(
                process_id=process_id,
                command=command,
                cwd=work_dir,
                output_callback=output_callback,
                timeout=3600  # 1小时超时
            )

            if not success:
                return {
                    "success": False,
                    "message": "启动下载进程失败"
                }

            # 等待下载完成
            while True:
                status = self.process_manager.get_process_status(process_id)
                if status in [ProcessStatus.COMPLETED, ProcessStatus.FAILED,
                             ProcessStatus.CANCELLED, ProcessStatus.TIMEOUT]:
                    break

                # 更新进度
                task.progress = 20  # 下载阶段占20%
                self._emit_task_event('compile_progress', task, "正在下载依赖包...")

                time.sleep(2)

            if status == ProcessStatus.COMPLETED:
                self._log("info", f"依赖包下载完成: {task.task_id}")
                return {
                    "success": True,
                    "message": "依赖包下载完成"
                }
            else:
                error_msg = f"依赖包下载失败，状态: {status.value}"
                self._log("error", error_msg)
                return {
                    "success": False,
                    "message": error_msg
                }

        except Exception as e:
            error_msg = f"下载依赖包时发生错误: {e}"
            self._log("error", error_msg)
            return {
                "success": False,
                "message": error_msg
            }

    def _handle_task_success(self, task: CompileTask, collect_result: Dict[str, Any]):
        """处理编译成功"""
        try:
            task.end_time = datetime.now()
            task.status = CompileStatus.COMPLETED
            task.progress = 100
            task.firmware_files = collect_result.get("firmware_files", [])

            # 计算编译时间
            compile_duration = task.end_time - task.start_time
            compile_time_str = self._format_duration(compile_duration)

            self._log("info", f"编译任务完成: {task.task_id}, 耗时: {compile_time_str}")

            # 结束用户编译会话
            if self.user_manager and task.session_id:
                result_data = {
                    "firmware_files": task.firmware_files,
                    "compile_time": compile_time_str,
                    "device_name": task.device_name
                }
                self.user_manager.end_compile_session(
                    task.username, task.session_id, True, result_data
                )

            # 发送成功事件
            self._emit_task_event('compile_completed', task, "编译完成")

            # 发送邮件通知
            self._send_email_notification(task, True, compile_time_str)

        except Exception as e:
            self._log("error", f"处理编译成功时发生错误: {e}")

    def _handle_task_failure(self, task: CompileTask, error_message: str):
        """处理编译失败"""
        try:
            task.end_time = datetime.now()
            task.status = CompileStatus.FAILED
            task.error_message = error_message

            # 计算编译时间
            if task.start_time:
                compile_duration = task.end_time - task.start_time
                compile_time_str = self._format_duration(compile_duration)
            else:
                compile_time_str = "0分钟"

            self._log("error", f"编译任务失败: {task.task_id}, 错误: {error_message}")

            # 结束用户编译会话
            if self.user_manager and task.session_id:
                result_data = {
                    "error_message": error_message,
                    "compile_time": compile_time_str,
                    "device_name": task.device_name
                }
                self.user_manager.end_compile_session(
                    task.username, task.session_id, False, result_data
                )

            # 发送失败事件
            self._emit_task_event('compile_failed', task, error_message)

            # 发送邮件通知
            self._send_email_notification(task, False, compile_time_str)

        except Exception as e:
            self._log("error", f"处理编译失败时发生错误: {e}")

    def _send_email_notification(self, task: CompileTask, success: bool, compile_time: str):
        """发送邮件通知"""
        try:
            if not self.user_manager:
                return

            # 获取用户信息
            user_info = self.user_manager.get_user(task.username)
            if not user_info or not user_info.get("email"):
                return

            # 检查用户是否启用邮件通知
            user_settings = user_info.get("settings", {})
            if not user_settings.get("email_notifications", False):
                return

            # 准备邮件数据
            compile_result = {
                "success": success,
                "device_name": task.device_name,
                "compile_time": compile_time,
                "start_time": task.start_time.strftime('%Y-%m-%d %H:%M:%S') if task.start_time else "",
                "end_time": task.end_time.strftime('%Y-%m-%d %H:%M:%S') if task.end_time else "",
                "firmware_files": self._prepare_firmware_download_info(task.firmware_files) if success else [],
                "error_message": task.error_message if not success else ""
            }

            # 发送邮件
            self.email_notifier.send_compile_notification(
                user_info["email"],
                task.username,
                compile_result
            )

            self._log("info", f"邮件通知已发送给用户: {task.username}")

        except Exception as e:
            self._log("error", f"发送邮件通知时发生错误: {e}")

    def _prepare_firmware_download_info(self, firmware_files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """准备固件下载信息"""
        download_info = []

        for file_info in firmware_files:
            download_info.append({
                "name": file_info.get("name", ""),
                "size": self._format_file_size(file_info.get("size", 0)),
                "id": file_info.get("id", ""),
                "path": file_info.get("path", "")
            })

        return download_info

    def _format_duration(self, duration) -> str:
        """格式化时间间隔"""
        total_seconds = int(duration.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        if hours > 0:
            return f"{hours}小时{minutes}分钟"
        elif minutes > 0:
            return f"{minutes}分钟{seconds}秒"
        else:
            return f"{seconds}秒"

    def _format_file_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        if size_bytes == 0:
            return "0B"

        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1

        return f"{size_bytes:.1f}{size_names[i]}"

    def _clean_previous_build(self, work_dir: Path):
        """清理之前的编译文件"""
        try:
            # 清理编译输出目录
            bin_dir = work_dir / "bin"
            if bin_dir.exists():
                shutil.rmtree(bin_dir, ignore_errors=True)

            # 清理临时文件
            tmp_dir = work_dir / "tmp"
            if tmp_dir.exists():
                shutil.rmtree(tmp_dir, ignore_errors=True)

            self._log("info", "清理之前的编译文件完成")

        except Exception as e:
            self._log("warning", f"清理编译文件时发生错误: {e}")

    def _emit_task_event(self, event_type: str, task: CompileTask, message: str = ""):
        """发送任务事件"""
        try:
            event_data = {
                "task_id": task.task_id,
                "username": task.username,
                "status": task.status.value,
                "progress": task.progress,
                "message": message,
                "device_name": task.device_name,
                "timestamp": datetime.now().isoformat()
            }

            if self.websocket_handler:
                self.websocket_handler.broadcast_message(event_type, event_data)

            # 也发送给特定用户
            if self.socketio:
                self.socketio.emit(event_type, event_data, room=f"user_{task.username}")

        except Exception as e:
            self._log("error", f"发送任务事件时发生错误: {e}")
    
    def clone_source(self, force_update: bool = False) -> Dict[str, Any]:
        """
        克隆LEDE源码
        
        Args:
            force_update: 是否强制更新
        
        Returns:
            dict: 操作结果
        """
        try:
            lede_dir = Path(self.config.LEDE_DIR)
            repo_url = self.config.LEDE_REPO_URL
            
            self._log("info", f"开始克隆LEDE源码: {repo_url}")
            
            # 检查是否已存在
            if self.git_helper.check_repository_exists(lede_dir):
                if not force_update:
                    repo_info = self.git_helper.get_repository_info(lede_dir)
                    return {
                        "success": True,
                        "message": "LEDE源码已存在",
                        "repository_info": repo_info
                    }
                else:
                    # 删除现有目录
                    self._log("info", "删除现有LEDE目录")
                    shutil.rmtree(lede_dir, ignore_errors=True)
            
            # 克隆仓库
            def progress_callback(progress, message):
                self._emit_event('clone_progress', {
                    'progress': progress,
                    'message': message
                })
            
            success, message = self.git_helper.clone_repository(
                repo_url, 
                lede_dir,
                progress_callback=progress_callback
            )
            
            if success:
                repo_info = self.git_helper.get_repository_info(lede_dir)
                self._emit_event('clone_complete', {
                    'success': True,
                    'repository_info': repo_info
                })
                
                return {
                    "success": True,
                    "message": "LEDE源码克隆成功",
                    "repository_info": repo_info
                }
            else:
                self._emit_event('clone_error', {
                    'success': False,
                    'message': message
                })
                
                return {
                    "success": False,
                    "message": message
                }
                
        except Exception as e:
            error_msg = f"克隆源码时发生错误: {e}"
            self._log("error", error_msg)
            self._emit_event('clone_error', {
                'success': False,
                'message': error_msg
            })
            
            return {
                "success": False,
                "message": error_msg
            }
    
    def update_feeds(self, enable_istore: bool = True, username: str = None) -> Dict[str, Any]:
        """
        更新feeds（优化版，支持iStore）

        Args:
            enable_istore: 是否启用iStore商店
            username: 用户名（用于多用户环境）

        Returns:
            dict: 操作结果
        """
        try:
            # 确定工作目录
            if username:
                lede_dir = Path(self.config.WORKSPACE_DIR) / "users" / username / "lede"
            else:
                lede_dir = Path(self.config.LEDE_DIR)

            if not self.git_helper.check_repository_exists(lede_dir):
                return {
                    "success": False,
                    "message": "LEDE源码不存在，请先克隆源码"
                }

            self._log("info", f"开始更新feeds (用户: {username or 'default'})")

            # 添加iStore源（如果启用）
            if enable_istore:
                self._log("info", "添加iStore软件源")
                feeds_config = lede_dir / "feeds.conf.default"

                # 检查是否已添加iStore源
                istore_added = False
                if feeds_config.exists():
                    with open(feeds_config, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if 'istore' in content:
                            istore_added = True

                # 添加iStore源
                if not istore_added:
                    with open(feeds_config, 'a', encoding='utf-8') as f:
                        f.write('\n# iStore商店\n')
                        f.write('src-git istore https://github.com/linkease/istore;main\n')
                    self._log("info", "iStore源已添加到feeds.conf.default")

            # 更新feeds
            def output_callback(process_id, line):
                self._emit_event('feeds_log', {
                    'process_id': process_id,
                    'line': line,
                    'username': username
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
                self._log("info", f"执行命令: {command}")

                success = self.process_manager.start_process(
                    process_id=process_id,
                    command=command,
                    cwd=lede_dir,
                    output_callback=output_callback,
                    timeout=1800  # 30分钟超时
                )

                if not success:
                    return {
                        "success": False,
                        "message": f"启动命令失败: {command}"
                    }

                # 等待进程完成
                while True:
                    status = self.process_manager.get_process_status(process_id)
                    if status in [ProcessStatus.COMPLETED, ProcessStatus.FAILED,
                                 ProcessStatus.CANCELLED, ProcessStatus.TIMEOUT]:
                        break
                    time.sleep(1)

                # 检查结果
                if status != ProcessStatus.COMPLETED:
                    error_msg = f"命令执行失败: {command}"
                    self._log("error", error_msg)
                    return {
                        "success": False,
                        "message": error_msg
                    }

            self._log("info", "feeds更新成功")
            return {
                    "success": True,
                    "message": "feeds更新成功"
                }
            else:
                error_msg = f"feeds更新失败，状态: {status.value}"
                self._log("error", error_msg)
                return {
                    "success": False,
                    "message": error_msg
                }
                
        except Exception as e:
            error_msg = f"更新feeds时发生错误: {e}"
            self._log("error", error_msg)
            return {
                "success": False,
                "message": error_msg
            }
    
    def install_feeds(self) -> Dict[str, Any]:
        """
        安装feeds
        
        Returns:
            dict: 操作结果
        """
        try:
            lede_dir = Path(self.config.LEDE_DIR)
            
            if not self.git_helper.check_repository_exists(lede_dir):
                return {
                    "success": False,
                    "message": "LEDE源码不存在，请先克隆源码"
                }
            
            self._log("info", "开始安装feeds")
            
            # 安装feeds
            def output_callback(process_id, line):
                self._emit_event('feeds_log', {
                    'process_id': process_id,
                    'line': line
                })
            
            process_id = "feeds_install"
            command = "./scripts/feeds install -a"
            
            success = self.process_manager.start_process(
                process_id=process_id,
                command=command,
                cwd=lede_dir,
                output_callback=output_callback,
                timeout=1800  # 30分钟超时
            )
            
            if not success:
                return {
                    "success": False,
                    "message": "启动feeds安装进程失败"
                }
            
            # 等待进程完成
            while True:
                status = self.process_manager.get_process_status(process_id)
                if status in [ProcessStatus.COMPLETED, ProcessStatus.FAILED, 
                             ProcessStatus.CANCELLED, ProcessStatus.TIMEOUT]:
                    break
                time.sleep(1)
            
            # 检查结果
            if status == ProcessStatus.COMPLETED:
                self._log("info", "feeds安装成功")
                return {
                    "success": True,
                    "message": "feeds安装成功"
                }
            else:
                error_msg = f"feeds安装失败，状态: {status.value}"
                self._log("error", error_msg)
                return {
                    "success": False,
                    "message": error_msg
                }
                
        except Exception as e:
            error_msg = f"安装feeds时发生错误: {e}"
            self._log("error", error_msg)
            return {
                "success": False,
                "message": error_msg
            }

    def start_compile(self, task_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        开始编译任务

        Args:
            task_id: 任务ID
            config: 编译配置

        Returns:
            dict: 操作结果
        """
        try:
            with self._lock:
                if self.current_task and self.current_task.status in [
                    CompileStatus.CLONING, CompileStatus.UPDATING_FEEDS,
                    CompileStatus.INSTALLING_FEEDS, CompileStatus.CONFIGURING,
                    CompileStatus.COMPILING
                ]:
                    return {
                        "success": False,
                        "message": "已有编译任务正在进行中"
                    }

            # 创建编译任务
            task = CompileTask(task_id, config)
            task.start_time = time.time()

            with self._lock:
                self.tasks[task_id] = task
                self.current_task = task

            # 添加到任务队列
            self.task_queue.put(task)

            self._log("info", f"编译任务已添加到队列: {task_id}")

            return {
                "success": True,
                "message": "编译任务已启动",
                "task_id": task_id
            }

        except Exception as e:
            error_msg = f"启动编译任务时发生错误: {e}"
            self._log("error", error_msg)
            return {
                "success": False,
                "message": error_msg
            }

    def _execute_task(self, task: CompileTask):
        """
        执行编译任务

        Args:
            task: 编译任务
        """
        try:
            self._log("info", f"开始执行编译任务: {task.task_id}")

            # 检查LEDE源码
            lede_dir = Path(self.config.LEDE_DIR)
            if not self.git_helper.check_repository_exists(lede_dir):
                task.status = CompileStatus.FAILED
                task.error_message = "LEDE源码不存在"
                self._emit_compile_status(task)
                return

            # 开始编译
            task.status = CompileStatus.COMPILING
            task.progress = 0.0
            self._emit_compile_status(task)

            # 构建编译命令
            jobs = getattr(self.config, 'MAX_COMPILE_JOBS', 4)
            command = f"make -j{jobs}"

            # 如果有特定目标，添加到命令中
            if 'target' in task.config:
                command += f" {task.config['target']}"

            self._log("info", f"编译命令: {command}")

            # 启动编译进程
            def output_callback(process_id, line):
                task.output_lines.append(line)

                # 计算编译进度
                progress = self._calculate_compile_progress(line, task.output_lines)
                if progress > task.progress:
                    task.progress = progress

                # 发送实时日志
                self._emit_event('compile_log', {
                    'task_id': task.task_id,
                    'line': line,
                    'progress': task.progress
                })

            process_id = f"compile_{task.task_id}"
            timeout = getattr(self.config, 'COMPILE_TIMEOUT', 21600)  # 6小时默认超时

            success = self.process_manager.start_process(
                process_id=process_id,
                command=command,
                cwd=lede_dir,
                output_callback=output_callback,
                timeout=timeout
            )

            if not success:
                task.status = CompileStatus.FAILED
                task.error_message = "启动编译进程失败"
                self._emit_compile_status(task)
                return

            # 等待编译完成
            while True:
                status = self.process_manager.get_process_status(process_id)
                if status in [ProcessStatus.COMPLETED, ProcessStatus.FAILED,
                             ProcessStatus.CANCELLED, ProcessStatus.TIMEOUT]:
                    break
                time.sleep(5)  # 每5秒检查一次状态

            # 处理编译结果
            if status == ProcessStatus.COMPLETED:
                task.status = CompileStatus.COMPLETED
                task.progress = 100.0
                task.end_time = time.time()

                # 收集固件文件
                task.firmware_files = self._collect_firmware_files(lede_dir)

                self._log("info", f"编译任务完成: {task.task_id}")
                self._emit_event('compile_complete', {
                    'task_id': task.task_id,
                    'firmware_files': task.firmware_files
                })
            else:
                task.status = CompileStatus.FAILED
                task.end_time = time.time()
                task.error_message = f"编译失败，进程状态: {status.value}"

                self._log("error", f"编译任务失败: {task.task_id}, 状态: {status.value}")
                self._emit_event('compile_error', {
                    'task_id': task.task_id,
                    'error': task.error_message
                })

            self._emit_compile_status(task)

            # 清理进程信息
            self.process_manager.cleanup_process(process_id)

        except Exception as e:
            task.status = CompileStatus.FAILED
            task.end_time = time.time()
            task.error_message = f"执行编译任务时发生错误: {e}"

            self._log("error", f"执行编译任务失败: {e}")
            self._emit_compile_status(task)

    def _calculate_compile_progress(self, line: str, all_lines: List[str]) -> float:
        """
        计算编译进度

        Args:
            line: 当前输出行
            all_lines: 所有输出行

        Returns:
            float: 进度百分比 (0-100)
        """
        try:
            # 基于关键词的进度估算
            progress_keywords = {
                'Checking': 5,
                'Downloading': 10,
                'Extracting': 15,
                'Patching': 20,
                'Configuring': 25,
                'Building': 30,
                'Compiling': 40,
                'Installing': 80,
                'Packaging': 90,
                'Successfully': 95
            }

            # 检查当前行的关键词
            current_progress = 0
            for keyword, progress in progress_keywords.items():
                if keyword.lower() in line.lower():
                    current_progress = max(current_progress, progress)

            # 基于编译目标数量的进度估算
            if 'make[' in line and '] Entering directory' in line:
                # 统计已进入的目录数量
                entering_count = sum(1 for l in all_lines if '] Entering directory' in l)
                # 假设总共有100个主要编译目标
                target_progress = min(30 + (entering_count * 0.5), 85)
                current_progress = max(current_progress, target_progress)

            return current_progress

        except Exception:
            return 0.0

    def _collect_firmware_files(self, lede_dir: Path) -> List[Dict[str, Any]]:
        """
        收集固件文件

        Args:
            lede_dir: LEDE源码目录

        Returns:
            list: 固件文件列表
        """
        try:
            firmware_files = []
            bin_dir = lede_dir / "bin"

            if not bin_dir.exists():
                return firmware_files

            # 查找固件文件
            for file_path in bin_dir.rglob("*"):
                if file_path.is_file():
                    # 检查是否是固件文件
                    if any(ext in file_path.suffix.lower() for ext in ['.bin', '.img', '.tar.gz', '.zip']):
                        file_info = {
                            "name": file_path.name,
                            "path": str(file_path.relative_to(lede_dir)),
                            "size": file_path.stat().st_size,
                            "modified": file_path.stat().st_mtime
                        }
                        firmware_files.append(file_info)

            return firmware_files

        except Exception as e:
            self._log("error", f"收集固件文件失败: {e}")
            return []

    def _emit_compile_status(self, task: CompileTask):
        """
        发送编译状态事件

        Args:
            task: 编译任务
        """
        self._emit_event('compile_status', {
            'task_id': task.task_id,
            'status': task.status.value,
            'progress': task.progress,
            'start_time': task.start_time,
            'end_time': task.end_time,
            'error_message': task.error_message
        })

    def cancel_compile(self, task_id: str) -> Dict[str, Any]:
        """
        取消编译任务

        Args:
            task_id: 任务ID

        Returns:
            dict: 操作结果
        """
        try:
            with self._lock:
                if task_id not in self.tasks:
                    return {
                        "success": False,
                        "message": "任务不存在"
                    }

                task = self.tasks[task_id]

                if task.status in [CompileStatus.COMPLETED, CompileStatus.FAILED, CompileStatus.CANCELLED]:
                    return {
                        "success": False,
                        "message": "任务已完成或已取消"
                    }

            # 终止编译进程
            process_id = f"compile_{task_id}"
            self.process_manager.kill_process(process_id)

            # 更新任务状态
            task.status = CompileStatus.CANCELLED
            task.end_time = time.time()
            self._emit_compile_status(task)

            self._log("info", f"编译任务已取消: {task_id}")

            return {
                "success": True,
                "message": "编译任务已取消"
            }

        except Exception as e:
            error_msg = f"取消编译任务时发生错误: {e}"
            self._log("error", error_msg)
            return {
                "success": False,
                "message": error_msg
            }

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取任务状态

        Args:
            task_id: 任务ID

        Returns:
            dict: 任务状态信息
        """
        with self._lock:
            if task_id not in self.tasks:
                return None

            task = self.tasks[task_id]

            return {
                "task_id": task.task_id,
                "status": task.status.value,
                "progress": task.progress,
                "start_time": task.start_time,
                "end_time": task.end_time,
                "error_message": task.error_message,
                "firmware_files": task.firmware_files,
                "config": task.config
            }

    def list_tasks(self) -> List[Dict[str, Any]]:
        """
        列出所有任务

        Returns:
            list: 任务列表
        """
        with self._lock:
            tasks = []
            for task in self.tasks.values():
                tasks.append({
                    "task_id": task.task_id,
                    "status": task.status.value,
                    "progress": task.progress,
                    "start_time": task.start_time,
                    "end_time": task.end_time,
                    "error_message": task.error_message,
                    "config": task.config
                })
            return tasks

    def get_repository_status(self) -> Dict[str, Any]:
        """
        获取仓库状态

        Returns:
            dict: 仓库状态信息
        """
        try:
            lede_dir = Path(self.config.LEDE_DIR)

            if not self.git_helper.check_repository_exists(lede_dir):
                return {
                    "exists": False,
                    "message": "LEDE源码不存在"
                }

            repo_info = self.git_helper.get_repository_info(lede_dir)

            return {
                "exists": True,
                "repository_info": repo_info
            }

        except Exception as e:
            error_msg = f"获取仓库状态时发生错误: {e}"
            self._log("error", error_msg)
            return {
                "exists": False,
                "message": error_msg
            }
