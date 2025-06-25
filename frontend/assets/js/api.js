/**
 * API调用封装模块
 */

class APIClient {
    constructor(baseUrl = 'http://127.0.0.1:5000/api') {
        this.baseUrl = baseUrl;
        this.timeout = 30000; // 30秒超时
        this.retryAttempts = 3;
        this.retryDelay = 1000; // 1秒重试延迟
    }
    
    /**
     * 通用API调用方法
     */
    async call(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const defaultOptions = {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
            timeout: this.timeout,
        };
        
        const finalOptions = { ...defaultOptions, ...options };
        
        // 添加超时控制
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.timeout);
        finalOptions.signal = controller.signal;
        
        let lastError;
        
        // 重试机制
        for (let attempt = 1; attempt <= this.retryAttempts; attempt++) {
            try {
                const response = await fetch(url, finalOptions);
                clearTimeout(timeoutId);
                
                if (!response.ok) {
                    const errorData = await response.json().catch(() => ({}));
                    throw new APIError(
                        errorData.message || `HTTP ${response.status}`,
                        response.status,
                        errorData
                    );
                }
                
                const data = await response.json();
                return data;
                
            } catch (error) {
                lastError = error;
                
                // 如果是最后一次尝试或者是不可重试的错误，直接抛出
                if (attempt === this.retryAttempts || !this.shouldRetry(error)) {
                    clearTimeout(timeoutId);
                    throw error;
                }
                
                // 等待后重试
                await this.delay(this.retryDelay * attempt);
            }
        }
        
        clearTimeout(timeoutId);
        throw lastError;
    }
    
    /**
     * 判断是否应该重试
     */
    shouldRetry(error) {
        // 网络错误或服务器错误可以重试
        if (error.name === 'AbortError') return false; // 超时不重试
        if (error instanceof APIError) {
            // 4xx客户端错误不重试，5xx服务器错误可以重试
            return error.status >= 500;
        }
        return true; // 网络错误等可以重试
    }
    
    /**
     * 延迟函数
     */
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    
    // 配置管理API
    async getConfigTemplates() {
        return this.call('/config/templates');
    }
    
    async applyTemplate(templateId, configName) {
        return this.call('/config/apply-template', {
            method: 'POST',
            body: JSON.stringify({
                template_id: templateId,
                config_name: configName
            })
        });
    }
    
    async getConfigs() {
        return this.call('/configs');
    }
    
    async getConfig(configName) {
        return this.call(`/config/${configName}`);
    }
    
    async updateConfig(configName, configData, metadata) {
        return this.call(`/config/${configName}`, {
            method: 'PUT',
            body: JSON.stringify({
                config_data: configData,
                metadata: metadata
            })
        });
    }
    
    async deleteConfig(configName) {
        return this.call(`/config/${configName}`, {
            method: 'DELETE'
        });
    }
    
    // 仓库管理API
    async cloneRepository(url, branch) {
        return this.call('/repository/clone', {
            method: 'POST',
            body: JSON.stringify({ url, branch })
        });
    }
    
    async updateFeeds() {
        return this.call('/repository/update-feeds', {
            method: 'POST'
        });
    }
    
    async installFeeds() {
        return this.call('/repository/install-feeds', {
            method: 'POST'
        });
    }
    
    async getRepositoryStatus() {
        return this.call('/repository/status');
    }
    
    // 编译管理API
    async startCompile(options) {
        return this.call('/compile/start', {
            method: 'POST',
            body: JSON.stringify(options)
        });
    }
    
    async stopCompile() {
        return this.call('/compile/stop', {
            method: 'POST'
        });
    }
    
    async getCompileStatus() {
        return this.call('/compile/status');
    }
    
    async getCompileLogs() {
        return this.call('/compile/logs');
    }
    
    // 文件管理API
    async getFirmwareFiles() {
        return this.call('/files/firmware');
    }
    
    async getConfigFiles() {
        return this.call('/files/configs');
    }
    
    async getStorageInfo() {
        return this.call('/files/storage');
    }
    
    async getFileInfo(type, filename) {
        return this.call(`/files/${type}/${filename}/info`);
    }
    
    async deleteFile(type, filename) {
        return this.call(`/files/${type}/${filename}`, {
            method: 'DELETE'
        });
    }
    
    async validateFile(type, filename, md5, sha256) {
        return this.call(`/files/${type}/${filename}/validate`, {
            method: 'POST',
            body: JSON.stringify({ md5, sha256 })
        });
    }
    
    async cleanupTempFiles() {
        return this.call('/files/cleanup', {
            method: 'POST'
        });
    }
    
    // 文件上传
    async uploadConfigFile(file, filename, overwrite = false) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('overwrite', overwrite.toString());
        
        const url = `${this.baseUrl}/files/configs/${filename}`;
        
        const response = await fetch(url, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new APIError(
                errorData.message || `HTTP ${response.status}`,
                response.status,
                errorData
            );
        }
        
        return response.json();
    }
    
    // WebSocket相关API
    async getWebSocketStats() {
        return this.call('/websocket/stats');
    }
    
    async getWebSocketClients() {
        return this.call('/websocket/clients');
    }
    
    async getWebSocketRooms() {
        return this.call('/websocket/rooms');
    }
    
    // 系统状态API
    async getSystemStatus() {
        return this.call('/status');
    }
    
    async getSystemInfo() {
        return this.call('/system/info');
    }
    
    // 健康检查
    async healthCheck() {
        try {
            const response = await this.call('/health');
            return { healthy: true, data: response };
        } catch (error) {
            return { healthy: false, error: error.message };
        }
    }
}

/**
 * API错误类
 */
class APIError extends Error {
    constructor(message, status, data) {
        super(message);
        this.name = 'APIError';
        this.status = status;
        this.data = data;
    }
}

/**
 * 网络状态监控
 */
class NetworkMonitor {
    constructor(apiClient) {
        this.apiClient = apiClient;
        this.isOnline = navigator.onLine;
        this.listeners = [];
        
        this.init();
    }
    
    init() {
        // 监听网络状态变化
        window.addEventListener('online', () => {
            this.isOnline = true;
            this.notifyListeners('online');
        });
        
        window.addEventListener('offline', () => {
            this.isOnline = false;
            this.notifyListeners('offline');
        });
        
        // 定期健康检查
        this.startHealthCheck();
    }
    
    startHealthCheck() {
        setInterval(async () => {
            if (this.isOnline) {
                const health = await this.apiClient.healthCheck();
                this.notifyListeners('health', health);
            }
        }, 30000); // 每30秒检查一次
    }
    
    addListener(callback) {
        this.listeners.push(callback);
    }
    
    removeListener(callback) {
        const index = this.listeners.indexOf(callback);
        if (index > -1) {
            this.listeners.splice(index, 1);
        }
    }
    
    notifyListeners(event, data) {
        this.listeners.forEach(callback => {
            try {
                callback(event, data);
            } catch (error) {
                console.error('Network monitor listener error:', error);
            }
        });
    }
}

// 导出类和实例
window.APIClient = APIClient;
window.APIError = APIError;
window.NetworkMonitor = NetworkMonitor;

// 创建默认API客户端实例
window.apiClient = new APIClient();
window.networkMonitor = new NetworkMonitor(window.apiClient);
