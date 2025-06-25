/**
 * 用户管理组件
 * 处理用户登录、注册和会话管理
 */

class UserManager {
    constructor(apiClient) {
        this.api = apiClient;
        this.currentUser = null;
        this.token = null;
        
        this.init();
    }
    
    init() {
        // 检查本地存储的token
        this.token = localStorage.getItem('auth_token');
        if (this.token) {
            this.validateToken();
        } else {
            this.showAuthInterface();
        }
    }
    
    async validateToken() {
        try {
            // 验证token有效性
            const response = await this.api.get('/auth/validate', {}, {
                'Authorization': `Bearer ${this.token}`
            });
            
            if (response.success) {
                this.currentUser = response.data.user;
                this.onUserAuthenticated();
            } else {
                this.clearAuth();
                this.showAuthInterface();
            }
        } catch (error) {
            console.error('Token验证失败:', error);
            this.clearAuth();
            this.showAuthInterface();
        }
    }
    
    showAuthInterface() {
        // 创建登录/注册界面
        const authContainer = document.createElement('div');
        authContainer.id = 'auth-container';
        authContainer.className = 'auth-overlay';
        
        authContainer.innerHTML = `
            <div class="auth-modal">
                <div class="auth-header">
                    <h2><i class="fas fa-microchip"></i> OpenWrt 编译器</h2>
                    <p>Debian版 - 多用户编译系统</p>
                </div>
                
                <div class="auth-tabs">
                    <button class="auth-tab active" data-tab="login">登录</button>
                    <button class="auth-tab" data-tab="register">注册</button>
                </div>
                
                <!-- 登录表单 -->
                <div class="auth-form" id="login-form">
                    <h3>用户登录</h3>
                    <form id="login-form-element">
                        <div class="form-group">
                            <label for="login-username">用户名:</label>
                            <input type="text" id="login-username" class="form-control" required>
                        </div>
                        <div class="form-group">
                            <label for="login-password">密码:</label>
                            <input type="password" id="login-password" class="form-control" required>
                        </div>
                        <button type="submit" class="btn btn-primary btn-block">
                            <i class="fas fa-sign-in-alt"></i> 登录
                        </button>
                    </form>
                </div>
                
                <!-- 注册表单 -->
                <div class="auth-form" id="register-form" style="display: none;">
                    <h3>用户注册</h3>
                    <form id="register-form-element">
                        <div class="form-group">
                            <label for="register-username">用户名:</label>
                            <input type="text" id="register-username" class="form-control" required>
                            <small class="form-text">3-20个字符，只能包含字母、数字和下划线</small>
                        </div>
                        <div class="form-group">
                            <label for="register-email">邮箱 (可选):</label>
                            <input type="email" id="register-email" class="form-control">
                        </div>
                        <div class="form-group">
                            <label for="register-password">密码:</label>
                            <input type="password" id="register-password" class="form-control" required>
                            <small class="form-text">至少6个字符</small>
                        </div>
                        <div class="form-group">
                            <label for="register-confirm-password">确认密码:</label>
                            <input type="password" id="register-confirm-password" class="form-control" required>
                        </div>
                        <button type="submit" class="btn btn-primary btn-block">
                            <i class="fas fa-user-plus"></i> 注册
                        </button>
                    </form>
                    <div class="auth-note">
                        <p><i class="fas fa-info-circle"></i> 首个注册用户将自动成为管理员</p>
                    </div>
                </div>
                
                <div class="auth-footer">
                    <p>OpenWrt编译器 Debian版 v2.0</p>
                </div>
            </div>
        `;
        
        document.body.appendChild(authContainer);
        this.bindAuthEvents();
    }
    
    bindAuthEvents() {
        // 标签切换
        document.querySelectorAll('.auth-tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                const tabType = e.target.dataset.tab;
                this.switchAuthTab(tabType);
            });
        });
        
        // 登录表单
        document.getElementById('login-form-element').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleLogin();
        });
        
        // 注册表单
        document.getElementById('register-form-element').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleRegister();
        });
    }
    
    switchAuthTab(tabType) {
        // 切换标签状态
        document.querySelectorAll('.auth-tab').forEach(tab => {
            tab.classList.toggle('active', tab.dataset.tab === tabType);
        });
        
        // 切换表单显示
        document.getElementById('login-form').style.display = 
            tabType === 'login' ? 'block' : 'none';
        document.getElementById('register-form').style.display = 
            tabType === 'register' ? 'block' : 'none';
    }
    
    async handleLogin() {
        const username = document.getElementById('login-username').value.trim();
        const password = document.getElementById('login-password').value;
        
        if (!username || !password) {
            this.showError('请填写用户名和密码');
            return;
        }
        
        try {
            const response = await this.api.post('/auth/login', {
                username,
                password
            });
            
            if (response.success) {
                this.token = response.data.token;
                this.currentUser = response.data.user;
                
                // 保存token
                localStorage.setItem('auth_token', this.token);
                
                // 设置API客户端的认证头
                this.api.setAuthToken(this.token);
                
                // 移除认证界面
                this.hideAuthInterface();
                
                // 触发认证成功事件
                this.onUserAuthenticated();
                
                this.showSuccess(`欢迎回来，${this.currentUser.username}！`);
            } else {
                this.showError(response.message || '登录失败');
            }
        } catch (error) {
            console.error('登录错误:', error);
            this.showError('登录时发生错误，请稍后重试');
        }
    }
    
    async handleRegister() {
        const username = document.getElementById('register-username').value.trim();
        const email = document.getElementById('register-email').value.trim();
        const password = document.getElementById('register-password').value;
        const confirmPassword = document.getElementById('register-confirm-password').value;
        
        // 验证输入
        if (!username || !password) {
            this.showError('请填写用户名和密码');
            return;
        }
        
        if (username.length < 3 || username.length > 20) {
            this.showError('用户名长度应在3-20个字符之间');
            return;
        }
        
        if (!/^[a-zA-Z0-9_]+$/.test(username)) {
            this.showError('用户名只能包含字母、数字和下划线');
            return;
        }
        
        if (password.length < 6) {
            this.showError('密码长度至少需要6个字符');
            return;
        }
        
        if (password !== confirmPassword) {
            this.showError('两次输入的密码不一致');
            return;
        }
        
        try {
            const response = await this.api.post('/auth/register', {
                username,
                email,
                password
            });
            
            if (response.success) {
                this.token = response.data.token;
                this.currentUser = response.data.user;
                
                // 保存token
                localStorage.setItem('auth_token', this.token);
                
                // 设置API客户端的认证头
                this.api.setAuthToken(this.token);
                
                // 移除认证界面
                this.hideAuthInterface();
                
                // 触发认证成功事件
                this.onUserAuthenticated();
                
                const welcomeMsg = this.currentUser.is_admin ? 
                    `欢迎，管理员 ${this.currentUser.username}！` :
                    `注册成功，欢迎 ${this.currentUser.username}！`;
                this.showSuccess(welcomeMsg);
            } else {
                this.showError(response.message || '注册失败');
            }
        } catch (error) {
            console.error('注册错误:', error);
            this.showError('注册时发生错误，请稍后重试');
        }
    }
    
    hideAuthInterface() {
        const authContainer = document.getElementById('auth-container');
        if (authContainer) {
            authContainer.remove();
        }
    }
    
    logout() {
        this.clearAuth();
        this.showAuthInterface();
        this.showSuccess('已成功退出登录');
    }
    
    clearAuth() {
        this.token = null;
        this.currentUser = null;
        localStorage.removeItem('auth_token');
        
        // 清除API客户端的认证头
        if (this.api.clearAuthToken) {
            this.api.clearAuthToken();
        }
    }
    
    onUserAuthenticated() {
        // 更新用户界面
        this.updateUserInterface();
        
        // 可以被外部重写的回调函数
        if (this.onAuthSuccess) {
            this.onAuthSuccess(this.currentUser);
        }
    }
    
    updateUserInterface() {
        // 更新顶部用户信息
        const userInfo = document.querySelector('.user-info');
        if (userInfo) {
            userInfo.innerHTML = `
                <div class="user-avatar">
                    <i class="fas fa-user"></i>
                </div>
                <div class="user-details">
                    <span class="username">${this.currentUser.username}</span>
                    ${this.currentUser.is_admin ? '<span class="user-role">管理员</span>' : ''}
                </div>
                <div class="user-actions">
                    <button id="user-menu-btn" class="user-menu-btn">
                        <i class="fas fa-chevron-down"></i>
                    </button>
                </div>
            `;
            
            // 绑定用户菜单事件
            document.getElementById('user-menu-btn').addEventListener('click', () => {
                this.showUserMenu();
            });
        }
    }
    
    showUserMenu() {
        // 显示用户菜单（设置、退出等）
        const menu = document.createElement('div');
        menu.className = 'user-menu';
        menu.innerHTML = `
            <div class="menu-item" data-action="settings">
                <i class="fas fa-cog"></i> 设置
            </div>
            <div class="menu-item" data-action="logout">
                <i class="fas fa-sign-out-alt"></i> 退出登录
            </div>
        `;
        
        // 绑定菜单事件
        menu.addEventListener('click', (e) => {
            const action = e.target.closest('.menu-item')?.dataset.action;
            if (action === 'logout') {
                this.logout();
            } else if (action === 'settings') {
                this.showUserSettings();
            }
            menu.remove();
        });
        
        document.body.appendChild(menu);
        
        // 点击其他地方关闭菜单
        setTimeout(() => {
            document.addEventListener('click', () => menu.remove(), { once: true });
        }, 100);
    }
    
    showUserSettings() {
        // 显示用户设置界面
        console.log('显示用户设置');
    }
    
    getCurrentUser() {
        return this.currentUser;
    }
    
    isAuthenticated() {
        return !!this.token && !!this.currentUser;
    }
    
    isAdmin() {
        return this.currentUser?.is_admin || false;
    }
    
    showSuccess(message) {
        console.log('成功:', message);
    }
    
    showError(message) {
        console.error('错误:', message);
    }
}
