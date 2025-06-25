"""
消息队列管理工具
"""

import time
import threading
from typing import Dict, List, Any, Optional, Callable
from queue import Queue, Empty
from dataclasses import dataclass
from enum import Enum


class MessagePriority(Enum):
    """消息优先级"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Message:
    """消息数据类"""
    id: str
    event: str
    data: Any
    priority: MessagePriority
    timestamp: float
    retry_count: int = 0
    max_retries: int = 3
    target_clients: Optional[List[str]] = None  # None表示广播给所有客户端


class MessageQueue:
    """消息队列管理器"""
    
    def __init__(self, logger=None):
        """
        初始化消息队列
        
        Args:
            logger: 日志记录器
        """
        self.logger = logger
        
        # 消息队列 - 按优先级分组
        self.queues = {
            MessagePriority.CRITICAL: Queue(),
            MessagePriority.HIGH: Queue(),
            MessagePriority.NORMAL: Queue(),
            MessagePriority.LOW: Queue()
        }
        
        # 消息历史记录
        self.message_history: List[Message] = []
        self.max_history_size = 1000
        
        # 失败消息重试队列
        self.retry_queue = Queue()
        
        # 线程控制
        self._running = False
        self._processor_thread = None
        self._retry_thread = None
        self._lock = threading.Lock()
        
        # 消息处理回调
        self.message_handlers: Dict[str, Callable] = {}
        
        # 统计信息
        self.stats = {
            "total_messages": 0,
            "processed_messages": 0,
            "failed_messages": 0,
            "retry_messages": 0
        }
    
    def _log(self, level: str, message: str):
        """记录日志"""
        if self.logger:
            getattr(self.logger, level.lower())(message)
        else:
            print(f"[{level.upper()}] {message}")
    
    def start(self):
        """启动消息队列处理"""
        if self._running:
            return
        
        self._running = True
        
        # 启动消息处理线程
        self._processor_thread = threading.Thread(
            target=self._process_messages,
            daemon=True
        )
        self._processor_thread.start()
        
        # 启动重试处理线程
        self._retry_thread = threading.Thread(
            target=self._process_retries,
            daemon=True
        )
        self._retry_thread.start()
        
        self._log("info", "消息队列处理器已启动")
    
    def stop(self):
        """停止消息队列处理"""
        self._running = False
        
        if self._processor_thread:
            self._processor_thread.join(timeout=5)
        
        if self._retry_thread:
            self._retry_thread.join(timeout=5)
        
        self._log("info", "消息队列处理器已停止")
    
    def add_message(self, event: str, data: Any, 
                   priority: MessagePriority = MessagePriority.NORMAL,
                   target_clients: Optional[List[str]] = None) -> str:
        """
        添加消息到队列
        
        Args:
            event: 事件名称
            data: 消息数据
            priority: 消息优先级
            target_clients: 目标客户端列表（None表示广播）
        
        Returns:
            str: 消息ID
        """
        message_id = f"{event}_{int(time.time() * 1000000)}"
        
        message = Message(
            id=message_id,
            event=event,
            data=data,
            priority=priority,
            timestamp=time.time(),
            target_clients=target_clients
        )
        
        # 添加到对应优先级队列
        self.queues[priority].put(message)
        
        with self._lock:
            self.stats["total_messages"] += 1
        
        self._log("debug", f"消息已添加到队列: {event} (优先级: {priority.name})")
        
        return message_id
    
    def add_message_handler(self, event: str, handler: Callable):
        """
        添加消息处理器
        
        Args:
            event: 事件名称
            handler: 处理函数
        """
        self.message_handlers[event] = handler
        self._log("debug", f"消息处理器已注册: {event}")
    
    def remove_message_handler(self, event: str):
        """
        移除消息处理器
        
        Args:
            event: 事件名称
        """
        if event in self.message_handlers:
            del self.message_handlers[event]
            self._log("debug", f"消息处理器已移除: {event}")
    
    def _process_messages(self):
        """处理消息队列"""
        while self._running:
            try:
                # 按优先级顺序处理消息
                message = None
                
                for priority in [MessagePriority.CRITICAL, MessagePriority.HIGH, 
                               MessagePriority.NORMAL, MessagePriority.LOW]:
                    try:
                        message = self.queues[priority].get(timeout=0.1)
                        break
                    except Empty:
                        continue
                
                if message:
                    self._handle_message(message)
                
            except Exception as e:
                self._log("error", f"消息处理线程错误: {e}")
                time.sleep(1)
    
    def _handle_message(self, message: Message):
        """
        处理单个消息
        
        Args:
            message: 消息对象
        """
        try:
            # 查找消息处理器
            handler = self.message_handlers.get(message.event)
            
            if handler:
                # 调用处理器
                success = handler(message)
                
                if success:
                    with self._lock:
                        self.stats["processed_messages"] += 1
                    
                    # 添加到历史记录
                    self._add_to_history(message)
                    
                    self._log("debug", f"消息处理成功: {message.event}")
                else:
                    # 处理失败，加入重试队列
                    self._add_to_retry(message)
            else:
                self._log("warning", f"未找到消息处理器: {message.event}")
                
        except Exception as e:
            self._log("error", f"处理消息失败 {message.event}: {e}")
            self._add_to_retry(message)
    
    def _add_to_retry(self, message: Message):
        """
        添加消息到重试队列
        
        Args:
            message: 消息对象
        """
        if message.retry_count < message.max_retries:
            message.retry_count += 1
            self.retry_queue.put(message)
            
            with self._lock:
                self.stats["retry_messages"] += 1
            
            self._log("debug", f"消息加入重试队列: {message.event} (重试次数: {message.retry_count})")
        else:
            with self._lock:
                self.stats["failed_messages"] += 1
            
            self._log("error", f"消息重试次数超限，丢弃: {message.event}")
    
    def _process_retries(self):
        """处理重试队列"""
        while self._running:
            try:
                message = self.retry_queue.get(timeout=1)
                
                # 等待一段时间后重试
                time.sleep(min(2 ** message.retry_count, 30))  # 指数退避，最大30秒
                
                # 重新添加到主队列
                self.queues[message.priority].put(message)
                
            except Empty:
                continue
            except Exception as e:
                self._log("error", f"重试处理线程错误: {e}")
    
    def _add_to_history(self, message: Message):
        """
        添加消息到历史记录
        
        Args:
            message: 消息对象
        """
        with self._lock:
            self.message_history.append(message)
            
            # 限制历史记录大小
            if len(self.message_history) > self.max_history_size:
                self.message_history = self.message_history[-self.max_history_size:]
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            dict: 统计信息
        """
        with self._lock:
            stats = self.stats.copy()
        
        # 添加队列大小信息
        stats["queue_sizes"] = {
            priority.name: queue.qsize() 
            for priority, queue in self.queues.items()
        }
        stats["retry_queue_size"] = self.retry_queue.qsize()
        stats["history_size"] = len(self.message_history)
        
        return stats
    
    def get_recent_messages(self, count: int = 50) -> List[Dict[str, Any]]:
        """
        获取最近的消息
        
        Args:
            count: 消息数量
        
        Returns:
            list: 消息列表
        """
        with self._lock:
            recent_messages = self.message_history[-count:]
        
        return [
            {
                "id": msg.id,
                "event": msg.event,
                "data": msg.data,
                "priority": msg.priority.name,
                "timestamp": msg.timestamp,
                "retry_count": msg.retry_count
            }
            for msg in recent_messages
        ]
    
    def clear_history(self):
        """清空消息历史"""
        with self._lock:
            self.message_history.clear()
        
        self._log("info", "消息历史已清空")
