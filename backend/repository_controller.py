"""
仓库控制器
提供独立的仓库管理API接口
"""

from flask import Blueprint, request, jsonify
from typing import Dict, Any
import threading
import time

from utils.logger import setup_logger
from utils import success_response, error_response


class RepositoryController:
    """仓库控制器"""
    
    def __init__(self, repository_manager, user_manager, logger=None):
        self.repository_manager = repository_manager
        self.user_manager = user_manager
        self.logger = logger or setup_logger(__name__)
        
        # 操作锁，防止并发操作
        self._operation_lock = threading.Lock()
        self._current_operations = {}  # 用户当前操作状态
    
    def clone_repository(self, username: str, force_rebuild: bool = False, 
                        enable_istore: bool = True) -> Dict[str, Any]:
        """克隆仓库"""
        try:
            # 检查用户权限
            if not self.user_manager.user_exists(username):
                return error_response("用户不存在", 404)
            
            # 检查是否有正在进行的操作
            if username in self._current_operations:
                return error_response("用户已有正在进行的仓库操作", 409)
            
            with self._operation_lock:
                self._current_operations[username] = "cloning"
            
            try:
                # 进度回调函数
                def progress_callback(stage, message):
                    self.logger.info(f"[{username}] {stage}: {message}")
                    # 更新用户活动时间
                    self.user_manager.update_user_activity(username)
                
                # 执行克隆
                result = self.repository_manager.clone_repository(
                    username=username,
                    force_rebuild=force_rebuild,
                    enable_istore=enable_istore,
                    progress_callback=progress_callback
                )
                
                if result["success"]:
                    self.logger.info(f"用户 {username} 仓库克隆成功")
                    return success_response(result, "仓库克隆成功")
                else:
                    self.logger.error(f"用户 {username} 仓库克隆失败: {result['message']}")
                    return error_response(result["message"], 500)
                    
            finally:
                # 清除操作状态
                with self._operation_lock:
                    self._current_operations.pop(username, None)
                    
        except Exception as e:
            error_msg = f"克隆仓库时发生错误: {e}"
            self.logger.error(error_msg)
            
            # 清除操作状态
            with self._operation_lock:
                self._current_operations.pop(username, None)
            
            return error_response(error_msg, 500)
    
    def update_repository(self, username: str, enable_istore: bool = True) -> Dict[str, Any]:
        """更新仓库"""
        try:
            # 检查用户权限
            if not self.user_manager.user_exists(username):
                return error_response("用户不存在", 404)
            
            # 检查是否有正在进行的操作
            if username in self._current_operations:
                return error_response("用户已有正在进行的仓库操作", 409)
            
            with self._operation_lock:
                self._current_operations[username] = "updating"
            
            try:
                # 进度回调函数
                def progress_callback(stage, message):
                    self.logger.info(f"[{username}] {stage}: {message}")
                    # 更新用户活动时间
                    self.user_manager.update_user_activity(username)
                
                # 执行更新
                result = self.repository_manager.update_repository(
                    username=username,
                    enable_istore=enable_istore,
                    progress_callback=progress_callback
                )
                
                if result["success"]:
                    self.logger.info(f"用户 {username} 仓库更新成功")
                    return success_response(result, "仓库更新成功")
                else:
                    self.logger.error(f"用户 {username} 仓库更新失败: {result['message']}")
                    return error_response(result["message"], 500)
                    
            finally:
                # 清除操作状态
                with self._operation_lock:
                    self._current_operations.pop(username, None)
                    
        except Exception as e:
            error_msg = f"更新仓库时发生错误: {e}"
            self.logger.error(error_msg)
            
            # 清除操作状态
            with self._operation_lock:
                self._current_operations.pop(username, None)
            
            return error_response(error_msg, 500)
    
    def rebuild_repository(self, username: str, enable_istore: bool = True) -> Dict[str, Any]:
        """重构仓库（完全重新克隆）"""
        return self.clone_repository(username, force_rebuild=True, enable_istore=enable_istore)
    
    def get_repository_status(self, username: str) -> Dict[str, Any]:
        """获取仓库状态"""
        try:
            # 检查用户权限
            if not self.user_manager.user_exists(username):
                return error_response("用户不存在", 404)
            
            # 获取仓库信息
            repo_info = self.repository_manager.get_repository_info(username)
            
            # 添加当前操作状态
            current_operation = self._current_operations.get(username)
            repo_info["current_operation"] = current_operation
            repo_info["is_busy"] = current_operation is not None
            
            return success_response(repo_info, "仓库状态获取成功")
            
        except Exception as e:
            error_msg = f"获取仓库状态时发生错误: {e}"
            self.logger.error(error_msg)
            return error_response(error_msg, 500)
    
    def get_all_repository_status(self) -> Dict[str, Any]:
        """获取所有用户的仓库状态（管理员功能）"""
        try:
            # 获取所有用户
            users = self.user_manager.list_users()
            
            status_list = []
            for user in users:
                username = user["username"]
                repo_info = self.repository_manager.get_repository_info(username)
                
                # 添加用户信息和操作状态
                repo_info["username"] = username
                repo_info["current_operation"] = self._current_operations.get(username)
                repo_info["is_busy"] = username in self._current_operations
                
                status_list.append(repo_info)
            
            return success_response({
                "repositories": status_list,
                "total_users": len(users),
                "active_operations": len(self._current_operations)
            }, "所有仓库状态获取成功")
            
        except Exception as e:
            error_msg = f"获取所有仓库状态时发生错误: {e}"
            self.logger.error(error_msg)
            return error_response(error_msg, 500)
    
    def cancel_operation(self, username: str) -> Dict[str, Any]:
        """取消当前操作"""
        try:
            # 检查用户权限
            if not self.user_manager.user_exists(username):
                return error_response("用户不存在", 404)
            
            # 检查是否有正在进行的操作
            if username not in self._current_operations:
                return error_response("用户没有正在进行的操作", 400)
            
            # 尝试取消操作（这里可以扩展具体的取消逻辑）
            operation = self._current_operations.get(username)
            
            with self._operation_lock:
                self._current_operations.pop(username, None)
            
            self.logger.info(f"用户 {username} 的操作 {operation} 已取消")
            
            return success_response({
                "cancelled_operation": operation
            }, "操作已取消")
            
        except Exception as e:
            error_msg = f"取消操作时发生错误: {e}"
            self.logger.error(error_msg)
            return error_response(error_msg, 500)


def create_repository_blueprint(repository_controller, user_manager):
    """创建仓库管理蓝图"""
    bp = Blueprint('repository', __name__, url_prefix='/api/repository')
    
    def require_auth(f):
        """认证装饰器"""
        def decorated_function(*args, **kwargs):
            # 这里应该实现JWT认证逻辑
            # 暂时简化处理
            username = request.headers.get('X-Username')
            if not username:
                return error_response("需要认证", 401)
            return f(username, *args, **kwargs)
        decorated_function.__name__ = f.__name__
        return decorated_function
    
    @bp.route('/clone', methods=['POST'])
    @require_auth
    def clone_repository(username):
        """克隆仓库"""
        data = request.get_json() or {}
        force_rebuild = data.get('force_rebuild', False)
        enable_istore = data.get('enable_istore', True)
        
        return repository_controller.clone_repository(username, force_rebuild, enable_istore)
    
    @bp.route('/update', methods=['POST'])
    @require_auth
    def update_repository(username):
        """更新仓库"""
        data = request.get_json() or {}
        enable_istore = data.get('enable_istore', True)
        
        return repository_controller.update_repository(username, enable_istore)
    
    @bp.route('/rebuild', methods=['POST'])
    @require_auth
    def rebuild_repository(username):
        """重构仓库"""
        data = request.get_json() or {}
        enable_istore = data.get('enable_istore', True)
        
        return repository_controller.rebuild_repository(username, enable_istore)
    
    @bp.route('/status', methods=['GET'])
    @require_auth
    def get_repository_status(username):
        """获取仓库状态"""
        return repository_controller.get_repository_status(username)
    
    @bp.route('/status/all', methods=['GET'])
    @require_auth
    def get_all_repository_status(username):
        """获取所有仓库状态（管理员功能）"""
        # 检查管理员权限
        if not user_manager.is_admin(username):
            return error_response("需要管理员权限", 403)
        
        return repository_controller.get_all_repository_status()
    
    @bp.route('/cancel', methods=['POST'])
    @require_auth
    def cancel_operation(username):
        """取消当前操作"""
        return repository_controller.cancel_operation(username)
    
    return bp
