# OpenWrt 编译器开发指南

本文档为开发者提供详细的开发环境搭建、代码规范、测试指南和贡献流程。

## 🛠️ 开发环境搭建

### 前置要求

#### 系统要求
- **操作系统**: Windows 10+, macOS 10.15+, Ubuntu 18.04+
- **Python**: 3.8+ (推荐3.9+)
- **Node.js**: 16+ (用于前端工具)
- **Git**: 2.20+
- **IDE**: VS Code, PyCharm, 或其他支持Python的IDE

#### 开发工具
```bash
# Python开发工具
pip install black flake8 pytest pytest-cov mypy

# 前端开发工具 (可选)
npm install -g prettier eslint live-server

# Git工具
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

### 环境搭建步骤

#### 1. 克隆仓库
```bash
git clone https://github.com/your-username/openwrt-compiler.git
cd openwrt-compiler

# 添加上游仓库
git remote add upstream https://github.com/original-repo/openwrt-compiler.git
```

#### 2. 创建开发环境
```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate     # Windows

# 安装开发依赖
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

#### 3. 配置开发环境
```bash
# 复制开发配置
cp .env.example .env.dev

# 编辑开发配置
nano .env.dev
```

开发配置示例 (`.env.dev`):
```bash
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=dev-secret-key
HOST=127.0.0.1
PORT=5000
LOG_LEVEL=DEBUG
WORKSPACE_DIR=./workspace
```

#### 4. 初始化开发数据
```bash
# 创建工作目录
mkdir -p workspace/{lede,configs,firmware,uploads,temp}
mkdir -p logs

# 创建测试配置
python scripts/create_test_data.py
```

#### 5. 启动开发服务器
```bash
# 启动后端服务
cd backend
python app.py --config ../.env.dev

# 启动前端开发服务器 (新终端)
cd frontend
python -m http.server 8080
# 或使用Node.js
npx serve . -p 8080
```

## 📁 项目结构详解

### 后端结构
```
backend/
├── app.py                 # Flask应用入口
├── config.py              # 配置管理
├── compiler.py            # 编译管理器
├── config_manager.py      # 配置文件管理
├── file_manager.py        # 文件服务管理
├── websocket_handler.py   # WebSocket处理器
├── templates/             # 配置模板
│   ├── x86_64.json        # x86_64架构模板
│   ├── raspberry_pi.json  # 树莓派模板
│   └── router_generic.json # 通用路由器模板
├── utils/                 # 工具模块
│   ├── __init__.py
│   ├── logger.py          # 日志管理
│   ├── response.py        # API响应封装
│   ├── git_helper.py      # Git操作辅助
│   ├── process_manager.py # 进程管理
│   ├── config_parser.py   # 配置解析器
│   ├── message_queue.py   # 消息队列管理
│   └── file_helper.py     # 文件操作辅助
└── tests/                 # 后端测试
    ├── __init__.py
    ├── test_app.py
    ├── test_compiler.py
    └── test_utils.py
```

### 前端结构
```
frontend/
├── index.html             # 主页面
├── assets/
│   ├── css/
│   │   └── style.css      # 主样式文件
│   ├── js/
│   │   ├── app.js         # 主应用逻辑
│   │   ├── api.js         # API调用封装
│   │   ├── utils.js       # 工具函数库
│   │   └── websocket.js   # WebSocket管理器
│   └── images/            # 图片资源
└── tests/                 # 前端测试
    ├── test-runner.html
    └── tests.js
```

## 📝 代码规范

### Python代码规范

#### 1. 代码风格
遵循 [PEP 8](https://www.python.org/dev/peps/pep-0008/) 规范:

```python
# 好的示例
class CompilerManager:
    """编译管理器类"""
    
    def __init__(self, config, logger=None):
        self.config = config
        self.logger = logger
        self._running = False
    
    def start_compile(self, config_name: str, options: dict) -> dict:
        """
        开始编译
        
        Args:
            config_name: 配置名称
            options: 编译选项
        
        Returns:
            dict: 编译结果
        """
        try:
            # 实现逻辑
            return {"success": True}
        except Exception as e:
            self.logger.error(f"编译失败: {e}")
            return {"success": False, "error": str(e)}
```

#### 2. 类型注解
使用类型注解提高代码可读性:

```python
from typing import Dict, List, Optional, Union

def process_config(config_data: str, 
                  metadata: Optional[Dict[str, str]] = None) -> Dict[str, Union[str, bool]]:
    """处理配置数据"""
    pass
```

#### 3. 文档字符串
使用Google风格的文档字符串:

```python
def compile_firmware(config_name: str, target: str = "all") -> Dict[str, Any]:
    """
    编译固件
    
    Args:
        config_name: 配置文件名称
        target: 编译目标，可选值: all, kernel, packages
    
    Returns:
        包含编译结果的字典，格式如下:
        {
            "success": bool,
            "task_id": str,
            "message": str
        }
    
    Raises:
        CompileError: 当编译配置无效时
        FileNotFoundError: 当配置文件不存在时
    """
    pass
```

### JavaScript代码规范

#### 1. ES6+语法
使用现代JavaScript语法:

```javascript
// 使用const/let而不是var
const API_BASE_URL = 'http://localhost:5000/api';
let currentStatus = 'idle';

// 使用箭头函数
const fetchData = async (endpoint) => {
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`);
        return await response.json();
    } catch (error) {
        console.error('API调用失败:', error);
        throw error;
    }
};

// 使用解构赋值
const { success, data, message } = await fetchData('/status');
```

#### 2. 类和模块
使用ES6类和模块:

```javascript
// api.js
export class APIClient {
    constructor(baseUrl) {
        this.baseUrl = baseUrl;
    }
    
    async call(endpoint, options = {}) {
        // 实现逻辑
    }
}

// app.js
import { APIClient } from './api.js';

class OpenWrtCompiler {
    constructor() {
        this.api = new APIClient('/api');
    }
}
```

#### 3. 错误处理
统一的错误处理模式:

```javascript
class APIError extends Error {
    constructor(message, status, data) {
        super(message);
        this.name = 'APIError';
        this.status = status;
        this.data = data;
    }
}

async function safeApiCall(apiFunction) {
    try {
        return await apiFunction();
    } catch (error) {
        if (error instanceof APIError) {
            showNotification('错误', error.message, 'error');
        } else {
            showNotification('错误', '网络连接失败', 'error');
        }
        throw error;
    }
}
```

### CSS代码规范

#### 1. 命名规范
使用BEM命名方法:

```css
/* 块 */
.compiler-panel {
    display: flex;
    flex-direction: column;
}

/* 元素 */
.compiler-panel__header {
    padding: 1rem;
    background-color: var(--bg-secondary);
}

/* 修饰符 */
.compiler-panel--collapsed {
    height: auto;
}

.compiler-panel__button--primary {
    background-color: var(--primary-color);
}
```

#### 2. CSS变量
使用CSS自定义属性:

```css
:root {
    --primary-color: #007bff;
    --secondary-color: #6c757d;
    --success-color: #28a745;
    --danger-color: #dc3545;
    
    --font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto;
    --border-radius: 0.375rem;
    --spacing-sm: 0.5rem;
    --spacing-md: 1rem;
}

.button {
    font-family: var(--font-family);
    border-radius: var(--border-radius);
    padding: var(--spacing-sm) var(--spacing-md);
}
```

## 🧪 测试指南

### 后端测试

#### 1. 单元测试
使用pytest进行单元测试:

```python
# tests/test_compiler.py
import pytest
from unittest.mock import Mock, patch
from backend.compiler import CompilerManager

class TestCompilerManager:
    
    @pytest.fixture
    def compiler(self):
        config = Mock()
        logger = Mock()
        return CompilerManager(config, logger)
    
    def test_start_compile_success(self, compiler):
        """测试编译启动成功"""
        result = compiler.start_compile("test_config", {"target": "all"})
        assert result["success"] is True
        assert "task_id" in result
    
    @patch('backend.compiler.subprocess.run')
    def test_start_compile_with_mock(self, mock_run, compiler):
        """使用Mock测试编译过程"""
        mock_run.return_value.returncode = 0
        result = compiler.start_compile("test_config", {})
        assert result["success"] is True
        mock_run.assert_called_once()
```

#### 2. 集成测试
```python
# tests/test_integration.py
import pytest
import requests
from backend.app import create_app

@pytest.fixture
def client():
    app = create_app('testing')
    with app.test_client() as client:
        yield client

def test_api_status(client):
    """测试状态API"""
    response = client.get('/api/status')
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True

def test_compile_workflow(client):
    """测试完整编译流程"""
    # 1. 检查系统状态
    response = client.get('/api/status')
    assert response.status_code == 200
    
    # 2. 开始编译
    response = client.post('/api/compile/start', json={
        'config_name': 'test_config',
        'target': 'all'
    })
    assert response.status_code == 200
    
    # 3. 检查编译状态
    response = client.get('/api/compile/status')
    assert response.status_code == 200
```

#### 3. 运行测试
```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_compiler.py

# 运行测试并生成覆盖率报告
pytest --cov=backend --cov-report=html

# 运行测试并显示详细输出
pytest -v -s
```

### 前端测试

#### 1. 单元测试
使用Jest或简单的测试框架:

```javascript
// tests/test-api.js
describe('APIClient', () => {
    let apiClient;
    
    beforeEach(() => {
        apiClient = new APIClient('/api');
    });
    
    test('should make successful API call', async () => {
        // Mock fetch
        global.fetch = jest.fn(() =>
            Promise.resolve({
                ok: true,
                json: () => Promise.resolve({ success: true, data: {} })
            })
        );
        
        const result = await apiClient.call('/status');
        expect(result.success).toBe(true);
        expect(fetch).toHaveBeenCalledWith('/api/status', expect.any(Object));
    });
    
    test('should handle API errors', async () => {
        global.fetch = jest.fn(() =>
            Promise.resolve({
                ok: false,
                status: 500,
                json: () => Promise.resolve({ message: 'Server Error' })
            })
        );
        
        await expect(apiClient.call('/status')).rejects.toThrow('Server Error');
    });
});
```

#### 2. E2E测试
使用Playwright或Cypress:

```javascript
// tests/e2e/test-compile.js
const { test, expect } = require('@playwright/test');

test('complete compile workflow', async ({ page }) => {
    // 打开应用
    await page.goto('http://localhost:8080');
    
    // 检查页面加载
    await expect(page.locator('h1')).toContainText('OpenWrt 编译器');
    
    // 填写Git仓库地址
    await page.fill('#git-url', 'https://github.com/coolsnowwolf/lede.git');
    
    // 点击克隆按钮
    await page.click('#clone-btn');
    
    // 等待克隆完成
    await expect(page.locator('#clone-progress')).toBeVisible();
    
    // 选择配置模板
    await page.selectOption('#config-template', 'x86_64');
    await page.fill('#config-name', 'test-config');
    await page.click('#apply-template-btn');
    
    // 开始编译
    await page.click('#start-compile-btn');
    
    // 检查编译状态
    await expect(page.locator('#compile-status-text')).toContainText('编译中');
});
```

## 🔧 调试技巧

### 后端调试

#### 1. 使用调试器
```python
# 在代码中设置断点
import pdb; pdb.set_trace()

# 或使用ipdb (更友好的界面)
import ipdb; ipdb.set_trace()
```

#### 2. 日志调试
```python
import logging

# 配置详细日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def some_function():
    logger.debug("函数开始执行")
    logger.info("处理数据: %s", data)
    logger.warning("发现潜在问题")
    logger.error("发生错误: %s", error)
```

#### 3. 性能分析
```python
import cProfile
import pstats

# 性能分析
profiler = cProfile.Profile()
profiler.enable()

# 执行代码
your_function()

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(10)
```

### 前端调试

#### 1. 浏览器开发者工具
```javascript
// 控制台调试
console.log('调试信息:', data);
console.warn('警告信息:', warning);
console.error('错误信息:', error);
console.table(arrayData);

// 断点调试
debugger;

// 性能监控
console.time('API调用');
await apiCall();
console.timeEnd('API调用');
```

#### 2. 网络调试
```javascript
// 拦截fetch请求
const originalFetch = window.fetch;
window.fetch = function(...args) {
    console.log('Fetch请求:', args);
    return originalFetch.apply(this, args)
        .then(response => {
            console.log('Fetch响应:', response);
            return response;
        });
};
```

## 🚀 开发工作流

### Git工作流

#### 1. 功能开发
```bash
# 更新主分支
git checkout main
git pull upstream main

# 创建功能分支
git checkout -b feature/new-feature

# 开发和提交
git add .
git commit -m "feat: 添加新功能"

# 推送分支
git push origin feature/new-feature
```

#### 2. 提交规范
使用[Conventional Commits](https://www.conventionalcommits.org/)规范:

```bash
# 功能
git commit -m "feat: 添加编译进度显示功能"

# 修复
git commit -m "fix: 修复WebSocket连接断开问题"

# 文档
git commit -m "docs: 更新API文档"

# 样式
git commit -m "style: 调整按钮样式"

# 重构
git commit -m "refactor: 重构编译管理器"

# 测试
git commit -m "test: 添加编译器单元测试"

# 构建
git commit -m "build: 更新依赖包版本"
```

### 代码审查

#### 1. 自检清单
- [ ] 代码符合项目规范
- [ ] 添加了必要的测试
- [ ] 更新了相关文档
- [ ] 没有调试代码残留
- [ ] 性能影响可接受
- [ ] 安全性考虑充分

#### 2. Pull Request模板
```markdown
## 变更描述
简要描述本次变更的内容和目的。

## 变更类型
- [ ] 新功能
- [ ] Bug修复
- [ ] 文档更新
- [ ] 性能优化
- [ ] 代码重构

## 测试
- [ ] 单元测试通过
- [ ] 集成测试通过
- [ ] 手动测试完成

## 检查清单
- [ ] 代码符合项目规范
- [ ] 添加了必要的测试
- [ ] 更新了相关文档
- [ ] 考虑了向后兼容性

## 截图/演示
如果有UI变更，请提供截图或演示视频。
```

## 📚 开发资源

### 文档资源
- [Flask官方文档](https://flask.palletsprojects.com/)
- [Socket.IO文档](https://socket.io/docs/)
- [OpenWrt开发指南](https://openwrt.org/docs/guide-developer/start)
- [Python最佳实践](https://docs.python-guide.org/)

### 工具推荐
- **IDE**: VS Code, PyCharm
- **API测试**: Postman, Insomnia
- **数据库**: SQLite Browser
- **版本控制**: Git, GitHub Desktop
- **调试**: Chrome DevTools, Python Debugger

### 社区资源
- [GitHub Issues](https://github.com/your-repo/issues)
- [GitHub Discussions](https://github.com/your-repo/discussions)
- [开发者QQ群](https://qm.qq.com/xxx)
- [技术博客](https://blog.example.com)

## 🤝 贡献流程

### 1. 准备工作
```bash
# Fork项目到你的GitHub账户
# 克隆你的Fork
git clone https://github.com/your-username/openwrt-compiler.git
cd openwrt-compiler

# 添加上游仓库
git remote add upstream https://github.com/original-repo/openwrt-compiler.git
```

### 2. 开发流程
```bash
# 创建功能分支
git checkout -b feature/your-feature-name

# 进行开发
# ... 编写代码 ...

# 运行测试
pytest
npm test

# 提交代码
git add .
git commit -m "feat: 你的功能描述"
git push origin feature/your-feature-name
```

### 3. 提交Pull Request
1. 在GitHub上创建Pull Request
2. 填写详细的PR描述
3. 等待代码审查
4. 根据反馈修改代码
5. 合并到主分支

### 4. 发布流程
```bash
# 更新版本号
echo "1.1.0" > VERSION

# 创建发布标签
git tag -a v1.1.0 -m "Release version 1.1.0"
git push origin v1.1.0

# 创建GitHub Release
# 在GitHub上创建Release，包含更新日志
```

---

**欢迎贡献代码！如有问题，请随时在Issues中提出。**
