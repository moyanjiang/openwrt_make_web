"""
WebSocket实时通信处理器
"""

import time
import threading
from datetime import datetime
from typing import Dict, List, Any, Optional, Set
from flask_socketio import emit, disconnect, join_room, leave_room
from flask import request

from utils.message_queue import MessageQueue, MessagePriority


class ClientInfo:
    """客户端信息"""
    
    def __init__(self, sid: str, user_agent: str = None):
        self.sid = sid
        self.user_agent = user_agent
        self.connect_time = time.time()
        self.last_ping = time.time()
        self.rooms: Set[str] = set()
        self.subscriptions: Set[str] = set()  # 订阅的事件类型
        self.is_active = True


class WebSocketHandler:
    """WebSocket事件处理器"""
    
    def __init__(self, socketio, logger=None):
        """
        初始化WebSocket处理器
        
        Args:
            socketio: SocketIO实例
            logger: 日志记录器
        """
        self.socketio = socketio
        self.logger = logger
        
        # 客户端连接管理
        self.clients: Dict[str, ClientInfo] = {}
        self.client_lock = threading.Lock()
        
        # 消息队列
        self.message_queue = MessageQueue(logger)
        
        # 房间管理
        self.rooms: Dict[str, Set[str]] = {}  # room_name -> set of client_ids
        
        # 事件统计
        self.stats = {
            "total_connections": 0,
            "current_connections": 0,
            "total_messages_sent": 0,
            "total_messages_received": 0,
            "total_errors": 0
        }
        
        # 心跳检测
        self.heartbeat_interval = 30  # 30秒
        self.heartbeat_timeout = 60   # 60秒超时
        self._heartbeat_thread = None
        self._running = False
        
        # 注册消息处理器
        self._register_message_handlers()
        
        # 注册SocketIO事件
        self._register_socketio_events()
    
    def _log(self, level: str, message: str):
        """记录日志"""
        if self.logger:
            getattr(self.logger, level.lower())(message)
        else:
            print(f"[{level.upper()}] {message}")
    
    def start(self):
        """启动WebSocket处理器"""
        if self._running:
            return
        
        self._running = True
        
        # 启动消息队列
        self.message_queue.start()
        
        # 启动心跳检测线程
        self._heartbeat_thread = threading.Thread(
            target=self._heartbeat_monitor,
            daemon=True
        )
        self._heartbeat_thread.start()
        
        self._log("info", "WebSocket处理器已启动")
    
    def stop(self):
        """停止WebSocket处理器"""
        self._running = False
        
        # 停止消息队列
        self.message_queue.stop()
        
        # 等待心跳线程结束
        if self._heartbeat_thread:
            self._heartbeat_thread.join(timeout=5)
        
        self._log("info", "WebSocket处理器已停止")
    
    def _register_message_handlers(self):
        """注册消息处理器"""
        
        def handle_broadcast_message(message):
            """处理广播消息"""
            try:
                if message.target_clients:
                    # 发送给指定客户端
                    for client_id in message.target_clients:
                        if client_id in self.clients:
                            self.socketio.emit(
                                message.event,
                                message.data,
                                room=client_id
                            )
                else:
                    # 广播给所有客户端
                    self.socketio.emit(message.event, message.data)
                
                self.stats["total_messages_sent"] += 1
                return True
                
            except Exception as e:
                self._log("error", f"广播消息失败: {e}")
                self.stats["total_errors"] += 1
                return False
        
        def handle_room_message(message):
            """处理房间消息"""
            try:
                room_name = message.data.get("room")
                event_name = message.data.get("event", message.event)
                event_data = message.data.get("data")

                if room_name:
                    self.socketio.emit(
                        event_name,
                        event_data,
                        room=room_name
                    )
                    self.stats["total_messages_sent"] += 1
                    return True

                return False

            except Exception as e:
                self._log("error", f"房间消息发送失败: {e}")
                self.stats["total_errors"] += 1
                return False
        
        # 注册处理器
        self.message_queue.add_message_handler("broadcast", handle_broadcast_message)
        self.message_queue.add_message_handler("room_message", handle_room_message)
        self.message_queue.add_message_handler("compile_log", handle_broadcast_message)
        self.message_queue.add_message_handler("compile_progress", handle_broadcast_message)
        self.message_queue.add_message_handler("compile_status", handle_broadcast_message)
        self.message_queue.add_message_handler("compile_complete", handle_broadcast_message)
        self.message_queue.add_message_handler("compile_error", handle_broadcast_message)
        self.message_queue.add_message_handler("clone_progress", handle_broadcast_message)
        self.message_queue.add_message_handler("clone_complete", handle_broadcast_message)
        self.message_queue.add_message_handler("clone_error", handle_broadcast_message)
        self.message_queue.add_message_handler("feeds_log", handle_broadcast_message)
        # 添加通用测试事件处理器
        self.message_queue.add_message_handler("test_broadcast", handle_broadcast_message)
    
    def _register_socketio_events(self):
        """注册SocketIO事件"""
        
        @self.socketio.on('connect')
        def handle_connect():
            """客户端连接事件"""
            sid = request.sid
            user_agent = request.headers.get('User-Agent', 'Unknown')
            
            # 创建客户端信息
            client_info = ClientInfo(sid, user_agent)
            
            with self.client_lock:
                self.clients[sid] = client_info
                self.stats["total_connections"] += 1
                self.stats["current_connections"] = len(self.clients)
            
            self._log("info", f"客户端连接: {sid} ({user_agent})")
            
            # 发送连接确认
            emit('connected', {
                'message': '已连接到OpenWrt编译器后端',
                'server_time': datetime.now().isoformat(),
                'client_id': sid
            })
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """客户端断开连接事件"""
            sid = request.sid
            
            with self.client_lock:
                if sid in self.clients:
                    client_info = self.clients[sid]
                    
                    # 离开所有房间
                    for room in client_info.rooms:
                        self._leave_room_internal(sid, room)
                    
                    del self.clients[sid]
                    self.stats["current_connections"] = len(self.clients)
            
            self._log("info", f"客户端断开连接: {sid}")
        
        @self.socketio.on('ping')
        def handle_ping():
            """心跳检测"""
            sid = request.sid
            
            with self.client_lock:
                if sid in self.clients:
                    self.clients[sid].last_ping = time.time()
            
            emit('pong', {
                'timestamp': datetime.now().isoformat(),
                'server_time': time.time()
            })
        
        @self.socketio.on('join_room')
        def handle_join_room(data):
            """加入房间"""
            sid = request.sid
            room_name = data.get('room')
            
            if room_name:
                self._join_room_internal(sid, room_name)
                emit('room_joined', {
                    'room': room_name,
                    'message': f'已加入房间: {room_name}'
                })
        
        @self.socketio.on('leave_room')
        def handle_leave_room(data):
            """离开房间"""
            sid = request.sid
            room_name = data.get('room')
            
            if room_name:
                self._leave_room_internal(sid, room_name)
                emit('room_left', {
                    'room': room_name,
                    'message': f'已离开房间: {room_name}'
                })
        
        @self.socketio.on('subscribe')
        def handle_subscribe(data):
            """订阅事件"""
            sid = request.sid
            events = data.get('events', [])
            
            with self.client_lock:
                if sid in self.clients:
                    for event in events:
                        self.clients[sid].subscriptions.add(event)
            
            emit('subscribed', {
                'events': events,
                'message': f'已订阅 {len(events)} 个事件'
            })
        
        @self.socketio.on('unsubscribe')
        def handle_unsubscribe(data):
            """取消订阅事件"""
            sid = request.sid
            events = data.get('events', [])
            
            with self.client_lock:
                if sid in self.clients:
                    for event in events:
                        self.clients[sid].subscriptions.discard(event)
            
            emit('unsubscribed', {
                'events': events,
                'message': f'已取消订阅 {len(events)} 个事件'
            })
        
        @self.socketio.on('get_status')
        def handle_get_status():
            """获取服务器状态"""
            emit('status', {
                'server_time': datetime.now().isoformat(),
                'uptime': time.time() - (self.clients.get(request.sid, ClientInfo(request.sid)).connect_time),
                'stats': self.get_stats(),
                'message_queue_stats': self.message_queue.get_stats()
            })
    
    def _join_room_internal(self, sid: str, room_name: str):
        """内部加入房间方法"""
        join_room(room_name, sid=sid)
        
        with self.client_lock:
            if sid in self.clients:
                self.clients[sid].rooms.add(room_name)
            
            if room_name not in self.rooms:
                self.rooms[room_name] = set()
            self.rooms[room_name].add(sid)
        
        self._log("debug", f"客户端 {sid} 加入房间 {room_name}")
    
    def _leave_room_internal(self, sid: str, room_name: str):
        """内部离开房间方法"""
        leave_room(room_name, sid=sid)
        
        with self.client_lock:
            if sid in self.clients:
                self.clients[sid].rooms.discard(room_name)
            
            if room_name in self.rooms:
                self.rooms[room_name].discard(sid)
                if not self.rooms[room_name]:
                    del self.rooms[room_name]
        
        self._log("debug", f"客户端 {sid} 离开房间 {room_name}")
    
    def _heartbeat_monitor(self):
        """心跳监控线程"""
        while self._running:
            try:
                current_time = time.time()
                disconnected_clients = []
                
                with self.client_lock:
                    for sid, client_info in self.clients.items():
                        if current_time - client_info.last_ping > self.heartbeat_timeout:
                            disconnected_clients.append(sid)
                            client_info.is_active = False
                
                # 断开超时的客户端
                for sid in disconnected_clients:
                    self._log("warning", f"客户端心跳超时，断开连接: {sid}")
                    self.socketio.disconnect(sid)
                
                time.sleep(self.heartbeat_interval)
                
            except Exception as e:
                self._log("error", f"心跳监控错误: {e}")
                time.sleep(5)

    def broadcast_message(self, event: str, data: Any,
                         priority: MessagePriority = MessagePriority.NORMAL,
                         target_clients: Optional[List[str]] = None):
        """
        广播消息给客户端

        Args:
            event: 事件名称
            data: 消息数据
            priority: 消息优先级
            target_clients: 目标客户端列表
        """
        self.message_queue.add_message(
            event=event,
            data=data,
            priority=priority,
            target_clients=target_clients
        )

    def send_to_room(self, room: str, event: str, data: Any,
                    priority: MessagePriority = MessagePriority.NORMAL):
        """
        发送消息到指定房间

        Args:
            room: 房间名称
            event: 事件名称
            data: 消息数据
            priority: 消息优先级
        """
        self.message_queue.add_message(
            event="room_message",
            data={"room": room, "event": event, "data": data},
            priority=priority
        )

    def send_compile_log(self, task_id: str, line: str, progress: float = None):
        """
        发送编译日志

        Args:
            task_id: 任务ID
            line: 日志行
            progress: 编译进度
        """
        log_data = {
            "task_id": task_id,
            "line": line,
            "timestamp": datetime.now().isoformat()
        }

        if progress is not None:
            log_data["progress"] = progress

        self.broadcast_message(
            event="compile_log",
            data=log_data,
            priority=MessagePriority.HIGH
        )

    def send_compile_progress(self, task_id: str, progress: float,
                            status: str = None, message: str = None):
        """
        发送编译进度

        Args:
            task_id: 任务ID
            progress: 进度百分比
            status: 状态信息
            message: 消息
        """
        progress_data = {
            "task_id": task_id,
            "progress": progress,
            "timestamp": datetime.now().isoformat()
        }

        if status:
            progress_data["status"] = status

        if message:
            progress_data["message"] = message

        self.broadcast_message(
            event="compile_progress",
            data=progress_data,
            priority=MessagePriority.HIGH
        )

    def send_compile_status(self, task_id: str, status: str,
                          progress: float = None, error: str = None):
        """
        发送编译状态

        Args:
            task_id: 任务ID
            status: 编译状态
            progress: 进度百分比
            error: 错误信息
        """
        status_data = {
            "task_id": task_id,
            "status": status,
            "timestamp": datetime.now().isoformat()
        }

        if progress is not None:
            status_data["progress"] = progress

        if error:
            status_data["error"] = error

        self.broadcast_message(
            event="compile_status",
            data=status_data,
            priority=MessagePriority.HIGH
        )

    def send_compile_complete(self, task_id: str, firmware_files: List[Dict] = None):
        """
        发送编译完成通知

        Args:
            task_id: 任务ID
            firmware_files: 固件文件列表
        """
        complete_data = {
            "task_id": task_id,
            "timestamp": datetime.now().isoformat(),
            "message": "编译完成"
        }

        if firmware_files:
            complete_data["firmware_files"] = firmware_files

        self.broadcast_message(
            event="compile_complete",
            data=complete_data,
            priority=MessagePriority.CRITICAL
        )

    def send_compile_error(self, task_id: str, error: str, details: str = None):
        """
        发送编译错误通知

        Args:
            task_id: 任务ID
            error: 错误信息
            details: 详细信息
        """
        error_data = {
            "task_id": task_id,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }

        if details:
            error_data["details"] = details

        self.broadcast_message(
            event="compile_error",
            data=error_data,
            priority=MessagePriority.CRITICAL
        )

    def send_clone_progress(self, progress: float, message: str = None):
        """
        发送克隆进度

        Args:
            progress: 进度百分比
            message: 消息
        """
        progress_data = {
            "progress": progress,
            "timestamp": datetime.now().isoformat()
        }

        if message:
            progress_data["message"] = message

        self.broadcast_message(
            event="clone_progress",
            data=progress_data,
            priority=MessagePriority.HIGH
        )

    def send_feeds_log(self, process_id: str, line: str):
        """
        发送feeds日志

        Args:
            process_id: 进程ID
            line: 日志行
        """
        log_data = {
            "process_id": process_id,
            "line": line,
            "timestamp": datetime.now().isoformat()
        }

        self.broadcast_message(
            event="feeds_log",
            data=log_data,
            priority=MessagePriority.NORMAL
        )

    def get_connected_clients(self) -> List[Dict[str, Any]]:
        """
        获取连接的客户端列表

        Returns:
            list: 客户端信息列表
        """
        with self.client_lock:
            clients = []
            for sid, client_info in self.clients.items():
                clients.append({
                    "sid": sid,
                    "user_agent": client_info.user_agent,
                    "connect_time": client_info.connect_time,
                    "last_ping": client_info.last_ping,
                    "rooms": list(client_info.rooms),
                    "subscriptions": list(client_info.subscriptions),
                    "is_active": client_info.is_active
                })

            return clients

    def get_room_info(self) -> Dict[str, List[str]]:
        """
        获取房间信息

        Returns:
            dict: 房间信息
        """
        with self.client_lock:
            return {
                room: list(clients)
                for room, clients in self.rooms.items()
            }

    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息

        Returns:
            dict: 统计信息
        """
        with self.client_lock:
            stats = self.stats.copy()
            stats["active_clients"] = sum(
                1 for client in self.clients.values()
                if client.is_active
            )
            stats["total_rooms"] = len(self.rooms)

            return stats

    def disconnect_client(self, sid: str, reason: str = "Server disconnect"):
        """
        断开指定客户端

        Args:
            sid: 客户端ID
            reason: 断开原因
        """
        try:
            self.socketio.emit('disconnect_notice', {
                'reason': reason,
                'timestamp': datetime.now().isoformat()
            }, room=sid)

            self.socketio.disconnect(sid)
            self._log("info", f"主动断开客户端 {sid}: {reason}")

        except Exception as e:
            self._log("error", f"断开客户端失败 {sid}: {e}")

    def cleanup_inactive_clients(self):
        """清理非活跃客户端"""
        current_time = time.time()
        inactive_clients = []

        with self.client_lock:
            for sid, client_info in self.clients.items():
                if not client_info.is_active or \
                   current_time - client_info.last_ping > self.heartbeat_timeout * 2:
                    inactive_clients.append(sid)

        for sid in inactive_clients:
            self.disconnect_client(sid, "Inactive client cleanup")

        if inactive_clients:
            self._log("info", f"清理了 {len(inactive_clients)} 个非活跃客户端")
