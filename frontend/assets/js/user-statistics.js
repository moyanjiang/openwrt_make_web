/**
 * 用户统计组件
 * 显示用户编译统计、时间统计等信息
 */

class UserStatistics {
    constructor(apiClient, userManager) {
        this.api = apiClient;
        this.userManager = userManager;
        this.refreshTimer = null;
        
        this.init();
    }
    
    init() {
        this.loadUserStatistics();
        this.startAutoRefresh();
    }
    
    async loadUserStatistics() {
        try {
            const currentUser = this.userManager.getCurrentUser();
            if (!currentUser) {
                return;
            }
            
            const response = await this.api.get(`/users/${currentUser.username}/statistics`);
            
            if (response.success) {
                this.displayStatistics(response.data);
            } else {
                this.showError('加载统计信息失败: ' + response.message);
            }
        } catch (error) {
            console.error('加载用户统计失败:', error);
            this.showError('无法加载统计信息');
        }
    }
    
    displayStatistics(stats) {
        const statsContainer = document.getElementById('user-stats');
        if (!statsContainer) return;
        
        statsContainer.innerHTML = `
            <div class="stats-overview">
                <div class="stat-card">
                    <div class="stat-icon">🏗️</div>
                    <div class="stat-content">
                        <div class="stat-number">${stats.total_compiles || 0}</div>
                        <div class="stat-label">总编译次数</div>
                    </div>
                </div>
                
                <div class="stat-card">
                    <div class="stat-icon">✅</div>
                    <div class="stat-content">
                        <div class="stat-number">${stats.successful_compiles || 0}</div>
                        <div class="stat-label">成功编译</div>
                    </div>
                </div>
                
                <div class="stat-card">
                    <div class="stat-icon">❌</div>
                    <div class="stat-content">
                        <div class="stat-number">${stats.failed_compiles || 0}</div>
                        <div class="stat-label">失败编译</div>
                    </div>
                </div>
                
                <div class="stat-card">
                    <div class="stat-icon">📊</div>
                    <div class="stat-content">
                        <div class="stat-number">${stats.success_rate || 0}%</div>
                        <div class="stat-label">成功率</div>
                    </div>
                </div>
            </div>
            
            <div class="stats-details">
                <div class="detail-section">
                    <h4><i class="fas fa-clock"></i> 时间统计</h4>
                    <div class="detail-grid">
                        <div class="detail-item">
                            <span class="detail-label">总编译时间:</span>
                            <span class="detail-value">${stats.total_compile_time_formatted || '0分钟'}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">平均编译时间:</span>
                            <span class="detail-value">${stats.average_compile_time_formatted || '0分钟'}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">登录次数:</span>
                            <span class="detail-value">${stats.login_count || 0}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">最后编译:</span>
                            <span class="detail-value">${this.formatDateTime(stats.last_compile_time) || '从未编译'}</span>
                        </div>
                    </div>
                </div>
                
                <div class="detail-section">
                    <h4><i class="fas fa-history"></i> 最近编译历史</h4>
                    <div class="compile-history" id="compile-history">
                        <!-- 编译历史将在这里显示 -->
                    </div>
                </div>
            </div>
        `;
        
        // 加载编译历史
        this.loadCompileHistory();
    }
    
    async loadCompileHistory() {
        try {
            const currentUser = this.userManager.getCurrentUser();
            if (!currentUser) {
                return;
            }
            
            const response = await this.api.get(`/users/${currentUser.username}/compile-history?limit=5`);
            
            if (response.success) {
                this.displayCompileHistory(response.data);
            }
        } catch (error) {
            console.error('加载编译历史失败:', error);
        }
    }
    
    displayCompileHistory(history) {
        const historyContainer = document.getElementById('compile-history');
        if (!historyContainer || !history || history.length === 0) {
            if (historyContainer) {
                historyContainer.innerHTML = '<div class="no-history">暂无编译历史</div>';
            }
            return;
        }
        
        historyContainer.innerHTML = history.map(session => {
            const statusIcon = session.status === 'success' ? '✅' : 
                              session.status === 'failed' ? '❌' : '⏳';
            const statusText = session.status === 'success' ? '成功' : 
                              session.status === 'failed' ? '失败' : '进行中';
            const statusClass = session.status === 'success' ? 'success' : 
                               session.status === 'failed' ? 'failed' : 'running';
            
            return `
                <div class="history-item">
                    <div class="history-header">
                        <span class="history-status ${statusClass}">
                            ${statusIcon} ${statusText}
                        </span>
                        <span class="history-time">${this.formatDateTime(session.start_time)}</span>
                    </div>
                    <div class="history-details">
                        <div class="history-device">${session.config?.device_name || '未知设备'}</div>
                        <div class="history-duration">${this.formatDuration(session.duration)}</div>
                    </div>
                </div>
            `;
        }).join('');
    }
    
    formatDateTime(dateTimeStr) {
        if (!dateTimeStr) return '';
        
        try {
            const date = new Date(dateTimeStr);
            const now = new Date();
            const diffMs = now - date;
            const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
            
            if (diffDays === 0) {
                return date.toLocaleTimeString('zh-CN', { 
                    hour: '2-digit', 
                    minute: '2-digit' 
                });
            } else if (diffDays === 1) {
                return '昨天 ' + date.toLocaleTimeString('zh-CN', { 
                    hour: '2-digit', 
                    minute: '2-digit' 
                });
            } else if (diffDays < 7) {
                return `${diffDays}天前`;
            } else {
                return date.toLocaleDateString('zh-CN', {
                    month: '2-digit',
                    day: '2-digit',
                    hour: '2-digit',
                    minute: '2-digit'
                });
            }
        } catch (error) {
            return dateTimeStr;
        }
    }
    
    formatDuration(seconds) {
        if (!seconds || seconds === 0) return '0秒';
        
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = seconds % 60;
        
        if (hours > 0) {
            return `${hours}小时${minutes}分钟`;
        } else if (minutes > 0) {
            return `${minutes}分钟${secs}秒`;
        } else {
            return `${secs}秒`;
        }
    }
    
    startAutoRefresh() {
        // 每5分钟自动刷新统计信息
        this.refreshTimer = setInterval(() => {
            this.loadUserStatistics();
        }, 5 * 60 * 1000);
    }
    
    stopAutoRefresh() {
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
            this.refreshTimer = null;
        }
    }
    
    showError(message) {
        const statsContainer = document.getElementById('user-stats');
        if (statsContainer) {
            statsContainer.innerHTML = `
                <div class="stats-error">
                    <div class="error-icon">❌</div>
                    <div class="error-message">${message}</div>
                    <button class="retry-btn" onclick="this.loadUserStatistics()">
                        <i class="fas fa-redo"></i> 重试
                    </button>
                </div>
            `;
        }
    }
    
    // 编译开始时更新统计
    onCompileStarted(taskInfo) {
        // 可以在这里添加实时更新逻辑
        console.log('编译开始:', taskInfo);
    }
    
    // 编译完成时更新统计
    onCompileCompleted(taskInfo) {
        // 刷新统计信息
        setTimeout(() => {
            this.loadUserStatistics();
        }, 1000);
    }
    
    // 编译失败时更新统计
    onCompileFailed(taskInfo) {
        // 刷新统计信息
        setTimeout(() => {
            this.loadUserStatistics();
        }, 1000);
    }
    
    // 销毁组件
    destroy() {
        this.stopAutoRefresh();
    }
}
