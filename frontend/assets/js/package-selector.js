/**
 * 软件包选择器
 * 简化的驱动和插件选择界面
 */

class PackageSelector {
    constructor(apiClient) {
        this.api = apiClient;
        this.selectedPackages = new Set();
        this.packageCategories = {};
        this.showAdvanced = false;
        
        this.init();
    }
    
    init() {
        this.createSelectorInterface();
        this.loadPackageCategories();
        this.bindEvents();
    }
    
    createSelectorInterface() {
        const selectorContainer = document.getElementById('package-selector-container');
        if (!selectorContainer) return;
        
        selectorContainer.innerHTML = `
            <div class="package-selector">
                <div class="selector-header">
                    <h3><i class="fas fa-cube"></i> 软件包选择</h3>
                    <div class="view-toggle">
                        <button id="simple-view-btn" class="view-btn active">
                            <i class="fas fa-th-large"></i> 简化视图
                        </button>
                        <button id="advanced-view-btn" class="view-btn">
                            <i class="fas fa-list"></i> 高级配置
                        </button>
                    </div>
                </div>
                
                <!-- 简化视图 -->
                <div id="simple-view" class="view-content">
                    <div class="package-categories">
                        <!-- 驱动程序 -->
                        <div class="category-section">
                            <div class="category-header">
                                <h4><i class="fas fa-microchip"></i> 驱动程序</h4>
                                <p>选择硬件驱动支持</p>
                            </div>
                            <div class="driver-grid" id="driver-packages">
                                <!-- 驱动包将在这里显示 -->
                            </div>
                        </div>
                        
                        <!-- 插件库 -->
                        <div class="category-section">
                            <div class="category-header">
                                <h4><i class="fas fa-puzzle-piece"></i> 功能插件</h4>
                                <p>选择功能插件</p>
                            </div>
                            <div class="plugin-tabs">
                                <div class="tab-nav">
                                    <button class="tab-btn active" data-tab="network">网络功能</button>
                                    <button class="tab-btn" data-tab="vpn">VPN服务</button>
                                    <button class="tab-btn" data-tab="storage">存储服务</button>
                                    <button class="tab-btn" data-tab="system">系统工具</button>
                                </div>
                                <div class="tab-content">
                                    <div class="tab-pane active" id="network-packages"></div>
                                    <div class="tab-pane" id="vpn-packages"></div>
                                    <div class="tab-pane" id="storage-packages"></div>
                                    <div class="tab-pane" id="system-packages"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- 高级视图 -->
                <div id="advanced-view" class="view-content" style="display: none;">
                    <div class="advanced-search">
                        <input type="text" 
                               id="package-search" 
                               class="search-input" 
                               placeholder="搜索软件包...">
                    </div>
                    <div class="advanced-categories" id="advanced-categories">
                        <!-- 高级分类将在这里显示 -->
                    </div>
                </div>
                
                <!-- 选择摘要 -->
                <div class="selection-summary">
                    <div class="summary-header">
                        <h4><i class="fas fa-check-circle"></i> 已选择的软件包</h4>
                        <span class="package-count">0 个软件包</span>
                    </div>
                    <div class="selected-packages" id="selected-packages-list">
                        <p class="no-selection">尚未选择任何软件包</p>
                    </div>
                    <div class="summary-actions">
                        <button id="clear-selection-btn" class="btn btn-secondary">
                            <i class="fas fa-trash"></i> 清空选择
                        </button>
                        <button id="apply-selection-btn" class="btn btn-primary">
                            <i class="fas fa-check"></i> 应用选择
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        this.elements = {
            simpleViewBtn: document.getElementById('simple-view-btn'),
            advancedViewBtn: document.getElementById('advanced-view-btn'),
            simpleView: document.getElementById('simple-view'),
            advancedView: document.getElementById('advanced-view'),
            driverPackages: document.getElementById('driver-packages'),
            packageSearch: document.getElementById('package-search'),
            advancedCategories: document.getElementById('advanced-categories'),
            selectedPackagesList: document.getElementById('selected-packages-list'),
            packageCount: document.querySelector('.package-count'),
            clearSelectionBtn: document.getElementById('clear-selection-btn'),
            applySelectionBtn: document.getElementById('apply-selection-btn'),
            tabBtns: document.querySelectorAll('.tab-btn'),
            tabPanes: document.querySelectorAll('.tab-pane')
        };
    }
    
    bindEvents() {
        // 视图切换
        this.elements.simpleViewBtn.addEventListener('click', () => {
            this.switchView('simple');
        });
        
        this.elements.advancedViewBtn.addEventListener('click', () => {
            this.switchView('advanced');
        });
        
        // 插件标签切换
        this.elements.tabBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const tabId = e.target.dataset.tab;
                this.switchTab(tabId);
            });
        });
        
        // 软件包搜索
        this.elements.packageSearch.addEventListener('input', (e) => {
            this.searchPackages(e.target.value);
        });
        
        // 选择操作
        this.elements.clearSelectionBtn.addEventListener('click', () => {
            this.clearSelection();
        });
        
        this.elements.applySelectionBtn.addEventListener('click', () => {
            this.applySelection();
        });
    }
    
    async loadPackageCategories() {
        try {
            const response = await this.api.get('/packages/categories');
            
            if (response.success) {
                this.packageCategories = response.data;
                this.displaySimpleView();
                this.displayAdvancedView();
            } else {
                this.showError('加载软件包分类失败: ' + response.message);
            }
        } catch (error) {
            console.error('加载软件包分类错误:', error);
            this.showError('加载软件包分类时发生错误');
        }
    }
    
    displaySimpleView() {
        // 显示驱动程序
        this.displayDriverPackages();
        
        // 显示插件分类
        this.displayPluginCategories();
    }
    
    displayDriverPackages() {
        if (!this.packageCategories.drivers) return;
        
        const drivers = this.packageCategories.drivers.packages;
        this.elements.driverPackages.innerHTML = drivers.map(pkg => `
            <div class="package-card driver-card">
                <div class="package-header">
                    <h5>${pkg.description}</h5>
                    <label class="package-toggle">
                        <input type="checkbox" 
                               data-package="${pkg.name}" 
                               ${pkg.default ? 'checked' : ''}>
                        <span class="toggle-slider"></span>
                    </label>
                </div>
                <p class="package-name">${pkg.name}</p>
            </div>
        `).join('');
        
        // 绑定驱动选择事件
        this.elements.driverPackages.querySelectorAll('input[type="checkbox"]').forEach(checkbox => {
            checkbox.addEventListener('change', (e) => {
                this.togglePackage(e.target.dataset.package, e.target.checked);
            });
            
            // 初始化选择状态
            if (checkbox.checked) {
                this.selectedPackages.add(checkbox.dataset.package);
            }
        });
    }
    
    displayPluginCategories() {
        const categories = ['network', 'vpn', 'storage', 'system'];
        
        categories.forEach(categoryId => {
            const category = this.packageCategories[categoryId];
            if (!category) return;
            
            const container = document.getElementById(`${categoryId}-packages`);
            if (!container) return;
            
            container.innerHTML = category.packages.map(pkg => `
                <div class="package-item">
                    <label class="package-label">
                        <input type="checkbox" 
                               data-package="${pkg.name}">
                        <span class="package-info">
                            <strong>${pkg.description}</strong>
                            <small>${pkg.name}</small>
                        </span>
                    </label>
                </div>
            `).join('');
            
            // 绑定插件选择事件
            container.querySelectorAll('input[type="checkbox"]').forEach(checkbox => {
                checkbox.addEventListener('change', (e) => {
                    this.togglePackage(e.target.dataset.package, e.target.checked);
                });
            });
        });
    }
    
    displayAdvancedView() {
        if (!this.elements.advancedCategories) return;
        
        this.elements.advancedCategories.innerHTML = Object.entries(this.packageCategories).map(([categoryId, category]) => `
            <div class="advanced-category">
                <div class="category-header">
                    <h4>${category.name}</h4>
                    <p>${category.description}</p>
                </div>
                <div class="package-list">
                    ${category.packages.map(pkg => `
                        <div class="advanced-package-item">
                            <label class="package-label">
                                <input type="checkbox" 
                                       data-package="${pkg.name}">
                                <span class="package-info">
                                    <strong>${pkg.description}</strong>
                                    <small>${pkg.name}</small>
                                </span>
                            </label>
                        </div>
                    `).join('')}
                </div>
            </div>
        `).join('');
        
        // 绑定高级视图选择事件
        this.elements.advancedCategories.querySelectorAll('input[type="checkbox"]').forEach(checkbox => {
            checkbox.addEventListener('change', (e) => {
                this.togglePackage(e.target.dataset.package, e.target.checked);
            });
        });
    }
    
    switchView(viewType) {
        this.showAdvanced = viewType === 'advanced';
        
        if (this.showAdvanced) {
            this.elements.simpleView.style.display = 'none';
            this.elements.advancedView.style.display = 'block';
            this.elements.simpleViewBtn.classList.remove('active');
            this.elements.advancedViewBtn.classList.add('active');
        } else {
            this.elements.simpleView.style.display = 'block';
            this.elements.advancedView.style.display = 'none';
            this.elements.simpleViewBtn.classList.add('active');
            this.elements.advancedViewBtn.classList.remove('active');
        }
    }
    
    switchTab(tabId) {
        // 切换标签按钮状态
        this.elements.tabBtns.forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === tabId);
        });
        
        // 切换标签内容
        this.elements.tabPanes.forEach(pane => {
            pane.classList.toggle('active', pane.id === `${tabId}-packages`);
        });
    }
    
    togglePackage(packageName, selected) {
        if (selected) {
            this.selectedPackages.add(packageName);
        } else {
            this.selectedPackages.delete(packageName);
        }
        
        this.updateSelectionSummary();
    }
    
    updateSelectionSummary() {
        const count = this.selectedPackages.size;
        this.elements.packageCount.textContent = `${count} 个软件包`;
        
        if (count === 0) {
            this.elements.selectedPackagesList.innerHTML = '<p class="no-selection">尚未选择任何软件包</p>';
        } else {
            this.elements.selectedPackagesList.innerHTML = Array.from(this.selectedPackages).map(pkg => `
                <span class="selected-package">
                    ${pkg}
                    <button class="remove-package" data-package="${pkg}">
                        <i class="fas fa-times"></i>
                    </button>
                </span>
            `).join('');
            
            // 绑定移除事件
            this.elements.selectedPackagesList.querySelectorAll('.remove-package').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    const packageName = e.target.closest('.remove-package').dataset.package;
                    this.removePackage(packageName);
                });
            });
        }
    }
    
    removePackage(packageName) {
        this.selectedPackages.delete(packageName);
        
        // 取消对应的复选框
        const checkbox = document.querySelector(`input[data-package="${packageName}"]`);
        if (checkbox) {
            checkbox.checked = false;
        }
        
        this.updateSelectionSummary();
    }
    
    clearSelection() {
        this.selectedPackages.clear();
        
        // 取消所有复选框
        document.querySelectorAll('input[data-package]').forEach(checkbox => {
            checkbox.checked = false;
        });
        
        this.updateSelectionSummary();
    }
    
    applySelection() {
        const packages = Array.from(this.selectedPackages);
        this.onSelectionApplied(packages);
        this.showSuccess(`已应用 ${packages.length} 个软件包的选择`);
    }
    
    searchPackages(query) {
        // 在高级视图中搜索软件包
        if (!query.trim()) {
            this.displayAdvancedView();
            return;
        }
        
        const filteredCategories = {};
        Object.entries(this.packageCategories).forEach(([categoryId, category]) => {
            const filteredPackages = category.packages.filter(pkg => 
                pkg.name.toLowerCase().includes(query.toLowerCase()) ||
                pkg.description.toLowerCase().includes(query.toLowerCase())
            );
            
            if (filteredPackages.length > 0) {
                filteredCategories[categoryId] = {
                    ...category,
                    packages: filteredPackages
                };
            }
        });
        
        // 显示搜索结果
        this.displayFilteredCategories(filteredCategories);
    }
    
    displayFilteredCategories(categories) {
        this.elements.advancedCategories.innerHTML = Object.entries(categories).map(([categoryId, category]) => `
            <div class="advanced-category">
                <div class="category-header">
                    <h4>${category.name}</h4>
                    <span class="package-count">${category.packages.length} 个软件包</span>
                </div>
                <div class="package-list">
                    ${category.packages.map(pkg => `
                        <div class="advanced-package-item">
                            <label class="package-label">
                                <input type="checkbox" 
                                       data-package="${pkg.name}"
                                       ${this.selectedPackages.has(pkg.name) ? 'checked' : ''}>
                                <span class="package-info">
                                    <strong>${pkg.description}</strong>
                                    <small>${pkg.name}</small>
                                </span>
                            </label>
                        </div>
                    `).join('')}
                </div>
            </div>
        `).join('');
        
        // 重新绑定事件
        this.elements.advancedCategories.querySelectorAll('input[type="checkbox"]').forEach(checkbox => {
            checkbox.addEventListener('change', (e) => {
                this.togglePackage(e.target.dataset.package, e.target.checked);
            });
        });
    }
    
    getSelectedPackages() {
        return Array.from(this.selectedPackages);
    }
    
    onSelectionApplied(packages) {
        // 可以被外部重写的回调函数
        console.log('软件包选择已应用:', packages);
    }
    
    showSuccess(message) {
        console.log('成功:', message);
    }
    
    showError(message) {
        console.error('错误:', message);
    }
}
