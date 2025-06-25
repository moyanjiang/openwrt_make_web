/**
 * 工具函数模块
 */

/**
 * DOM操作工具
 */
const DOM = {
    /**
     * 根据ID获取元素
     */
    getElementById(id) {
        return document.getElementById(id);
    },
    
    /**
     * 根据选择器获取元素
     */
    querySelector(selector) {
        return document.querySelector(selector);
    },
    
    /**
     * 根据选择器获取所有元素
     */
    querySelectorAll(selector) {
        return document.querySelectorAll(selector);
    },
    
    /**
     * 创建元素
     */
    createElement(tag, attributes = {}, textContent = '') {
        const element = document.createElement(tag);
        
        Object.entries(attributes).forEach(([key, value]) => {
            if (key === 'className') {
                element.className = value;
            } else if (key === 'dataset') {
                Object.entries(value).forEach(([dataKey, dataValue]) => {
                    element.dataset[dataKey] = dataValue;
                });
            } else {
                element.setAttribute(key, value);
            }
        });
        
        if (textContent) {
            element.textContent = textContent;
        }
        
        return element;
    },
    
    /**
     * 添加事件监听器
     */
    addEventListener(element, event, handler, options = {}) {
        if (typeof element === 'string') {
            element = this.querySelector(element);
        }
        
        if (element) {
            element.addEventListener(event, handler, options);
        }
    },
    
    /**
     * 移除事件监听器
     */
    removeEventListener(element, event, handler) {
        if (typeof element === 'string') {
            element = this.querySelector(element);
        }
        
        if (element) {
            element.removeEventListener(event, handler);
        }
    },
    
    /**
     * 添加CSS类
     */
    addClass(element, className) {
        if (typeof element === 'string') {
            element = this.querySelector(element);
        }
        
        if (element) {
            element.classList.add(className);
        }
    },
    
    /**
     * 移除CSS类
     */
    removeClass(element, className) {
        if (typeof element === 'string') {
            element = this.querySelector(element);
        }
        
        if (element) {
            element.classList.remove(className);
        }
    },
    
    /**
     * 切换CSS类
     */
    toggleClass(element, className) {
        if (typeof element === 'string') {
            element = this.querySelector(element);
        }
        
        if (element) {
            element.classList.toggle(className);
        }
    },
    
    /**
     * 检查是否包含CSS类
     */
    hasClass(element, className) {
        if (typeof element === 'string') {
            element = this.querySelector(element);
        }
        
        return element ? element.classList.contains(className) : false;
    }
};

/**
 * 字符串工具
 */
const StringUtils = {
    /**
     * 格式化字符串
     */
    format(template, ...args) {
        return template.replace(/{(\d+)}/g, (match, number) => {
            return typeof args[number] !== 'undefined' ? args[number] : match;
        });
    },
    
    /**
     * 首字母大写
     */
    capitalize(str) {
        return str.charAt(0).toUpperCase() + str.slice(1);
    },
    
    /**
     * 驼峰命名转换
     */
    toCamelCase(str) {
        return str.replace(/-([a-z])/g, (match, letter) => letter.toUpperCase());
    },
    
    /**
     * 短横线命名转换
     */
    toKebabCase(str) {
        return str.replace(/([A-Z])/g, '-$1').toLowerCase();
    },
    
    /**
     * 截断字符串
     */
    truncate(str, length, suffix = '...') {
        if (str.length <= length) return str;
        return str.substring(0, length) + suffix;
    },
    
    /**
     * 转义HTML
     */
    escapeHtml(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    },
    
    /**
     * 生成随机字符串
     */
    randomString(length = 8) {
        const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
        let result = '';
        for (let i = 0; i < length; i++) {
            result += chars.charAt(Math.floor(Math.random() * chars.length));
        }
        return result;
    }
};

/**
 * 时间工具
 */
const TimeUtils = {
    /**
     * 格式化时间
     */
    formatTime(timestamp, format = 'YYYY-MM-DD HH:mm:ss') {
        const date = new Date(timestamp);
        
        const formatMap = {
            'YYYY': date.getFullYear(),
            'MM': String(date.getMonth() + 1).padStart(2, '0'),
            'DD': String(date.getDate()).padStart(2, '0'),
            'HH': String(date.getHours()).padStart(2, '0'),
            'mm': String(date.getMinutes()).padStart(2, '0'),
            'ss': String(date.getSeconds()).padStart(2, '0')
        };
        
        return format.replace(/YYYY|MM|DD|HH|mm|ss/g, match => formatMap[match]);
    },
    
    /**
     * 相对时间
     */
    timeAgo(timestamp) {
        const now = Date.now();
        const diff = now - timestamp;
        
        const units = [
            { name: '年', value: 365 * 24 * 60 * 60 * 1000 },
            { name: '月', value: 30 * 24 * 60 * 60 * 1000 },
            { name: '天', value: 24 * 60 * 60 * 1000 },
            { name: '小时', value: 60 * 60 * 1000 },
            { name: '分钟', value: 60 * 1000 },
            { name: '秒', value: 1000 }
        ];
        
        for (const unit of units) {
            const count = Math.floor(diff / unit.value);
            if (count > 0) {
                return `${count}${unit.name}前`;
            }
        }
        
        return '刚刚';
    },
    
    /**
     * 格式化持续时间
     */
    formatDuration(milliseconds) {
        const seconds = Math.floor(milliseconds / 1000);
        const minutes = Math.floor(seconds / 60);
        const hours = Math.floor(minutes / 60);
        
        if (hours > 0) {
            return `${hours}:${String(minutes % 60).padStart(2, '0')}:${String(seconds % 60).padStart(2, '0')}`;
        } else {
            return `${minutes}:${String(seconds % 60).padStart(2, '0')}`;
        }
    }
};

/**
 * 文件工具
 */
const FileUtils = {
    /**
     * 格式化文件大小
     */
    formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        
        const units = ['B', 'KB', 'MB', 'GB', 'TB'];
        const k = 1024;
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return `${(bytes / Math.pow(k, i)).toFixed(1)} ${units[i]}`;
    },
    
    /**
     * 获取文件扩展名
     */
    getFileExtension(filename) {
        return filename.slice((filename.lastIndexOf('.') - 1 >>> 0) + 2);
    },
    
    /**
     * 获取文件名（不含扩展名）
     */
    getFileName(filename) {
        return filename.replace(/\.[^/.]+$/, '');
    },
    
    /**
     * 验证文件类型
     */
    validateFileType(filename, allowedTypes) {
        const extension = this.getFileExtension(filename).toLowerCase();
        return allowedTypes.includes(extension);
    },
    
    /**
     * 读取文件内容
     */
    readFileAsText(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = e => resolve(e.target.result);
            reader.onerror = e => reject(e);
            reader.readAsText(file);
        });
    },
    
    /**
     * 下载文件
     */
    downloadFile(url, filename) {
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    },
    
    /**
     * 下载文本内容为文件
     */
    downloadTextAsFile(content, filename, mimeType = 'text/plain') {
        const blob = new Blob([content], { type: mimeType });
        const url = URL.createObjectURL(blob);
        this.downloadFile(url, filename);
        URL.revokeObjectURL(url);
    }
};

/**
 * 验证工具
 */
const ValidationUtils = {
    /**
     * 验证邮箱
     */
    isEmail(email) {
        const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return regex.test(email);
    },
    
    /**
     * 验证URL
     */
    isUrl(url) {
        try {
            new URL(url);
            return true;
        } catch {
            return false;
        }
    },
    
    /**
     * 验证Git URL
     */
    isGitUrl(url) {
        const gitRegex = /^(https?:\/\/|git@)[\w\.-]+[\/:][\w\.-]+\.git$/;
        return gitRegex.test(url);
    },
    
    /**
     * 验证IP地址
     */
    isIpAddress(ip) {
        const ipRegex = /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;
        return ipRegex.test(ip);
    },
    
    /**
     * 验证端口号
     */
    isPort(port) {
        const portNum = parseInt(port);
        return !isNaN(portNum) && portNum >= 1 && portNum <= 65535;
    }
};

/**
 * 存储工具
 */
const StorageUtils = {
    /**
     * 设置localStorage
     */
    setLocal(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
            return true;
        } catch (error) {
            console.error('localStorage set error:', error);
            return false;
        }
    },
    
    /**
     * 获取localStorage
     */
    getLocal(key, defaultValue = null) {
        try {
            const value = localStorage.getItem(key);
            return value ? JSON.parse(value) : defaultValue;
        } catch (error) {
            console.error('localStorage get error:', error);
            return defaultValue;
        }
    },
    
    /**
     * 删除localStorage
     */
    removeLocal(key) {
        try {
            localStorage.removeItem(key);
            return true;
        } catch (error) {
            console.error('localStorage remove error:', error);
            return false;
        }
    },
    
    /**
     * 清空localStorage
     */
    clearLocal() {
        try {
            localStorage.clear();
            return true;
        } catch (error) {
            console.error('localStorage clear error:', error);
            return false;
        }
    },
    
    /**
     * 设置sessionStorage
     */
    setSession(key, value) {
        try {
            sessionStorage.setItem(key, JSON.stringify(value));
            return true;
        } catch (error) {
            console.error('sessionStorage set error:', error);
            return false;
        }
    },
    
    /**
     * 获取sessionStorage
     */
    getSession(key, defaultValue = null) {
        try {
            const value = sessionStorage.getItem(key);
            return value ? JSON.parse(value) : defaultValue;
        } catch (error) {
            console.error('sessionStorage get error:', error);
            return defaultValue;
        }
    }
};

/**
 * 防抖和节流工具
 */
const ThrottleUtils = {
    /**
     * 防抖函数
     */
    debounce(func, wait, immediate = false) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                timeout = null;
                if (!immediate) func.apply(this, args);
            };
            const callNow = immediate && !timeout;
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
            if (callNow) func.apply(this, args);
        };
    },
    
    /**
     * 节流函数
     */
    throttle(func, limit) {
        let inThrottle;
        return function executedFunction(...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }
};

// 导出工具对象
window.DOM = DOM;
window.StringUtils = StringUtils;
window.TimeUtils = TimeUtils;
window.FileUtils = FileUtils;
window.ValidationUtils = ValidationUtils;
window.StorageUtils = StorageUtils;
window.ThrottleUtils = ThrottleUtils;
