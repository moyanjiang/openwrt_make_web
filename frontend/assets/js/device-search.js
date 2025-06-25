/**
 * 设备搜索组件
 * 支持CPU和设备型号搜索
 */

class DeviceSearch {
    constructor(apiClient) {
        this.api = apiClient;
        this.selectedDevice = null;
        this.searchResults = [];
        this.searchTimeout = null;
        
        this.init();
    }
    
    init() {
        this.createSearchInterface();
        this.bindEvents();
    }
    
    createSearchInterface() {
        // 创建设备搜索界面
        const searchContainer = document.getElementById('device-search-container');
        if (!searchContainer) return;
        
        searchContainer.innerHTML = `
            <div class="device-search">
                <div class="search-header">
                    <h3><i class="fas fa-search"></i> 设备搜索</h3>
                    <p>搜索CPU型号或设备名称来选择编译目标</p>
                </div>
                
                <div class="search-input-group">
                    <input type="text" 
                           id="device-search-input" 
                           class="search-input" 
                           placeholder="输入设备名称、CPU型号或关键词..."
                           autocomplete="off">
                    <button id="search-clear-btn" class="search-clear-btn" style="display: none;">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                
                <div class="search-results" id="device-search-results" style="display: none;">
                    <div class="results-header">
                        <span class="results-count">找到 0 个设备</span>
                    </div>
                    <div class="results-list" id="device-results-list"></div>
                </div>
                
                <div class="selected-device" id="selected-device-info" style="display: none;">
                    <div class="device-card selected">
                        <div class="device-header">
                            <h4 class="device-name"></h4>
                            <span class="device-category"></span>
                        </div>
                        <div class="device-details">
                            <div class="device-detail">
                                <span class="label">目标平台:</span>
                                <span class="value target"></span>
                            </div>
                            <div class="device-detail">
                                <span class="label">CPU:</span>
                                <span class="value cpu"></span>
                            </div>
                        </div>
                        <div class="device-actions">
                            <button id="change-device-btn" class="btn btn-secondary">
                                <i class="fas fa-edit"></i> 更换设备
                            </button>
                            <button id="generate-config-btn" class="btn btn-primary">
                                <i class="fas fa-cog"></i> 生成配置
                            </button>
                        </div>
                    </div>
                </div>
                
                <div class="popular-devices" id="popular-devices">
                    <h4><i class="fas fa-star"></i> 热门设备</h4>
                    <div class="device-grid" id="popular-devices-grid">
                        <!-- 热门设备将在这里显示 -->
                    </div>
                </div>
            </div>
        `;
        
        this.elements = {
            searchInput: document.getElementById('device-search-input'),
            clearBtn: document.getElementById('search-clear-btn'),
            searchResults: document.getElementById('device-search-results'),
            resultsList: document.getElementById('device-results-list'),
            resultsCount: document.querySelector('.results-count'),
            selectedDeviceInfo: document.getElementById('selected-device-info'),
            changeDeviceBtn: document.getElementById('change-device-btn'),
            generateConfigBtn: document.getElementById('generate-config-btn'),
            popularDevices: document.getElementById('popular-devices'),
            popularDevicesGrid: document.getElementById('popular-devices-grid')
        };
    }
    
    bindEvents() {
        if (!this.elements.searchInput) return;
        
        // 搜索输入事件
        this.elements.searchInput.addEventListener('input', (e) => {
            const query = e.target.value.trim();
            
            if (query.length === 0) {
                this.clearSearch();
                return;
            }
            
            this.elements.clearBtn.style.display = 'block';
            
            // 防抖搜索
            clearTimeout(this.searchTimeout);
            this.searchTimeout = setTimeout(() => {
                this.searchDevices(query);
            }, 300);
        });
        
        // 清除搜索
        this.elements.clearBtn.addEventListener('click', () => {
            this.clearSearch();
        });
        
        // 更换设备
        this.elements.changeDeviceBtn.addEventListener('click', () => {
            this.showSearchInterface();
        });
        
        // 生成配置
        this.elements.generateConfigBtn.addEventListener('click', () => {
            this.generateDeviceConfig();
        });
        
        // 加载热门设备
        this.loadPopularDevices();
    }
    
    async searchDevices(query) {
        try {
            const response = await this.api.get('/devices/search', { q: query, limit: 20 });
            
            if (response.success) {
                this.searchResults = response.data.devices;
                this.displaySearchResults();
            } else {
                this.showError('搜索设备失败: ' + response.message);
            }
        } catch (error) {
            console.error('搜索设备错误:', error);
            this.showError('搜索设备时发生错误');
        }
    }
    
    displaySearchResults() {
        if (!this.elements.resultsList) return;
        
        this.elements.resultsCount.textContent = `找到 ${this.searchResults.length} 个设备`;
        this.elements.searchResults.style.display = 'block';
        this.elements.popularDevices.style.display = 'none';
        
        if (this.searchResults.length === 0) {
            this.elements.resultsList.innerHTML = `
                <div class="no-results">
                    <i class="fas fa-search"></i>
                    <p>未找到匹配的设备</p>
                    <p class="text-muted">请尝试其他关键词</p>
                </div>
            `;
            return;
        }
        
        this.elements.resultsList.innerHTML = this.searchResults.map(device => `
            <div class="device-card" data-device-id="${device.id}">
                <div class="device-header">
                    <h4 class="device-name">${device.name}</h4>
                    <span class="device-category">${this.getCategoryName(device.category)}</span>
                </div>
                <div class="device-details">
                    <div class="device-detail">
                        <span class="label">目标:</span>
                        <span class="value">${device.target}</span>
                    </div>
                    <div class="device-detail">
                        <span class="label">CPU:</span>
                        <span class="value">${device.cpu}</span>
                    </div>
                </div>
                <div class="device-keywords">
                    ${device.keywords.slice(0, 3).map(keyword => 
                        `<span class="keyword">${keyword}</span>`
                    ).join('')}
                </div>
                <button class="select-device-btn" data-device-id="${device.id}">
                    <i class="fas fa-check"></i> 选择此设备
                </button>
            </div>
        `).join('');
        
        // 绑定选择设备事件
        this.elements.resultsList.querySelectorAll('.select-device-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const deviceId = e.target.dataset.deviceId;
                this.selectDevice(deviceId);
            });
        });
    }
    
    async loadPopularDevices() {
        try {
            // 加载热门设备（预定义的常用设备）
            const popularDeviceIds = ['x86_64', 'raspberry_pi_4', 'xiaomi_r3g', 'newifi_d2'];
            const response = await this.api.get('/devices/search', { q: '', limit: 50 });
            
            if (response.success) {
                const popularDevices = response.data.devices.filter(device => 
                    popularDeviceIds.includes(device.id)
                );
                
                this.displayPopularDevices(popularDevices);
            }
        } catch (error) {
            console.error('加载热门设备错误:', error);
        }
    }
    
    displayPopularDevices(devices) {
        if (!this.elements.popularDevicesGrid) return;
        
        this.elements.popularDevicesGrid.innerHTML = devices.map(device => `
            <div class="popular-device-card" data-device-id="${device.id}">
                <div class="device-icon">
                    <i class="fas ${this.getDeviceIcon(device.category)}"></i>
                </div>
                <h5>${device.name}</h5>
                <p class="device-cpu">${device.cpu}</p>
                <button class="select-popular-btn" data-device-id="${device.id}">
                    选择
                </button>
            </div>
        `).join('');
        
        // 绑定选择热门设备事件
        this.elements.popularDevicesGrid.querySelectorAll('.select-popular-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const deviceId = e.target.dataset.deviceId;
                this.selectDevice(deviceId);
            });
        });
    }
    
    selectDevice(deviceId) {
        const device = this.searchResults.find(d => d.id === deviceId) ||
                      this.popularDevices?.find(d => d.id === deviceId);
        
        if (!device) return;
        
        this.selectedDevice = device;
        this.showSelectedDevice();
        
        // 触发设备选择事件
        this.onDeviceSelected(device);
    }
    
    showSelectedDevice() {
        if (!this.selectedDevice || !this.elements.selectedDeviceInfo) return;
        
        const device = this.selectedDevice;
        const deviceInfo = this.elements.selectedDeviceInfo;
        
        deviceInfo.querySelector('.device-name').textContent = device.name;
        deviceInfo.querySelector('.device-category').textContent = this.getCategoryName(device.category);
        deviceInfo.querySelector('.target').textContent = device.target;
        deviceInfo.querySelector('.cpu').textContent = device.cpu;
        
        // 隐藏搜索界面，显示选中设备
        this.elements.searchResults.style.display = 'none';
        this.elements.popularDevices.style.display = 'none';
        deviceInfo.style.display = 'block';
    }
    
    showSearchInterface() {
        this.elements.selectedDeviceInfo.style.display = 'none';
        this.elements.popularDevices.style.display = 'block';
        this.clearSearch();
    }
    
    clearSearch() {
        this.elements.searchInput.value = '';
        this.elements.clearBtn.style.display = 'none';
        this.elements.searchResults.style.display = 'none';
        this.elements.popularDevices.style.display = 'block';
        this.searchResults = [];
    }
    
    async generateDeviceConfig() {
        if (!this.selectedDevice) return;
        
        try {
            const response = await this.api.get(`/devices/${this.selectedDevice.id}/config`, {
                istore: 'true'
            });
            
            if (response.success) {
                // 触发配置生成事件
                this.onConfigGenerated(response.data.config);
                this.showSuccess('设备配置生成成功');
            } else {
                this.showError('生成设备配置失败: ' + response.message);
            }
        } catch (error) {
            console.error('生成设备配置错误:', error);
            this.showError('生成设备配置时发生错误');
        }
    }
    
    getCategoryName(category) {
        const categoryNames = {
            'x86': 'x86架构',
            'arm': 'ARM架构',
            'mips': 'MIPS架构'
        };
        return categoryNames[category] || category;
    }
    
    getDeviceIcon(category) {
        const categoryIcons = {
            'x86': 'fa-desktop',
            'arm': 'fa-microchip',
            'mips': 'fa-router'
        };
        return categoryIcons[category] || 'fa-microchip';
    }
    
    onDeviceSelected(device) {
        // 可以被外部重写的回调函数
        console.log('设备已选择:', device);
    }
    
    onConfigGenerated(config) {
        // 可以被外部重写的回调函数
        console.log('配置已生成:', config);
    }
    
    showSuccess(message) {
        // 显示成功消息
        console.log('成功:', message);
    }
    
    showError(message) {
        // 显示错误消息
        console.error('错误:', message);
    }
}
