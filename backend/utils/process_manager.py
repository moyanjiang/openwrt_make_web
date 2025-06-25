"""
进程管理工具
"""

import os
import subprocess
import threading
import time
import signal
import psutil
from typing import Optional, Callable, Dict, Any
from pathlib import Path
from queue import Queue, Empty
from enum import Enum


class ProcessStatus(Enum):
    """进程状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class ProcessManager:
    """进程管理器"""
    
    def __init__(self, logger=None):
        """
        初始化进程管理器
        
        Args:
            logger: 日志记录器
        """
        self.logger = logger
        self.processes: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
    
    def _log(self, level: str, message: str):
        """记录日志"""
        if self.logger:
            getattr(self.logger, level.lower())(message)
        else:
            print(f"[{level.upper()}] {message}")
    
    def start_process(self, 
                     process_id: str,
                     command: str,
                     cwd: Optional[Path] = None,
                     env: Optional[Dict[str, str]] = None,
                     output_callback: Optional[Callable] = None,
                     timeout: Optional[int] = None) -> bool:
        """
        启动进程
        
        Args:
            process_id: 进程ID
            command: 命令
            cwd: 工作目录
            env: 环境变量
            output_callback: 输出回调函数
            timeout: 超时时间（秒）
        
        Returns:
            bool: 是否启动成功
        """
        try:
            with self._lock:
                if process_id in self.processes:
                    self._log("warning", f"进程 {process_id} 已存在")
                    return False
            
            self._log("info", f"启动进程: {process_id}")
            self._log("info", f"命令: {command}")
            self._log("info", f"工作目录: {cwd}")
            
            # 准备环境变量
            process_env = os.environ.copy()
            if env:
                process_env.update(env)
            
            # 启动进程
            process = subprocess.Popen(
                command,
                shell=True,
                cwd=str(cwd) if cwd else None,
                env=process_env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            # 创建输出队列
            output_queue = Queue()
            
            # 存储进程信息
            process_info = {
                "process": process,
                "status": ProcessStatus.RUNNING,
                "command": command,
                "cwd": str(cwd) if cwd else None,
                "start_time": time.time(),
                "end_time": None,
                "output_queue": output_queue,
                "output_callback": output_callback,
                "timeout": timeout,
                "output_lines": []
            }
            
            with self._lock:
                self.processes[process_id] = process_info
            
            # 启动输出读取线程
            output_thread = threading.Thread(
                target=self._read_output,
                args=(process_id, process, output_queue, output_callback),
                daemon=True
            )
            output_thread.start()
            
            # 启动进程监控线程
            monitor_thread = threading.Thread(
                target=self._monitor_process,
                args=(process_id,),
                daemon=True
            )
            monitor_thread.start()
            
            return True
            
        except Exception as e:
            self._log("error", f"启动进程失败: {e}")
            return False
    
    def _read_output(self, process_id: str, process: subprocess.Popen, 
                    output_queue: Queue, callback: Optional[Callable]):
        """读取进程输出"""
        try:
            for line in iter(process.stdout.readline, ''):
                if line:
                    line = line.rstrip('\n\r')
                    output_queue.put(line)
                    
                    # 存储输出行
                    with self._lock:
                        if process_id in self.processes:
                            self.processes[process_id]["output_lines"].append(line)
                    
                    # 调用回调函数
                    if callback:
                        try:
                            callback(process_id, line)
                        except Exception as e:
                            self._log("error", f"输出回调函数执行失败: {e}")
            
        except Exception as e:
            self._log("error", f"读取进程输出失败: {e}")
        finally:
            if process.stdout:
                process.stdout.close()
    
    def _monitor_process(self, process_id: str):
        """监控进程状态"""
        try:
            with self._lock:
                if process_id not in self.processes:
                    return
                
                process_info = self.processes[process_id]
                process = process_info["process"]
                timeout = process_info["timeout"]
                start_time = process_info["start_time"]
            
            # 等待进程完成或超时
            while True:
                return_code = process.poll()
                
                if return_code is not None:
                    # 进程已完成
                    with self._lock:
                        if process_id in self.processes:
                            self.processes[process_id]["end_time"] = time.time()
                            if return_code == 0:
                                self.processes[process_id]["status"] = ProcessStatus.COMPLETED
                                self._log("info", f"进程 {process_id} 完成")
                            else:
                                self.processes[process_id]["status"] = ProcessStatus.FAILED
                                self._log("error", f"进程 {process_id} 失败，返回码: {return_code}")
                    break
                
                # 检查超时
                if timeout and (time.time() - start_time) > timeout:
                    self._log("warning", f"进程 {process_id} 超时，正在终止")
                    self.kill_process(process_id)
                    with self._lock:
                        if process_id in self.processes:
                            self.processes[process_id]["status"] = ProcessStatus.TIMEOUT
                    break
                
                time.sleep(1)
                
        except Exception as e:
            self._log("error", f"监控进程失败: {e}")
    
    def kill_process(self, process_id: str) -> bool:
        """
        终止进程
        
        Args:
            process_id: 进程ID
        
        Returns:
            bool: 是否成功终止
        """
        try:
            with self._lock:
                if process_id not in self.processes:
                    return False
                
                process_info = self.processes[process_id]
                process = process_info["process"]
            
            if process.poll() is None:  # 进程仍在运行
                self._log("info", f"终止进程: {process_id}")
                
                # 尝试优雅终止
                try:
                    if os.name == 'nt':  # Windows
                        process.terminate()
                    else:  # Unix/Linux
                        process.send_signal(signal.SIGTERM)
                    
                    # 等待进程终止
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        # 强制终止
                        process.kill()
                        process.wait()
                        
                except Exception as e:
                    self._log("error", f"终止进程失败: {e}")
                    return False
            
            with self._lock:
                if process_id in self.processes:
                    self.processes[process_id]["status"] = ProcessStatus.CANCELLED
                    self.processes[process_id]["end_time"] = time.time()
            
            return True
            
        except Exception as e:
            self._log("error", f"终止进程失败: {e}")
            return False
    
    def get_process_status(self, process_id: str) -> Optional[ProcessStatus]:
        """
        获取进程状态
        
        Args:
            process_id: 进程ID
        
        Returns:
            ProcessStatus: 进程状态
        """
        with self._lock:
            if process_id in self.processes:
                return self.processes[process_id]["status"]
            return None
    
    def get_process_info(self, process_id: str) -> Optional[Dict[str, Any]]:
        """
        获取进程信息
        
        Args:
            process_id: 进程ID
        
        Returns:
            dict: 进程信息
        """
        with self._lock:
            if process_id not in self.processes:
                return None
            
            process_info = self.processes[process_id].copy()
            
            # 移除不可序列化的对象
            process_info.pop("process", None)
            process_info.pop("output_queue", None)
            process_info.pop("output_callback", None)
            
            # 转换状态为字符串
            process_info["status"] = process_info["status"].value
            
            return process_info
    
    def get_process_output(self, process_id: str, last_n_lines: Optional[int] = None) -> list:
        """
        获取进程输出
        
        Args:
            process_id: 进程ID
            last_n_lines: 获取最后N行（可选）
        
        Returns:
            list: 输出行列表
        """
        with self._lock:
            if process_id not in self.processes:
                return []
            
            output_lines = self.processes[process_id]["output_lines"]
            
            if last_n_lines:
                return output_lines[-last_n_lines:]
            else:
                return output_lines.copy()
    
    def cleanup_process(self, process_id: str):
        """
        清理进程信息
        
        Args:
            process_id: 进程ID
        """
        with self._lock:
            if process_id in self.processes:
                del self.processes[process_id]
                self._log("info", f"清理进程信息: {process_id}")
    
    def list_processes(self) -> Dict[str, Dict[str, Any]]:
        """
        列出所有进程
        
        Returns:
            dict: 进程信息字典
        """
        with self._lock:
            result = {}
            for process_id, process_info in self.processes.items():
                info = process_info.copy()
                info.pop("process", None)
                info.pop("output_queue", None)
                info.pop("output_callback", None)
                info["status"] = info["status"].value
                result[process_id] = info
            return result
