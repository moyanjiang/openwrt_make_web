/**
 * 仓库管理组件
 * 处理Git仓库的克隆、更新、重构等操作
 */

class RepositoryManager {
    constructor(apiClient, userManager) {
        this.api = apiClient;
        this.userManager = userManager;
        this.currentOperation = null;
        this.operationTimer = null;
        
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.loadRepositoryStatus();
        
        // 定期检查仓库状态
        this.startStatusPolling();
    }
    
    bindEvents() {
        // 克隆按钮
        document.getElementById('clone-btn').addEventListener('click', () => {
            this.cloneRepository();
        });
        
        // 更新按钮
        document.getElementById('update-repo-btn').addEventListener('click', () => {
            this.updateRepository();
        });
        
        // 重构按钮
        document.getElementById('rebuild-repo-btn').addEventListener('click', () => {
            this.rebuildRepository();
        });
        
        // 取消操作按钮
        document.getElementById('cancel-repo-operation').addEventListener('click', () => {
            this.cancelOperation();
        });
    }
    
    async loadRepositoryStatus() {
        try {
            const response = await this.api.get('/repository/status');
            
            if (response.success) {
                this.updateStatusDisplay(response.data);
            } else {
                this.showStatusError(response.message);
            }
        } catch (error) {
            console.error('加载仓库状态失败:', error);
            this.showStatusError('无法连接到服务器');
        }
    }
    
    updateStatusDisplay(repoInfo) {
        const statusCard = document.querySelector('.repository-status .status-card');
        const statusIcon = statusCard.querySelector('.status-icon');
        const statusText = statusCard.querySelector('.status-text');
        const statusDetails = document.getElementById('repo-details');
        
        if (repoInfo.exists) {
            // 仓库存在
            statusIcon.textContent = '✅';
            statusText.textContent = '仓库已就绪';
            
            // 显示详细信息
            statusDetails.innerHTML = `
                <div class="repo-info">
                    <div class="info-item">
                        <span class="label">分支:</span>
                        <span class="value">${repoInfo.branch || 'unknown'}</span>
                    </div>
                    <div class="info-item">
                        <span class="label">最后提交:</span>
                        <span class="value">${repoInfo.last_commit?.hash || 'unknown'}</span>
                    </div>
                    <div class="info-item">
                        <span class="label">提交时间:</span>
                        <span class="value">${repoInfo.last_commit?.date || 'unknown'}</span>
                    </div>
                    <div class="info-item">
                        <span class="label">作者:</span>
                        <span class="value">${repoInfo.last_commit?.author || 'unknown'}</span>
                    </div>
                </div>
            `;
            statusDetails.style.display = 'block';
            
            // 启用操作按钮
            this.enableButtons(['update-repo-btn', 'rebuild-repo-btn']);
            
        } else {
            // 仓库不存在
            statusIcon.textContent = '📦';
            statusText.textContent = '仓库未克隆';
            statusDetails.style.display = 'none';
            
            // 只启用克隆按钮
            this.enableButtons(['clone-btn']);
            this.disableButtons(['update-repo-btn', 'rebuild-repo-btn']);
        }
        
        // 检查是否有正在进行的操作
        if (repoInfo.is_busy) {
            this.showOperationInProgress(repoInfo.current_operation);
        } else {
            this.hideOperationProgress();
        }
    }
    
    showStatusError(message) {
        const statusCard = document.querySelector('.repository-status .status-card');
        const statusIcon = statusCard.querySelector('.status-icon');
        const statusText = statusCard.querySelector('.status-text');
        
        statusIcon.textContent = '❌';
        statusText.textContent = `状态检查失败: ${message}`;
        
        // 禁用所有操作按钮
        this.disableButtons(['clone-btn', 'update-repo-btn', 'rebuild-repo-btn']);
    }
    
    async cloneRepository() {
        const enableIstore = document.getElementById('enable-istore').checked;
        
        if (!confirm('确定要克隆源码仓库吗？这可能需要较长时间。')) {
            return;
        }
        
        try {
            this.showOperationInProgress('cloning');
            
            const response = await this.api.post('/repository/clone', {
                force_rebuild: false,
                enable_istore: enableIstore
            });
            
            if (response.success) {
                this.showSuccess('源码克隆成功');
                this.loadRepositoryStatus();
            } else {
                this.showError('克隆失败: ' + response.message);
                this.hideOperationProgress();
            }
        } catch (error) {
            console.error('克隆仓库失败:', error);
            this.showError('克隆时发生错误');
            this.hideOperationProgress();
        }
    }
    
    async updateRepository() {
        const enableIstore = document.getElementById('enable-istore').checked;
        
        if (!confirm('确定要更新仓库吗？')) {
            return;
        }
        
        try {
            this.showOperationInProgress('updating');
            
            const response = await this.api.post('/repository/update', {
                enable_istore: enableIstore
            });
            
            if (response.success) {
                this.showSuccess('仓库更新成功');
                this.loadRepositoryStatus();
            } else {
                this.showError('更新失败: ' + response.message);
                this.hideOperationProgress();
            }
        } catch (error) {
            console.error('更新仓库失败:', error);
            this.showError('更新时发生错误');
            this.hideOperationProgress();
        }
    }
    
    async rebuildRepository() {
        const enableIstore = document.getElementById('enable-istore').checked;
        
        if (!confirm('确定要重构仓库吗？这将删除现有仓库并重新克隆，可能需要较长时间。')) {
            return;
        }
        
        try {
            this.showOperationInProgress('rebuilding');
            
            const response = await this.api.post('/repository/rebuild', {
                enable_istore: enableIstore
            });
            
            if (response.success) {
                this.showSuccess('仓库重构成功');
                this.loadRepositoryStatus();
            } else {
                this.showError('重构失败: ' + response.message);
                this.hideOperationProgress();
            }
        } catch (error) {
            console.error('重构仓库失败:', error);
            this.showError('重构时发生错误');
            this.hideOperationProgress();
        }
    }
    
    async cancelOperation() {
        if (!confirm('确定要取消当前操作吗？')) {
            return;
        }
        
        try {
            const response = await this.api.post('/repository/cancel');
            
            if (response.success) {
                this.showSuccess('操作已取消');
                this.hideOperationProgress();
                this.loadRepositoryStatus();
            } else {
                this.showError('取消操作失败: ' + response.message);
            }
        } catch (error) {
            console.error('取消操作失败:', error);
            this.showError('取消操作时发生错误');
        }
    }
    
    showOperationInProgress(operation) {
        this.currentOperation = operation;
        
        const progressContainer = document.getElementById('repo-progress');
        const progressTitle = progressContainer.querySelector('.progress-title');
        const progressText = document.getElementById('repo-progress-text');
        
        // 设置操作标题
        const operationNames = {
            'cloning': '正在克隆源码...',
            'updating': '正在更新仓库...',
            'rebuilding': '正在重构仓库...'
        };
        
        progressTitle.textContent = operationNames[operation] || '正在处理...';
        progressText.textContent = '准备中...';
        
        // 显示进度界面
        progressContainer.style.display = 'block';
        
        // 禁用操作按钮
        this.disableButtons(['clone-btn', 'update-repo-btn', 'rebuild-repo-btn']);
        
        // 开始进度轮询
        this.startProgressPolling();
    }
    
    hideOperationProgress() {
        this.currentOperation = null;
        
        const progressContainer = document.getElementById('repo-progress');
        progressContainer.style.display = 'none';
        
        // 停止进度轮询
        this.stopProgressPolling();
        
        // 重新启用按钮
        this.loadRepositoryStatus();
    }
    
    startProgressPolling() {
        this.stopProgressPolling();
        
        this.operationTimer = setInterval(() => {
            this.loadRepositoryStatus();
        }, 2000); // 每2秒检查一次
    }
    
    stopProgressPolling() {
        if (this.operationTimer) {
            clearInterval(this.operationTimer);
            this.operationTimer = null;
        }
    }
    
    startStatusPolling() {
        // 每30秒检查一次仓库状态
        setInterval(() => {
            if (!this.currentOperation) {
                this.loadRepositoryStatus();
            }
        }, 30000);
    }
    
    enableButtons(buttonIds) {
        buttonIds.forEach(id => {
            const button = document.getElementById(id);
            if (button) {
                button.disabled = false;
                button.classList.remove('disabled');
            }
        });
    }
    
    disableButtons(buttonIds) {
        buttonIds.forEach(id => {
            const button = document.getElementById(id);
            if (button) {
                button.disabled = true;
                button.classList.add('disabled');
            }
        });
    }
    
    showSuccess(message) {
        // 显示成功消息
        console.log('成功:', message);
        // 这里可以集成通知组件
    }
    
    showError(message) {
        // 显示错误消息
        console.error('错误:', message);
        // 这里可以集成通知组件
    }
    
    // WebSocket事件处理
    onRepositoryProgress(data) {
        if (this.currentOperation) {
            const progressText = document.getElementById('repo-progress-text');
            const progressLog = document.getElementById('repo-progress-log');
            
            if (progressText) {
                progressText.textContent = data.message || '处理中...';
            }
            
            if (progressLog && data.log) {
                const logEntry = document.createElement('div');
                logEntry.className = 'log-entry';
                logEntry.textContent = data.log;
                progressLog.appendChild(logEntry);
                
                // 滚动到底部
                progressLog.scrollTop = progressLog.scrollHeight;
            }
        }
    }
    
    onRepositoryCompleted(data) {
        if (data.success) {
            this.showSuccess(data.message || '操作完成');
        } else {
            this.showError(data.message || '操作失败');
        }
        
        this.hideOperationProgress();
    }
}
