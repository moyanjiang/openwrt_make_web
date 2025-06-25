/**
 * OpenWrt 编译器 - 主应用程序
 */

class OpenWrtCompiler {
    constructor() {
        this.config = {
            apiBaseUrl: 'http://127.0.0.1:5000/api',  // 后端API端口保持5000
            wsUrl: 'http://127.0.0.1:5000',           // WebSocket端口保持5000
            frontendPort: 9963,                       // 前端服务端口9963
            autoReconnect: true,
            reconnectInterval: 5000,
            maxReconnectAttempts: 10
        };

        this.state = {
            connected: false,
            compiling: false,
            cloning: false,
            currentTab: 'logs',
            reconnectAttempts: 0,
            selectedDevice: null,
            selectedPackages: []
        };

        this.elements = {};
        this.websocket = null;
        this.compileStartTime = null;
        this.compileTimer = null;

        // 使用全局API客户端
        this.api = window.apiClient;

        // 设置API客户端的基础URL
        if (this.api) {
            this.api.baseUrl = this.config.apiBaseUrl;
        }

        // 初始化组件
        this.userManager = null;
        this.deviceSearch = null;
        this.packageSelector = null;
        this.repositoryManager = null;
        this.userStatistics = null;

        this.init();
    }
    
    /**
     * 初始化应用程序
     */
    init() {
        this.initUserManager();
    }

    /**
     * 初始化用户管理器
     */
    initUserManager() {
        this.userManager = new UserManager(this.api);

        // 设置认证成功回调
        this.userManager.onAuthSuccess = (user) => {
            this.onUserAuthenticated(user);
        };
    }

    /**
     * 用户认证成功后的初始化
     */
    onUserAuthenticated(user) {
        this.initElements();
        this.initComponents();
        this.initEventListeners();
        this.initWebSocket();
        this.loadInitialData();
        this.hideLoading();

        console.log('OpenWrt Compiler (Debian版) initialized for user:', user.username);
    }

    /**
     * 初始化组件
     */
    initComponents() {
        // 初始化设备搜索组件
        this.deviceSearch = new DeviceSearch(this.api);
        this.deviceSearch.onDeviceSelected = (device) => {
            this.state.selectedDevice = device;
            this.onDeviceSelected(device);
        };
        this.deviceSearch.onConfigGenerated = (config) => {
            this.onDeviceConfigGenerated(config);
        };

        // 初始化软件包选择器
        this.packageSelector = new PackageSelector(this.api);
        this.packageSelector.onSelectionApplied = (packages) => {
            this.state.selectedPackages = packages;
            this.onPackagesSelected(packages);
        };

        // 初始化仓库管理器
        this.repositoryManager = new RepositoryManager(this.api, this.userManager);

        // 初始化用户统计
        this.userStatistics = new UserStatistics(this.api, this.userManager);
    }

    /**
     * 设备选择回调
     */
    onDeviceSelected(device) {
        console.log('设备已选择:', device);

        // 更新编译目标
        if (this.elements.compileTarget) {
            this.elements.compileTarget.value = device.target;
        }

        // 显示成功消息
        this.showNotification('success', `已选择设备: ${device.name}`);
    }

    /**
     * 设备配置生成回调
     */
    onDeviceConfigGenerated(config) {
        console.log('设备配置已生成:', config);

        // 可以在这里处理生成的配置
        this.showNotification('success', '设备配置已生成');
    }

    /**
     * 软件包选择回调
     */
    onPackagesSelected(packages) {
        console.log('软件包已选择:', packages);

        // 显示选择的软件包数量
        this.showNotification('success', `已选择 ${packages.length} 个软件包`);
    }
    
    /**
     * 初始化DOM元素引用
     */
    initElements() {
        // 状态元素
        this.elements.connectionStatus = document.getElementById('connection-status');
        this.elements.systemInfo = document.getElementById('system-info');
        
        // 源码管理
        this.elements.gitUrl = document.getElementById('git-url');
        this.elements.gitBranch = document.getElementById('git-branch');
        this.elements.cloneBtn = document.getElementById('clone-btn');
        this.elements.updateFeedsBtn = document.getElementById('update-feeds-btn');
        this.elements.installFeedsBtn = document.getElementById('install-feeds-btn');
        this.elements.cloneProgress = document.getElementById('clone-progress');
        this.elements.cloneProgressFill = document.getElementById('clone-progress-fill');
        this.elements.cloneProgressText = document.getElementById('clone-progress-text');
        
        // 配置管理
        this.elements.configTemplate = document.getElementById('config-template');
        this.elements.configName = document.getElementById('config-name');
        this.elements.applyTemplateBtn = document.getElementById('apply-template-btn');
        this.elements.uploadConfigBtn = document.getElementById('upload-config-btn');
        this.elements.downloadConfigBtn = document.getElementById('download-config-btn');
        this.elements.configFileInput = document.getElementById('config-file-input');
        
        // 编译控制
        this.elements.compileTarget = document.getElementById('compile-target');
        this.elements.compileThreads = document.getElementById('compile-threads');
        this.elements.verboseCompile = document.getElementById('verbose-compile');
        this.elements.cleanBuild = document.getElementById('clean-build');
        this.elements.startCompileBtn = document.getElementById('start-compile-btn');
        this.elements.stopCompileBtn = document.getElementById('stop-compile-btn');
        this.elements.compileStatusText = document.getElementById('compile-status-text');
        this.elements.compileProgressText = document.getElementById('compile-progress-text');
        this.elements.compileTimeText = document.getElementById('compile-time-text');
        this.elements.compileProgressFill = document.getElementById('compile-progress-fill');
        
        // 标签页
        this.elements.tabBtns = document.querySelectorAll('.tab-btn');
        this.elements.tabPanes = document.querySelectorAll('.tab-pane');
        
        // 日志
        this.elements.logsContent = document.getElementById('logs-content');
        this.elements.clearLogsBtn = document.getElementById('clear-logs-btn');
        this.elements.downloadLogsBtn = document.getElementById('download-logs-btn');
        this.elements.logSearch = document.getElementById('log-search');
        
        // 文件列表
        this.elements.filesList = document.getElementById('files-list');
        this.elements.refreshFilesBtn = document.getElementById('refresh-files-btn');
        this.elements.storageInfo = document.getElementById('storage-info');
        
        // 配置列表
        this.elements.configsList = document.getElementById('configs-list');
        this.elements.refreshConfigsBtn = document.getElementById('refresh-configs-btn');
        this.elements.newConfigBtn = document.getElementById('new-config-btn');
        
        // 系统信息
        this.elements.refreshSystemBtn = document.getElementById('refresh-system-btn');
        this.elements.serverStatus = document.getElementById('server-status');
        this.elements.connectionInfo = document.getElementById('connection-info');
        this.elements.storageDetails = document.getElementById('storage-details');
        this.elements.statsInfo = document.getElementById('stats-info');
        
        // 模态框
        this.elements.modalOverlay = document.getElementById('modal-overlay');
        this.elements.modal = document.getElementById('modal');
        this.elements.modalTitle = document.getElementById('modal-title');
        this.elements.modalBody = document.getElementById('modal-body');
        this.elements.modalFooter = document.getElementById('modal-footer');
        this.elements.modalClose = document.getElementById('modal-close');
        this.elements.modalCancel = document.getElementById('modal-cancel');
        this.elements.modalConfirm = document.getElementById('modal-confirm');
        
        // 通知容器
        this.elements.notifications = document.getElementById('notifications');
        
        // 面板切换
        this.elements.panelToggles = document.querySelectorAll('.panel-toggle');
    }
    
    /**
     * 初始化事件监听器
     */
    initEventListeners() {
        // 源码管理事件
        this.elements.cloneBtn.addEventListener('click', () => this.cloneRepository());
        this.elements.updateFeedsBtn.addEventListener('click', () => this.updateFeeds());
        this.elements.installFeedsBtn.addEventListener('click', () => this.installFeeds());
        
        // 配置管理事件
        this.elements.configTemplate.addEventListener('change', () => this.onConfigTemplateChange());
        this.elements.applyTemplateBtn.addEventListener('click', () => this.applyTemplate());
        this.elements.uploadConfigBtn.addEventListener('click', () => this.elements.configFileInput.click());
        this.elements.configFileInput.addEventListener('change', (e) => this.uploadConfig(e));
        this.elements.downloadConfigBtn.addEventListener('click', () => this.downloadConfig());
        
        // 编译控制事件
        this.elements.startCompileBtn.addEventListener('click', () => this.startCompile());
        this.elements.stopCompileBtn.addEventListener('click', () => this.stopCompile());
        
        // 标签页事件
        this.elements.tabBtns.forEach(btn => {
            btn.addEventListener('click', () => this.switchTab(btn.dataset.tab));
        });
        
        // 日志事件
        this.elements.clearLogsBtn.addEventListener('click', () => this.clearLogs());
        this.elements.downloadLogsBtn.addEventListener('click', () => this.downloadLogs());
        this.elements.logSearch.addEventListener('input', (e) => this.searchLogs(e.target.value));
        
        // 文件列表事件
        this.elements.refreshFilesBtn.addEventListener('click', () => this.loadFilesList());
        
        // 配置列表事件
        this.elements.refreshConfigsBtn.addEventListener('click', () => this.loadConfigsList());
        this.elements.newConfigBtn.addEventListener('click', () => this.newConfig());
        
        // 系统信息事件
        this.elements.refreshSystemBtn.addEventListener('click', () => this.loadSystemInfo());
        
        // 模态框事件
        this.elements.modalClose.addEventListener('click', () => this.hideModal());
        this.elements.modalCancel.addEventListener('click', () => this.hideModal());
        this.elements.modalOverlay.addEventListener('click', (e) => {
            if (e.target === this.elements.modalOverlay) {
                this.hideModal();
            }
        });
        
        // 面板切换事件
        this.elements.panelToggles.forEach(toggle => {
            toggle.addEventListener('click', () => this.togglePanel(toggle));
        });
        
        // 键盘事件
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.hideModal();
            }
        });
        
        // 窗口事件
        window.addEventListener('beforeunload', () => {
            if (this.websocket) {
                this.websocket.disconnect();
            }
        });
    }
    
    /**
     * 初始化WebSocket连接
     */
    initWebSocket() {
        if (typeof io !== 'undefined') {
            this.websocket = new WebSocketManager(this.config.wsUrl, this);
            this.websocket.connect();
        } else {
            console.warn('Socket.IO not loaded, WebSocket functionality disabled');
            this.showNotification('警告', 'WebSocket功能不可用，实时功能将受限', 'warning');
        }
    }
    
    /**
     * 加载初始数据
     */
    async loadInitialData() {
        try {
            await Promise.all([
                this.loadConfigTemplates(),
                this.loadFilesList(),
                this.loadConfigsList(),
                this.loadSystemInfo(),
                this.loadStorageInfo()
            ]);
        } catch (error) {
            console.error('Failed to load initial data:', error);
            this.showNotification('错误', '加载初始数据失败', 'error');
        }
    }
    
    /**
     * 隐藏加载指示器
     */
    hideLoading() {
        const loadingOverlay = document.getElementById('loading-overlay');
        if (loadingOverlay) {
            setTimeout(() => {
                loadingOverlay.style.opacity = '0';
                setTimeout(() => {
                    loadingOverlay.style.display = 'none';
                }, 300);
            }, 500);
        }
    }
    
    /**
     * 更新连接状态
     */
    updateConnectionStatus(connected) {
        this.state.connected = connected;
        const statusElement = this.elements.connectionStatus;
        const statusText = statusElement.querySelector('span');
        
        if (connected) {
            statusElement.className = 'connection-status connected';
            statusText.textContent = '已连接';
        } else {
            statusElement.className = 'connection-status disconnected';
            statusText.textContent = '连接断开';
        }
    }
    
    /**
     * 显示通知
     */
    showNotification(title, message, type = 'info', duration = 5000) {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        
        const iconMap = {
            success: 'fas fa-check-circle',
            error: 'fas fa-exclamation-circle',
            warning: 'fas fa-exclamation-triangle',
            info: 'fas fa-info-circle'
        };
        
        notification.innerHTML = `
            <div class="notification-header">
                <div class="notification-title">
                    <i class="${iconMap[type]}"></i>
                    ${title}
                </div>
                <button class="notification-close">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="notification-message">${message}</div>
            <div class="notification-progress" style="width: 100%;"></div>
        `;
        
        const closeBtn = notification.querySelector('.notification-close');
        const progressBar = notification.querySelector('.notification-progress');
        
        closeBtn.addEventListener('click', () => {
            this.removeNotification(notification);
        });
        
        this.elements.notifications.appendChild(notification);
        
        // 显示动画
        setTimeout(() => {
            notification.classList.add('show');
        }, 10);
        
        // 进度条动画
        if (duration > 0) {
            progressBar.style.transition = `width ${duration}ms linear`;
            setTimeout(() => {
                progressBar.style.width = '0%';
            }, 10);
            
            // 自动移除
            setTimeout(() => {
                this.removeNotification(notification);
            }, duration);
        }
        
        return notification;
    }
    
    /**
     * 移除通知
     */
    removeNotification(notification) {
        notification.classList.remove('show');
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }
    
    /**
     * 显示模态框
     */
    showModal(title, body, footer = null) {
        this.elements.modalTitle.textContent = title;
        this.elements.modalBody.innerHTML = body;
        
        if (footer) {
            this.elements.modalFooter.innerHTML = footer;
        }
        
        this.elements.modalOverlay.classList.add('show');
    }
    
    /**
     * 隐藏模态框
     */
    hideModal() {
        this.elements.modalOverlay.classList.remove('show');
    }
    
    /**
     * 切换面板
     */
    togglePanel(toggle) {
        const targetId = toggle.dataset.target;
        const content = document.getElementById(targetId);
        const isCollapsed = content.classList.contains('collapsed');
        
        if (isCollapsed) {
            content.classList.remove('collapsed');
            toggle.classList.remove('collapsed');
        } else {
            content.classList.add('collapsed');
            toggle.classList.add('collapsed');
        }
    }
    
    /**
     * 切换标签页
     */
    switchTab(tabName) {
        // 更新按钮状态
        this.elements.tabBtns.forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === tabName);
        });
        
        // 更新内容显示
        this.elements.tabPanes.forEach(pane => {
            pane.classList.toggle('active', pane.id === `${tabName}-tab`);
        });
        
        this.state.currentTab = tabName;
        
        // 加载对应数据
        switch (tabName) {
            case 'files':
                this.loadFilesList();
                break;
            case 'configs':
                this.loadConfigsList();
                break;
            case 'system':
                this.loadSystemInfo();
                break;
        }
    }

    /**
     * API调用辅助方法（使用API客户端）
     */
    async apiCall(endpoint, options = {}) {
        try {
            if (this.api) {
                return await this.api.call(endpoint, options);
            } else {
                // 回退到原始fetch方法
                const url = `${this.config.apiBaseUrl}${endpoint}`;
                const defaultOptions = {
                    method: 'GET',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                };

                const finalOptions = { ...defaultOptions, ...options };
                const response = await fetch(url, finalOptions);
                const data = await response.json();

                if (!response.ok) {
                    throw new Error(data.message || `HTTP ${response.status}`);
                }

                return data;
            }
        } catch (error) {
            console.error(`API call failed: ${endpoint}`, error);
            throw error;
        }
    }

    /**
     * 加载配置模板
     */
    async loadConfigTemplates() {
        try {
            const response = this.api ?
                await this.api.getConfigTemplates() :
                await this.apiCall('/config/templates');
            const templates = response.data.templates;

            // 清空现有选项
            this.elements.configTemplate.innerHTML = '<option value="">选择配置模板...</option>';

            // 添加模板选项
            Object.entries(templates).forEach(([id, template]) => {
                const option = document.createElement('option');
                option.value = id;
                option.textContent = template.name;
                this.elements.configTemplate.appendChild(option);
            });

        } catch (error) {
            console.error('Failed to load config templates:', error);
            this.showNotification('错误', '加载配置模板失败', 'error');
        }
    }

    /**
     * 配置模板变化事件
     */
    onConfigTemplateChange() {
        const hasTemplate = this.elements.configTemplate.value !== '';
        const hasName = this.elements.configName.value.trim() !== '';

        this.elements.applyTemplateBtn.disabled = !hasTemplate || !hasName;
    }

    /**
     * 应用配置模板
     */
    async applyTemplate() {
        const templateId = this.elements.configTemplate.value;
        const configName = this.elements.configName.value.trim();

        if (!templateId || !configName) {
            this.showNotification('错误', '请选择模板并输入配置名称', 'error');
            return;
        }

        try {
            this.elements.applyTemplateBtn.disabled = true;

            const response = await this.apiCall('/config/apply-template', {
                method: 'POST',
                body: JSON.stringify({
                    template_id: templateId,
                    config_name: configName
                })
            });

            this.showNotification('成功', '配置模板应用成功', 'success');
            this.loadConfigsList();
            this.elements.configName.value = '';
            this.elements.configTemplate.value = '';

        } catch (error) {
            this.showNotification('错误', `应用模板失败: ${error.message}`, 'error');
        } finally {
            this.elements.applyTemplateBtn.disabled = false;
        }
    }

    /**
     * 上传配置文件
     */
    async uploadConfig(event) {
        const file = event.target.files[0];
        if (!file) return;

        const formData = new FormData();
        formData.append('file', file);
        formData.append('overwrite', 'true');

        try {
            const response = await fetch(`${this.config.apiBaseUrl}/files/configs/${file.name}`, {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (response.ok) {
                this.showNotification('成功', '配置文件上传成功', 'success');
                this.loadConfigsList();
            } else {
                throw new Error(data.message);
            }

        } catch (error) {
            this.showNotification('错误', `上传失败: ${error.message}`, 'error');
        } finally {
            event.target.value = '';
        }
    }

    /**
     * 克隆仓库
     */
    async cloneRepository() {
        const gitUrl = this.elements.gitUrl.value.trim();
        const branch = this.elements.gitBranch.value;

        if (!gitUrl) {
            this.showNotification('错误', '请输入Git仓库地址', 'error');
            return;
        }

        try {
            this.state.cloning = true;
            this.elements.cloneBtn.disabled = true;
            this.elements.cloneProgress.style.display = 'block';
            this.updateCloneProgress(0, '开始克隆...');

            const response = await this.apiCall('/repository/clone', {
                method: 'POST',
                body: JSON.stringify({
                    url: gitUrl,
                    branch: branch
                })
            });

            this.showNotification('成功', '仓库克隆已开始', 'info');

        } catch (error) {
            this.showNotification('错误', `克隆失败: ${error.message}`, 'error');
            this.resetCloneState();
        }
    }

    /**
     * 更新克隆进度
     */
    updateCloneProgress(progress, message) {
        this.elements.cloneProgressFill.style.width = `${progress}%`;
        this.elements.cloneProgressText.textContent = `${progress}% - ${message}`;
    }

    /**
     * 重置克隆状态
     */
    resetCloneState() {
        this.state.cloning = false;
        this.elements.cloneBtn.disabled = false;
        this.elements.cloneProgress.style.display = 'none';
        this.elements.updateFeedsBtn.disabled = false;
        this.elements.installFeedsBtn.disabled = false;
    }

    /**
     * 更新Feeds
     */
    async updateFeeds() {
        try {
            this.elements.updateFeedsBtn.disabled = true;

            const response = await this.apiCall('/repository/update-feeds', {
                method: 'POST'
            });

            this.showNotification('成功', 'Feeds更新已开始', 'info');

        } catch (error) {
            this.showNotification('错误', `更新Feeds失败: ${error.message}`, 'error');
        } finally {
            this.elements.updateFeedsBtn.disabled = false;
        }
    }

    /**
     * 安装Feeds
     */
    async installFeeds() {
        try {
            this.elements.installFeedsBtn.disabled = true;

            const response = await this.apiCall('/repository/install-feeds', {
                method: 'POST'
            });

            this.showNotification('成功', 'Feeds安装已开始', 'info');

        } catch (error) {
            this.showNotification('错误', `安装Feeds失败: ${error.message}`, 'error');
        } finally {
            this.elements.installFeedsBtn.disabled = false;
        }
    }

    /**
     * 开始编译
     */
    async startCompile() {
        try {
            this.state.compiling = true;
            this.elements.startCompileBtn.disabled = true;
            this.elements.stopCompileBtn.disabled = false;
            this.compileStartTime = Date.now();
            this.startCompileTimer();

            const compileOptions = {
                target: this.elements.compileTarget.value,
                threads: this.elements.compileThreads.value,
                verbose: this.elements.verboseCompile.checked,
                clean: this.elements.cleanBuild.checked
            };

            const response = await this.apiCall('/compile/start', {
                method: 'POST',
                body: JSON.stringify(compileOptions)
            });

            this.showNotification('成功', '编译已开始', 'info');
            this.updateCompileStatus('编译中', 0);

        } catch (error) {
            this.showNotification('错误', `启动编译失败: ${error.message}`, 'error');
            this.resetCompileState();
        }
    }

    /**
     * 停止编译
     */
    async stopCompile() {
        try {
            const response = await this.apiCall('/compile/stop', {
                method: 'POST'
            });

            this.showNotification('成功', '编译已停止', 'warning');
            this.resetCompileState();

        } catch (error) {
            this.showNotification('错误', `停止编译失败: ${error.message}`, 'error');
        }
    }

    /**
     * 更新编译状态
     */
    updateCompileStatus(status, progress) {
        this.elements.compileStatusText.textContent = status;
        this.elements.compileProgressText.textContent = `${progress}%`;
        this.elements.compileProgressFill.style.width = `${progress}%`;
    }

    /**
     * 重置编译状态
     */
    resetCompileState() {
        this.state.compiling = false;
        this.elements.startCompileBtn.disabled = false;
        this.elements.stopCompileBtn.disabled = true;
        this.stopCompileTimer();
        this.updateCompileStatus('未开始', 0);
    }

    /**
     * 开始编译计时器
     */
    startCompileTimer() {
        this.compileTimer = setInterval(() => {
            if (this.compileStartTime) {
                const elapsed = Date.now() - this.compileStartTime;
                const hours = Math.floor(elapsed / 3600000);
                const minutes = Math.floor((elapsed % 3600000) / 60000);
                const seconds = Math.floor((elapsed % 60000) / 1000);

                const timeString = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
                this.elements.compileTimeText.textContent = timeString;
            }
        }, 1000);
    }

    /**
     * 停止编译计时器
     */
    stopCompileTimer() {
        if (this.compileTimer) {
            clearInterval(this.compileTimer);
            this.compileTimer = null;
        }
    }

    /**
     * 加载文件列表
     */
    async loadFilesList() {
        try {
            const response = await this.apiCall('/files/firmware');
            const files = response.data.files;

            this.renderFilesList(files);

        } catch (error) {
            console.error('Failed to load files list:', error);
            this.showNotification('错误', '加载文件列表失败', 'error');
        }
    }

    /**
     * 渲染文件列表
     */
    renderFilesList(files) {
        if (files.length === 0) {
            this.elements.filesList.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-folder-open"></i>
                    <p>暂无固件文件</p>
                    <small>编译完成后，固件文件将显示在这里</small>
                </div>
            `;
            return;
        }

        this.elements.filesList.innerHTML = files.map(file => `
            <div class="file-item">
                <div class="file-header">
                    <div class="file-name">
                        <i class="fas fa-file-archive"></i>
                        ${file.name}
                    </div>
                    <div class="file-actions">
                        <button class="btn btn-sm btn-primary" onclick="app.downloadFile('firmware', '${file.name}')">
                            <i class="fas fa-download"></i> 下载
                        </button>
                        <button class="btn btn-sm btn-secondary" onclick="app.showFileInfo('firmware', '${file.name}')">
                            <i class="fas fa-info"></i> 详情
                        </button>
                        <button class="btn btn-sm btn-danger" onclick="app.deleteFile('firmware', '${file.name}')">
                            <i class="fas fa-trash"></i> 删除
                        </button>
                    </div>
                </div>
                <div class="file-info">
                    <div class="info-item">
                        <div class="info-label">大小</div>
                        <div class="info-value">${file.size_human}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">修改时间</div>
                        <div class="info-value">${TimeUtils ? TimeUtils.formatTime(file.modified_time * 1000) : new Date(file.modified_time * 1000).toLocaleString()}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">MD5</div>
                        <div class="info-value">${file.md5.substring(0, 8)}...</div>
                    </div>
                </div>
            </div>
        `).join('');
    }

    /**
     * 加载配置列表
     */
    async loadConfigsList() {
        try {
            const response = await this.apiCall('/files/configs');
            const configs = response.data.files;

            this.renderConfigsList(configs);

        } catch (error) {
            console.error('Failed to load configs list:', error);
            this.showNotification('错误', '加载配置列表失败', 'error');
        }
    }

    /**
     * 渲染配置列表
     */
    renderConfigsList(configs) {
        if (configs.length === 0) {
            this.elements.configsList.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-cogs"></i>
                    <p>暂无配置文件</p>
                    <small>请先应用配置模板或上传配置文件</small>
                </div>
            `;
            return;
        }

        this.elements.configsList.innerHTML = configs.map(config => `
            <div class="config-item">
                <div class="config-header">
                    <div class="config-name">
                        <i class="fas fa-cog"></i>
                        ${config.name}
                    </div>
                    <div class="config-actions">
                        <button class="btn btn-sm btn-primary" onclick="app.downloadFile('config', '${config.name}')">
                            <i class="fas fa-download"></i> 下载
                        </button>
                        <button class="btn btn-sm btn-secondary" onclick="app.showFileInfo('config', '${config.name}')">
                            <i class="fas fa-info"></i> 详情
                        </button>
                        <button class="btn btn-sm btn-danger" onclick="app.deleteFile('config', '${config.name}')">
                            <i class="fas fa-trash"></i> 删除
                        </button>
                    </div>
                </div>
                <div class="config-info">
                    <div class="info-item">
                        <div class="info-label">大小</div>
                        <div class="info-value">${config.size_human}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">修改时间</div>
                        <div class="info-value">${new Date(config.modified_time * 1000).toLocaleString()}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">类型</div>
                        <div class="info-value">${config.extension}</div>
                    </div>
                </div>
            </div>
        `).join('');
    }

    /**
     * 加载存储信息
     */
    async loadStorageInfo() {
        try {
            const response = await this.apiCall('/files/storage');
            const storage = response.data.storage;

            this.elements.storageInfo.textContent = `存储空间: ${storage.used_space_human} / ${storage.available_space_human}`;

            // 更新系统信息页面的存储详情
            if (this.elements.storageDetails) {
                const availableSpace = document.getElementById('available-space');
                const usedSpace = document.getElementById('used-space');
                const firmwareSize = document.getElementById('firmware-size');

                if (availableSpace) availableSpace.textContent = storage.available_space_human;
                if (usedSpace) usedSpace.textContent = storage.used_space_human;
                if (firmwareSize) firmwareSize.textContent = storage.firmware_size_human;
            }

        } catch (error) {
            console.error('Failed to load storage info:', error);
        }
    }

    /**
     * 加载系统信息
     */
    async loadSystemInfo() {
        try {
            // 加载服务器状态
            const statusResponse = await this.apiCall('/status');
            this.updateServerStatus(statusResponse.data);

            // 加载WebSocket统计
            const wsResponse = await this.apiCall('/websocket/stats');
            this.updateConnectionInfo(wsResponse.data);

            // 加载存储信息
            await this.loadStorageInfo();

        } catch (error) {
            console.error('Failed to load system info:', error);
            this.showNotification('错误', '加载系统信息失败', 'error');
        }
    }

    /**
     * 更新服务器状态
     */
    updateServerStatus(data) {
        const serverUptime = document.getElementById('server-uptime');
        const serverVersion = document.getElementById('server-version');

        if (serverUptime) {
            const uptime = Math.floor(data.uptime || 0);
            const hours = Math.floor(uptime / 3600);
            const minutes = Math.floor((uptime % 3600) / 60);
            serverUptime.textContent = `${hours}小时${minutes}分钟`;
        }

        if (serverVersion) {
            serverVersion.textContent = data.version || '1.0.0';
        }
    }

    /**
     * 更新连接信息
     */
    updateConnectionInfo(data) {
        const wsStatus = document.getElementById('ws-status');
        const apiStatus = document.getElementById('api-status');
        const connectionLatency = document.getElementById('connection-latency');

        if (wsStatus) {
            wsStatus.innerHTML = this.state.connected ?
                '<span class="status-indicator online">已连接</span>' :
                '<span class="status-indicator offline">断开</span>';
        }

        if (apiStatus) {
            apiStatus.innerHTML = '<span class="status-indicator online">正常</span>';
        }

        if (connectionLatency) {
            connectionLatency.textContent = '< 50ms';
        }
    }

    /**
     * 下载文件
     */
    downloadFile(type, filename) {
        const url = `${this.config.apiBaseUrl}/files/${type}/${filename}`;
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        this.showNotification('成功', `开始下载 ${filename}`, 'info');
    }

    /**
     * 显示文件信息
     */
    async showFileInfo(type, filename) {
        try {
            const response = await this.apiCall(`/files/${type}/${filename}/info`);
            const fileInfo = response.data.file_info;

            const infoHtml = `
                <div class="file-details">
                    <p><strong>文件名:</strong> ${fileInfo.name}</p>
                    <p><strong>大小:</strong> ${fileInfo.size_human} (${fileInfo.size} 字节)</p>
                    <p><strong>类型:</strong> ${fileInfo.mime_type}</p>
                    <p><strong>创建时间:</strong> ${new Date(fileInfo.created_time * 1000).toLocaleString()}</p>
                    <p><strong>修改时间:</strong> ${new Date(fileInfo.modified_time * 1000).toLocaleString()}</p>
                    <p><strong>MD5:</strong> <code>${fileInfo.md5}</code></p>
                    <p><strong>SHA256:</strong> <code>${fileInfo.sha256}</code></p>
                </div>
            `;

            this.showModal(`文件信息 - ${filename}`, infoHtml);

        } catch (error) {
            this.showNotification('错误', `获取文件信息失败: ${error.message}`, 'error');
        }
    }

    /**
     * 删除文件
     */
    async deleteFile(type, filename) {
        const confirmed = confirm(`确定要删除文件 "${filename}" 吗？此操作不可撤销。`);
        if (!confirmed) return;

        try {
            await this.apiCall(`/files/${type}/${filename}`, {
                method: 'DELETE'
            });

            this.showNotification('成功', `文件 ${filename} 已删除`, 'success');

            // 刷新对应列表
            if (type === 'firmware') {
                this.loadFilesList();
            } else if (type === 'config') {
                this.loadConfigsList();
            }

        } catch (error) {
            this.showNotification('错误', `删除文件失败: ${error.message}`, 'error');
        }
    }

    /**
     * 清空日志
     */
    clearLogs() {
        this.elements.logsContent.innerHTML = `
            <div class="log-entry info">
                <span class="log-time">[${new Date().toLocaleString()}]</span>
                <span class="log-level">INFO</span>
                <span class="log-message">日志已清空</span>
            </div>
        `;
    }

    /**
     * 下载日志
     */
    downloadLogs() {
        const logs = this.elements.logsContent.textContent;
        const blob = new Blob([logs], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);

        const link = document.createElement('a');
        link.href = url;
        link.download = `compile-logs-${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.txt`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        URL.revokeObjectURL(url);
        this.showNotification('成功', '日志文件已下载', 'success');
    }

    /**
     * 搜索日志
     */
    searchLogs(query) {
        const logEntries = this.elements.logsContent.querySelectorAll('.log-entry');

        logEntries.forEach(entry => {
            const text = entry.textContent.toLowerCase();
            const matches = query === '' || text.includes(query.toLowerCase());
            entry.style.display = matches ? 'block' : 'none';
        });
    }

    /**
     * 添加日志条目
     */
    addLogEntry(level, message, timestamp = null) {
        const time = timestamp || new Date().toLocaleString();
        const logEntry = document.createElement('div');
        logEntry.className = `log-entry ${level}`;
        logEntry.innerHTML = `
            <span class="log-time">[${time}]</span>
            <span class="log-level">${level.toUpperCase()}</span>
            <span class="log-message">${message}</span>
        `;

        this.elements.logsContent.appendChild(logEntry);

        // 自动滚动到底部
        this.elements.logsContent.scrollTop = this.elements.logsContent.scrollHeight;

        // 限制日志条目数量
        const maxEntries = 1000;
        const entries = this.elements.logsContent.querySelectorAll('.log-entry');
        if (entries.length > maxEntries) {
            entries[0].remove();
        }
    }
}

// 全局应用实例
let app;

// 页面加载完成后初始化应用
document.addEventListener('DOMContentLoaded', () => {
    app = new OpenWrtCompiler();
});
