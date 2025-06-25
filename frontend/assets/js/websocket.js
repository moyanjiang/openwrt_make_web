/**
 * WebSocket管理器
 */

class WebSocketManager {
    constructor(url, app) {
        this.url = url;
        this.app = app;
        this.socket = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 10;
        this.reconnectInterval = 5000;
        this.pingInterval = null;
        this.isConnecting = false;
        this.isManualDisconnect = false;
    }
    
    /**
     * 连接WebSocket
     */
    connect() {
        if (this.isConnecting || (this.socket && this.socket.connected)) {
            return;
        }
        
        this.isConnecting = true;
        this.isManualDisconnect = false;
        
        try {
            // 使用Socket.IO客户端
            this.socket = io(this.url, {
                transports: ['websocket', 'polling'],
                timeout: 10000,
                forceNew: true
            });
            
            this.setupEventListeners();
            
        } catch (error) {
            console.error('WebSocket connection failed:', error);
            this.isConnecting = false;
            this.scheduleReconnect();
        }
    }
    
    /**
     * 断开WebSocket连接
     */
    disconnect() {
        this.isManualDisconnect = true;
        
        if (this.pingInterval) {
            clearInterval(this.pingInterval);
            this.pingInterval = null;
        }
        
        if (this.socket) {
            this.socket.disconnect();
            this.socket = null;
        }
        
        this.app.updateConnectionStatus(false);
    }
    
    /**
     * 设置事件监听器
     */
    setupEventListeners() {
        // 连接成功
        this.socket.on('connect', () => {
            console.log('WebSocket connected');
            this.isConnecting = false;
            this.reconnectAttempts = 0;
            this.app.updateConnectionStatus(true);
            this.app.showNotification('成功', 'WebSocket连接已建立', 'success', 3000);
            
            // 开始心跳检测
            this.startPing();
            
            // 订阅编译相关事件
            this.socket.emit('subscribe', {
                events: ['compile_log', 'compile_progress', 'compile_status', 'compile_complete', 'compile_error']
            });
        });
        
        // 连接断开
        this.socket.on('disconnect', (reason) => {
            console.log('WebSocket disconnected:', reason);
            this.isConnecting = false;
            this.app.updateConnectionStatus(false);
            
            if (this.pingInterval) {
                clearInterval(this.pingInterval);
                this.pingInterval = null;
            }
            
            if (!this.isManualDisconnect) {
                this.app.showNotification('警告', 'WebSocket连接断开', 'warning', 3000);
                this.scheduleReconnect();
            }
        });
        
        // 连接错误
        this.socket.on('connect_error', (error) => {
            console.error('WebSocket connection error:', error);
            this.isConnecting = false;
            this.app.updateConnectionStatus(false);
            
            if (!this.isManualDisconnect) {
                this.scheduleReconnect();
            }
        });
        
        // 连接确认
        this.socket.on('connected', (data) => {
            console.log('Server connection confirmed:', data);
            this.app.addLogEntry('info', `服务器连接确认: ${data.message}`);
        });
        
        // 心跳响应
        this.socket.on('pong', (data) => {
            console.log('Pong received:', data);
        });
        
        // 编译日志
        this.socket.on('compile_log', (data) => {
            this.handleCompileLog(data);
        });
        
        // 编译进度
        this.socket.on('compile_progress', (data) => {
            this.handleCompileProgress(data);
        });
        
        // 编译状态
        this.socket.on('compile_status', (data) => {
            this.handleCompileStatus(data);
        });
        
        // 编译完成
        this.socket.on('compile_complete', (data) => {
            this.handleCompileComplete(data);
        });
        
        // 编译错误
        this.socket.on('compile_error', (data) => {
            this.handleCompileError(data);
        });
        
        // 克隆进度
        this.socket.on('clone_progress', (data) => {
            this.handleCloneProgress(data);
        });
        
        // 克隆完成
        this.socket.on('clone_complete', (data) => {
            this.handleCloneComplete(data);
        });
        
        // 克隆错误
        this.socket.on('clone_error', (data) => {
            this.handleCloneError(data);
        });
        
        // Feeds日志
        this.socket.on('feeds_log', (data) => {
            this.handleFeedsLog(data);
        });
    }
    
    /**
     * 开始心跳检测
     */
    startPing() {
        this.pingInterval = setInterval(() => {
            if (this.socket && this.socket.connected) {
                this.socket.emit('ping');
            }
        }, 30000); // 每30秒发送一次心跳
    }
    
    /**
     * 安排重连
     */
    scheduleReconnect() {
        if (this.isManualDisconnect || this.reconnectAttempts >= this.maxReconnectAttempts) {
            if (this.reconnectAttempts >= this.maxReconnectAttempts) {
                this.app.showNotification('错误', 'WebSocket重连次数超限，请刷新页面', 'error');
            }
            return;
        }
        
        this.reconnectAttempts++;
        const delay = Math.min(this.reconnectInterval * this.reconnectAttempts, 30000);
        
        console.log(`Scheduling reconnect attempt ${this.reconnectAttempts} in ${delay}ms`);
        
        setTimeout(() => {
            if (!this.isManualDisconnect) {
                this.connect();
            }
        }, delay);
    }
    
    /**
     * 处理编译日志
     */
    handleCompileLog(data) {
        const level = this.detectLogLevel(data.line);
        this.app.addLogEntry(level, data.line, data.timestamp);
        
        // 如果有进度信息，更新进度
        if (data.progress !== undefined) {
            this.app.updateCompileStatus('编译中', data.progress);
        }
    }
    
    /**
     * 处理编译进度
     */
    handleCompileProgress(data) {
        this.app.updateCompileStatus(data.status || '编译中', data.progress);
        
        if (data.message) {
            this.app.addLogEntry('info', data.message, data.timestamp);
        }
    }
    
    /**
     * 处理编译状态
     */
    handleCompileStatus(data) {
        this.app.updateCompileStatus(data.status, data.progress || 0);
        
        if (data.error) {
            this.app.addLogEntry('error', data.error, data.timestamp);
        }
    }
    
    /**
     * 处理编译完成
     */
    handleCompileComplete(data) {
        this.app.updateCompileStatus('编译完成', 100);
        this.app.addLogEntry('success', '编译完成！', data.timestamp);
        this.app.showNotification('成功', '编译完成', 'success');
        this.app.resetCompileState();
        
        // 刷新文件列表
        this.app.loadFilesList();
    }
    
    /**
     * 处理编译错误
     */
    handleCompileError(data) {
        this.app.updateCompileStatus('编译失败', 0);
        this.app.addLogEntry('error', `编译错误: ${data.error}`, data.timestamp);
        this.app.showNotification('错误', `编译失败: ${data.error}`, 'error');
        this.app.resetCompileState();
    }
    
    /**
     * 处理克隆进度
     */
    handleCloneProgress(data) {
        this.app.updateCloneProgress(data.progress, data.message || '克隆中...');
        this.app.addLogEntry('info', data.message || `克隆进度: ${data.progress}%`, data.timestamp);
    }
    
    /**
     * 处理克隆完成
     */
    handleCloneComplete(data) {
        this.app.updateCloneProgress(100, '克隆完成');
        this.app.addLogEntry('success', '仓库克隆完成', data.timestamp);
        this.app.showNotification('成功', '仓库克隆完成', 'success');
        this.app.resetCloneState();
    }
    
    /**
     * 处理克隆错误
     */
    handleCloneError(data) {
        this.app.addLogEntry('error', `克隆错误: ${data.error}`, data.timestamp);
        this.app.showNotification('错误', `克隆失败: ${data.error}`, 'error');
        this.app.resetCloneState();
    }
    
    /**
     * 处理Feeds日志
     */
    handleFeedsLog(data) {
        const level = this.detectLogLevel(data.line);
        this.app.addLogEntry(level, data.line, data.timestamp);
    }
    
    /**
     * 检测日志级别
     */
    detectLogLevel(message) {
        const lowerMessage = message.toLowerCase();
        
        if (lowerMessage.includes('error') || lowerMessage.includes('failed') || lowerMessage.includes('fatal')) {
            return 'error';
        } else if (lowerMessage.includes('warning') || lowerMessage.includes('warn')) {
            return 'warning';
        } else if (lowerMessage.includes('success') || lowerMessage.includes('complete') || lowerMessage.includes('done')) {
            return 'success';
        } else {
            return 'info';
        }
    }
    
    /**
     * 发送消息
     */
    emit(event, data) {
        if (this.socket && this.socket.connected) {
            this.socket.emit(event, data);
        } else {
            console.warn('WebSocket not connected, cannot send message:', event, data);
        }
    }
    
    /**
     * 获取连接状态
     */
    isConnected() {
        return this.socket && this.socket.connected;
    }
}
