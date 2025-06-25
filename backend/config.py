"""
OpenWrt Compiler Backend Configuration
应用配置管理模块
"""

import os
from pathlib import Path
from datetime import timedelta

class Config:
    """基础配置类"""
    
    # 基础配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'openwrt-compiler-secret-key-2024'
    
    # Flask配置
    DEBUG = False
    TESTING = False

    # 服务器配置
    HOST = "0.0.0.0"
    PORT = 5000  # 后端API端口
    FRONTEND_PORT = 9963  # 前端服务端口
    
    # SocketIO配置
    SOCKETIO_ASYNC_MODE = 'threading'
    SOCKETIO_CORS_ALLOWED_ORIGINS = "*"
    SOCKETIO_PING_TIMEOUT = 60
    SOCKETIO_PING_INTERVAL = 25
    
    # CORS配置
    CORS_ORIGINS = ["*"]
    CORS_METHODS = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    CORS_ALLOW_HEADERS = ["Content-Type", "Authorization"]
    
    # 项目路径配置
    BASE_DIR = Path(__file__).parent.parent
    WORKSPACE_DIR = BASE_DIR / "workspace"
    LEDE_DIR = WORKSPACE_DIR / "lede"
    CONFIGS_DIR = WORKSPACE_DIR / "configs"
    OUTPUT_DIR = WORKSPACE_DIR / "output"
    
    # Git仓库配置
    LEDE_REPO_URL = "https://github.com/coolsnowwolf/lede"
    LEDE_BRANCH = "master"
    ISTORE_REPO_URL = "https://github.com/linkease/istore"
    ISTORE_BRANCH = "main"

    # 编译配置
    MAX_COMPILE_JOBS = os.cpu_count() or 4
    COMPILE_TIMEOUT = 3600 * 8  # 8小时超时
    DOWNLOAD_JOBS = 8  # make download并发数
    ENABLE_CCACHE = True

    # 用户管理配置
    USER_SESSION_TIMEOUT = timedelta(hours=24)
    MAX_USERS = 100
    PASSWORD_MIN_LENGTH = 6
    ENABLE_USER_TIMING = True

    # 邮箱通知配置
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    ENABLE_MAIL_NOTIFICATIONS = bool(MAIL_USERNAME and MAIL_PASSWORD)

    # 文件下载配置
    DOWNLOAD_BASE_URL = os.environ.get('DOWNLOAD_BASE_URL', 'http://localhost:9963')
    FIRMWARE_RETENTION_DAYS = 7  # 固件保留天数
    
    # 日志配置
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE = BASE_DIR / "logs" / "app.log"
    
    # API配置
    API_PREFIX = "/api"
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB
    
    @staticmethod
    def init_app(app):
        """初始化应用配置"""
        # 创建必要的目录
        os.makedirs(Config.WORKSPACE_DIR, exist_ok=True)
        os.makedirs(Config.CONFIGS_DIR, exist_ok=True)
        os.makedirs(Config.OUTPUT_DIR, exist_ok=True)
        os.makedirs(Config.LOG_FILE.parent, exist_ok=True)


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    LOG_LEVEL = "DEBUG"


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    LOG_LEVEL = "WARNING"
    
    # 生产环境安全配置
    SOCKETIO_CORS_ALLOWED_ORIGINS = [
        "http://localhost:*",
        "file://*"
    ]


class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    DEBUG = True
    LOG_LEVEL = "DEBUG"


# 配置字典
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
