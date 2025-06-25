"""
用户管理模块
支持多用户系统，每个用户独立的编译环境
"""

import os
import json
import hashlib
import secrets
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import jwt

from utils.logger import setup_logger


class UserManager:
    """用户管理器"""
    
    def __init__(self, config, logger=None):
        self.config = config
        self.logger = logger or setup_logger(__name__)
        self.users_dir = Path(config.WORKSPACE_DIR) / "users"
        self.users_config_file = self.users_dir / "users.json"
        self.secret_key = config.SECRET_KEY
        
        # 确保用户目录存在
        self.users_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化用户配置
        self._init_users_config()
    
    def _init_users_config(self):
        """初始化用户配置文件"""
        if not self.users_config_file.exists():
            default_config = {
                "users": {},
                "settings": {
                    "require_admin_approval": False,
                    "max_users": 100,
                    "session_timeout": 24 * 60 * 60,  # 24小时
                    "password_min_length": 6
                }
            }
            self._save_users_config(default_config)
    
    def _load_users_config(self) -> Dict:
        """加载用户配置"""
        try:
            with open(self.users_config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"users": {}, "settings": {}}
    
    def _save_users_config(self, config: Dict):
        """保存用户配置"""
        with open(self.users_config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    
    def _hash_password(self, password: str) -> str:
        """密码哈希"""
        salt = secrets.token_hex(16)
        pwd_hash = hashlib.pbkdf2_hmac('sha256', 
                                      password.encode('utf-8'), 
                                      salt.encode('utf-8'), 
                                      100000)
        return f"{salt}:{pwd_hash.hex()}"
    
    def _verify_password(self, password: str, hashed: str) -> bool:
        """验证密码"""
        try:
            salt, pwd_hash = hashed.split(':')
            return hashlib.pbkdf2_hmac('sha256',
                                     password.encode('utf-8'),
                                     salt.encode('utf-8'),
                                     100000).hex() == pwd_hash
        except ValueError:
            return False
    
    def create_user(self, username: str, password: str, email: str = "", 
                   is_admin: bool = False) -> Dict[str, Any]:
        """创建用户"""
        config = self._load_users_config()
        
        # 检查用户是否已存在
        if username in config["users"]:
            raise ValueError(f"用户 {username} 已存在")
        
        # 检查用户数量限制
        if len(config["users"]) >= config["settings"].get("max_users", 100):
            raise ValueError("用户数量已达上限")
        
        # 验证密码长度
        min_length = config["settings"].get("password_min_length", 6)
        if len(password) < min_length:
            raise ValueError(f"密码长度至少需要 {min_length} 位")
        
        # 创建用户数据
        user_data = {
            "username": username,
            "email": email,
            "password_hash": self._hash_password(password),
            "is_admin": is_admin,
            "is_active": True,
            "created_at": datetime.now().isoformat(),
            "last_login": None,
            "settings": {
                "git_url": "https://github.com/coolsnowwolf/lede",
                "git_branch": "master",
                "enable_istore": True,
                "compile_threads": "auto",
                "enable_ccache": True,
                "email_notifications": bool(email)
            },
            "statistics": {
                "total_compile_time": 0,  # 总编译时间（秒）
                "total_compiles": 0,      # 总编译次数
                "successful_compiles": 0,  # 成功编译次数
                "failed_compiles": 0,     # 失败编译次数
                "last_compile_time": None, # 最后编译时间
                "average_compile_time": 0, # 平均编译时间
                "total_login_time": 0,    # 总登录时间
                "login_count": 0,         # 登录次数
                "last_activity": None     # 最后活动时间
            },
            "compile_sessions": []  # 编译会话记录
        }
        
        # 保存用户
        config["users"][username] = user_data
        self._save_users_config(config)
        
        # 创建用户工作空间
        self._create_user_workspace(username)
        
        self.logger.info(f"用户 {username} 创建成功")
        
        # 返回用户信息（不包含密码）
        user_info = user_data.copy()
        del user_info["password_hash"]
        return user_info
    
    def _create_user_workspace(self, username: str):
        """创建用户工作空间"""
        user_dir = self.users_dir / username
        user_dir.mkdir(exist_ok=True)
        
        # 创建子目录
        subdirs = ["lede", "configs", "firmware", "output", "temp", "uploads"]
        for subdir in subdirs:
            (user_dir / subdir).mkdir(exist_ok=True)
        
        # 创建用户配置文件
        user_config = {
            "username": username,
            "workspace_path": str(user_dir),
            "git_url": "https://github.com/coolsnowwolf/lede.git",
            "git_branch": "master",
            "enable_istore": True,
            "compile_settings": {
                "threads": "auto",
                "enable_ccache": True,
                "clean_build": False
            },
            "device_configs": {},
            "build_history": []
        }
        
        config_file = user_dir / "config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(user_config, f, indent=2, ensure_ascii=False)
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """用户认证"""
        config = self._load_users_config()
        
        if username not in config["users"]:
            return None
        
        user_data = config["users"][username]
        
        if not user_data.get("is_active", True):
            return None
        
        if not self._verify_password(password, user_data["password_hash"]):
            return None
        
        # 更新登录统计
        now = datetime.now().isoformat()
        user_data["last_login"] = now
        user_data["statistics"]["login_count"] += 1
        user_data["statistics"]["last_activity"] = now

        config["users"][username] = user_data
        self._save_users_config(config)
        
        # 返回用户信息（不包含密码）
        user_info = user_data.copy()
        del user_info["password_hash"]
        
        self.logger.info(f"用户 {username} 登录成功")
        return user_info
    
    def generate_token(self, username: str) -> str:
        """生成JWT令牌"""
        config = self._load_users_config()
        timeout = config["settings"].get("session_timeout", 24 * 60 * 60)
        
        payload = {
            "username": username,
            "exp": datetime.utcnow() + timedelta(seconds=timeout),
            "iat": datetime.utcnow()
        }
        
        return jwt.encode(payload, self.secret_key, algorithm="HS256")
    
    def verify_token(self, token: str) -> Optional[str]:
        """验证JWT令牌"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            return payload.get("username")
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        """获取用户信息"""
        config = self._load_users_config()
        
        if username not in config["users"]:
            return None
        
        user_data = config["users"][username].copy()
        del user_data["password_hash"]
        return user_data
    
    def list_users(self) -> List[Dict[str, Any]]:
        """列出所有用户"""
        config = self._load_users_config()
        users = []
        
        for username, user_data in config["users"].items():
            user_info = user_data.copy()
            del user_info["password_hash"]
            users.append(user_info)
        
        return users
    
    def update_user_settings(self, username: str, settings: Dict[str, Any]) -> bool:
        """更新用户设置"""
        config = self._load_users_config()
        
        if username not in config["users"]:
            return False
        
        user_data = config["users"][username]
        user_data["settings"].update(settings)
        
        config["users"][username] = user_data
        self._save_users_config(config)
        
        self.logger.info(f"用户 {username} 设置已更新")
        return True
    
    def get_user_workspace(self, username: str) -> Optional[Path]:
        """获取用户工作空间路径"""
        if not self.user_exists(username):
            return None
        
        return self.users_dir / username
    
    def user_exists(self, username: str) -> bool:
        """检查用户是否存在"""
        config = self._load_users_config()
        return username in config["users"]
    
    def is_admin(self, username: str) -> bool:
        """检查用户是否为管理员"""
        config = self._load_users_config()
        
        if username not in config["users"]:
            return False
        
        return config["users"][username].get("is_admin", False)
    
    def has_users(self) -> bool:
        """检查是否有用户"""
        config = self._load_users_config()
        return len(config["users"]) > 0

    def start_compile_session(self, username: str, task_id: str, config_data: Dict[str, Any]) -> str:
        """开始编译会话"""
        config = self._load_users_config()

        if username not in config["users"]:
            return None

        session_id = f"compile_{int(time.time())}_{secrets.token_hex(4)}"
        session = {
            "session_id": session_id,
            "task_id": task_id,
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "duration": 0,
            "status": "running",
            "config": config_data,
            "result": None
        }

        user_data = config["users"][username]
        user_data["compile_sessions"].append(session)
        user_data["statistics"]["last_activity"] = datetime.now().isoformat()

        config["users"][username] = user_data
        self._save_users_config(config)

        self.logger.info(f"用户 {username} 开始编译会话: {session_id}")
        return session_id

    def end_compile_session(self, username: str, session_id: str, success: bool, result: Dict[str, Any] = None):
        """结束编译会话"""
        config = self._load_users_config()

        if username not in config["users"]:
            return False

        user_data = config["users"][username]

        # 查找并更新会话
        for session in user_data["compile_sessions"]:
            if session["session_id"] == session_id:
                end_time = datetime.now()
                start_time = datetime.fromisoformat(session["start_time"])
                duration = int((end_time - start_time).total_seconds())

                session["end_time"] = end_time.isoformat()
                session["duration"] = duration
                session["status"] = "success" if success else "failed"
                session["result"] = result or {}

                # 更新统计信息
                stats = user_data["statistics"]
                stats["total_compiles"] += 1
                stats["total_compile_time"] += duration
                stats["last_compile_time"] = end_time.isoformat()
                stats["last_activity"] = end_time.isoformat()

                if success:
                    stats["successful_compiles"] += 1
                else:
                    stats["failed_compiles"] += 1

                # 计算平均编译时间
                if stats["total_compiles"] > 0:
                    stats["average_compile_time"] = stats["total_compile_time"] / stats["total_compiles"]

                break

        config["users"][username] = user_data
        self._save_users_config(config)

        self.logger.info(f"用户 {username} 编译会话结束: {session_id}, 成功: {success}")
        return True

    def get_user_statistics(self, username: str) -> Optional[Dict[str, Any]]:
        """获取用户统计信息"""
        config = self._load_users_config()

        if username not in config["users"]:
            return None

        user_data = config["users"][username]
        stats = user_data["statistics"].copy()

        # 格式化时间显示
        if stats["total_compile_time"] > 0:
            hours = stats["total_compile_time"] // 3600
            minutes = (stats["total_compile_time"] % 3600) // 60
            stats["total_compile_time_formatted"] = f"{hours}小时{minutes}分钟"
        else:
            stats["total_compile_time_formatted"] = "0分钟"

        if stats["average_compile_time"] > 0:
            avg_minutes = int(stats["average_compile_time"] // 60)
            stats["average_compile_time_formatted"] = f"{avg_minutes}分钟"
        else:
            stats["average_compile_time_formatted"] = "0分钟"

        # 计算成功率
        if stats["total_compiles"] > 0:
            stats["success_rate"] = round((stats["successful_compiles"] / stats["total_compiles"]) * 100, 1)
        else:
            stats["success_rate"] = 0

        return stats

    def get_user_compile_history(self, username: str, limit: int = 10) -> List[Dict[str, Any]]:
        """获取用户编译历史"""
        config = self._load_users_config()

        if username not in config["users"]:
            return []

        user_data = config["users"][username]
        sessions = user_data["compile_sessions"]

        # 按时间倒序排列，返回最近的记录
        sorted_sessions = sorted(sessions, key=lambda x: x["start_time"], reverse=True)
        return sorted_sessions[:limit]

    def update_user_activity(self, username: str):
        """更新用户活动时间"""
        config = self._load_users_config()

        if username not in config["users"]:
            return False

        user_data = config["users"][username]
        user_data["statistics"]["last_activity"] = datetime.now().isoformat()

        config["users"][username] = user_data
        self._save_users_config(config)

        return True
