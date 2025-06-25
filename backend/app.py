#!/usr/bin/env python3
"""
OpenWrt Compiler Backend Application
OpenWrt编译器后端主应用
"""

import os
import sys
import time
import click
from datetime import datetime
from flask import Flask, request, jsonify
from flask_socketio import SocketIO
from flask_cors import CORS

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import config
from utils import setup_logger, success_response, error_response
from compiler import CompilerManager
from config_manager import ConfigManager
from websocket_handler import WebSocketHandler
from file_manager import FileManager
from user_manager import UserManager
from device_manager import DeviceManager
from web_menuconfig import WebMenuconfig
from repository_manager import RepositoryManager
from email_notifier import EmailNotifier
from repository_controller import RepositoryController, create_repository_blueprint


def create_app(config_name=None):
    """
    应用工厂函数
    
    Args:
        config_name: 配置名称 ('development', 'production', 'testing')
    
    Returns:
        Flask: 配置好的Flask应用实例
    """
    
    # 获取配置名称
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    # 创建Flask应用
    app = Flask(__name__)
    
    # 加载配置
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # 设置日志
    logger = setup_logger(
        'openwrt-compiler',
        log_file=app.config.get('LOG_FILE'),
        log_level=app.config.get('LOG_LEVEL', 'INFO'),
        log_format=app.config.get('LOG_FORMAT')
    )
    
    # 初始化扩展
    socketio = SocketIO(
        app,
        cors_allowed_origins=app.config['SOCKETIO_CORS_ALLOWED_ORIGINS'],
        async_mode=app.config['SOCKETIO_ASYNC_MODE'],
        ping_timeout=app.config['SOCKETIO_PING_TIMEOUT'],
        ping_interval=app.config['SOCKETIO_PING_INTERVAL']
    )
    
    # 配置CORS
    CORS(app, 
         origins=app.config['CORS_ORIGINS'],
         methods=app.config['CORS_METHODS'],
         allow_headers=app.config['CORS_ALLOW_HEADERS'])
    
    # 注册中间件
    @app.before_request
    def before_request():
        """请求前处理"""
        logger.debug(f"Request: {request.method} {request.url}")
    
    @app.after_request
    def after_request(response):
        """请求后处理 - 添加时间戳"""
        if response.is_json:
            try:
                data = response.get_json()
                if isinstance(data, dict) and 'timestamp' in data:
                    data['timestamp'] = datetime.now().isoformat()
                    response.set_data(jsonify(data).data)
            except Exception:
                pass
        return response
    
    # 全局错误处理
    @app.errorhandler(404)
    def not_found(error):
        """404错误处理"""
        return error_response("API endpoint not found", 404, "NOT_FOUND")
    
    @app.errorhandler(500)
    def internal_error(error):
        """500错误处理"""
        logger.error(f"Internal server error: {error}")
        return error_response("Internal server error", 500, "INTERNAL_ERROR")
    
    @app.errorhandler(Exception)
    def handle_exception(error):
        """通用异常处理"""
        logger.error(f"Unhandled exception: {error}")
        return error_response("An unexpected error occurred", 500, "UNEXPECTED_ERROR")
    
    # 注册API路由
    register_api_routes(app, logger)
    
    # SocketIO事件由WebSocket处理器管理
    
    # 存储socketio实例供其他模块使用
    app.socketio = socketio

    # 初始化WebSocket处理器
    app.websocket_handler = WebSocketHandler(socketio, logger)
    app.websocket_handler.start()

    # 初始化用户管理器
    app.user_manager = UserManager(config[config_name], logger)

    # 初始化设备管理器
    app.device_manager = DeviceManager(config[config_name], logger)

    # 初始化Web版menuconfig
    app.web_menuconfig = WebMenuconfig(config[config_name], logger)

    # 初始化仓库管理器
    app.repository_manager = RepositoryManager(config[config_name], logger, app.websocket_handler)

    # 初始化邮件通知器
    app.email_notifier = EmailNotifier(config[config_name], logger)

    # 初始化编译管理器
    app.compiler_manager = CompilerManager(config[config_name], logger, socketio,
                                         app.websocket_handler, app.user_manager)

    # 初始化仓库控制器
    app.repository_controller = RepositoryController(app.repository_manager, app.user_manager, logger)

    # 初始化配置管理器
    app.config_manager = ConfigManager(config[config_name], logger)

    # 初始化文件管理器
    app.file_manager = FileManager(config[config_name], logger)
    app.file_manager.start()

    # 注册仓库管理蓝图
    repository_bp = create_repository_blueprint(app.repository_controller, app.user_manager)
    app.register_blueprint(repository_bp)

    logger.info(f"OpenWrt Compiler Backend (Debian版) initialized with config: {config_name}")

    return app, socketio


def register_api_routes(app, logger):
    """注册API路由"""
    
    api_prefix = app.config['API_PREFIX']
    
    @app.route(f'{api_prefix}/status', methods=['GET'])
    def get_status():
        """获取系统状态"""
        try:
            status_data = {
                "server": "running",
                "version": "1.0.0",
                "config": app.config.get('ENV', 'development'),
                "workspace": str(app.config['WORKSPACE_DIR']),
                "lede_installed": app.config['LEDE_DIR'].exists()
            }
            return success_response(status_data, "System status retrieved successfully")
        except Exception as e:
            logger.error(f"Error getting status: {e}")
            return error_response("Failed to get system status", 500)
    
    @app.route(f'{api_prefix}/configs', methods=['GET'])
    def get_configs():
        """获取配置列表"""
        try:
            result = app.config_manager.list_configs()

            if result['success']:
                return success_response(result, "配置列表获取成功")
            else:
                return error_response(result['message'], 400)

        except Exception as e:
            logger.error(f"获取配置列表API错误: {e}")
            return error_response("获取配置列表时发生错误", 500)
    
    @app.route(f'{api_prefix}/health', methods=['GET'])
    def health_check():
        """健康检查"""
        return success_response({"status": "healthy"}, "Service is healthy")

    # 用户管理API
    @app.route(f'{api_prefix}/auth/register', methods=['POST'])
    def register_user():
        """用户注册"""
        try:
            data = request.get_json() or {}
            username = data.get('username', '').strip()
            password = data.get('password', '')
            email = data.get('email', '').strip()

            if not username or not password:
                return error_response("用户名和密码不能为空", 400)

            # 检查是否为首个用户（自动设为管理员）
            is_admin = not app.user_manager.has_users()

            user_info = app.user_manager.create_user(username, password, email, is_admin)
            token = app.user_manager.generate_token(username)

            return success_response({
                "user": user_info,
                "token": token
            }, "用户注册成功")

        except ValueError as e:
            return error_response(str(e), 400)
        except Exception as e:
            logger.error(f"用户注册API错误: {e}")
            return error_response("注册时发生错误", 500)

    @app.route(f'{api_prefix}/auth/login', methods=['POST'])
    def login_user():
        """用户登录"""
        try:
            data = request.get_json() or {}
            username = data.get('username', '').strip()
            password = data.get('password', '')

            if not username or not password:
                return error_response("用户名和密码不能为空", 400)

            user_info = app.user_manager.authenticate_user(username, password)
            if not user_info:
                return error_response("用户名或密码错误", 401)

            token = app.user_manager.generate_token(username)

            return success_response({
                "user": user_info,
                "token": token
            }, "登录成功")

        except Exception as e:
            logger.error(f"用户登录API错误: {e}")
            return error_response("登录时发生错误", 500)

    # 设备管理API
    @app.route(f'{api_prefix}/devices/search', methods=['GET'])
    def search_devices():
        """搜索设备"""
        try:
            query = request.args.get('q', '').strip()
            limit = int(request.args.get('limit', 20))

            devices = app.device_manager.search_devices(query, limit)
            device_list = [
                {
                    "id": device.id,
                    "name": device.name,
                    "target": device.target,
                    "cpu": device.cpu,
                    "category": device.category,
                    "keywords": device.keywords,
                    "description": device.description
                }
                for device in devices
            ]

            return success_response({
                "devices": device_list,
                "total": len(device_list)
            }, "设备搜索完成")

        except Exception as e:
            logger.error(f"设备搜索API错误: {e}")
            return error_response("搜索设备时发生错误", 500)

    @app.route(f'{api_prefix}/devices/<device_id>/config', methods=['GET'])
    def get_device_config():
        """获取设备配置"""
        try:
            enable_istore = request.args.get('istore', 'true').lower() == 'true'
            custom_packages = request.args.getlist('packages')

            config = app.device_manager.generate_device_config(
                device_id, enable_istore, custom_packages
            )

            return success_response({
                "device_id": device_id,
                "config": config
            }, "设备配置生成成功")

        except ValueError as e:
            return error_response(str(e), 404)
        except Exception as e:
            logger.error(f"获取设备配置API错误: {e}")
            return error_response("获取设备配置时发生错误", 500)

    # Web配置界面API
    @app.route(f'{api_prefix}/config/web', methods=['GET'])
    def get_web_config():
        """获取Web配置界面数据"""
        try:
            device_id = request.args.get('device_id')

            result = app.web_menuconfig.generate_web_config(device_id)

            if result['success']:
                return success_response(result['config'], "Web配置数据获取成功")
            else:
                return error_response(result['message'], 400)

        except Exception as e:
            logger.error(f"获取Web配置API错误: {e}")
            return error_response("获取Web配置时发生错误", 500)

    @app.route(f'{api_prefix}/packages/categories', methods=['GET'])
    def get_package_categories():
        """获取软件包分类"""
        try:
            categories = app.device_manager.get_package_categories()
            return success_response(categories, "软件包分类获取成功")

        except Exception as e:
            logger.error(f"获取软件包分类API错误: {e}")
            return error_response("获取软件包分类时发生错误", 500)

    # 用户统计API
    @app.route(f'{api_prefix}/users/<username>/statistics', methods=['GET'])
    def get_user_statistics(username):
        """获取用户统计信息"""
        try:
            # 这里应该添加认证检查
            if not app.user_manager.user_exists(username):
                return error_response("用户不存在", 404)

            stats = app.user_manager.get_user_statistics(username)
            if stats is None:
                return error_response("获取统计信息失败", 500)

            return success_response(stats, "用户统计信息获取成功")

        except Exception as e:
            logger.error(f"获取用户统计API错误: {e}")
            return error_response("获取用户统计时发生错误", 500)

    @app.route(f'{api_prefix}/users/<username>/compile-history', methods=['GET'])
    def get_user_compile_history(username):
        """获取用户编译历史"""
        try:
            # 这里应该添加认证检查
            if not app.user_manager.user_exists(username):
                return error_response("用户不存在", 404)

            limit = int(request.args.get('limit', 10))
            history = app.user_manager.get_user_compile_history(username, limit)

            return success_response(history, "编译历史获取成功")

        except Exception as e:
            logger.error(f"获取编译历史API错误: {e}")
            return error_response("获取编译历史时发生错误", 500)

    # 编译控制API
    @app.route(f'{api_prefix}/compile/start', methods=['POST'])
    def start_compile():
        """开始编译"""
        try:
            data = request.get_json() or {}
            username = data.get('username')  # 这里应该从认证中获取

            if not username:
                return error_response("缺少用户名", 400)

            if not app.user_manager.user_exists(username):
                return error_response("用户不存在", 404)

            # 检查必要参数
            device_id = data.get('device_id')
            if not device_id:
                return error_response("缺少设备ID", 400)

            # 准备编译配置
            compile_config = {
                "device_id": device_id,
                "device_name": data.get('device_name', '未知设备'),
                "packages": data.get('packages', []),
                "compile_threads": data.get('compile_threads', 'auto'),
                "enable_email_notification": data.get('enable_email_notification', True)
            }

            result = app.compiler_manager.start_compile(username, compile_config)

            if result['success']:
                return success_response(result, "编译任务已启动")
            else:
                return error_response(result['message'], 400)

        except Exception as e:
            logger.error(f"启动编译API错误: {e}")
            return error_response("启动编译时发生错误", 500)

    # 邮件测试API
    @app.route(f'{api_prefix}/email/test', methods=['POST'])
    def test_email():
        """测试邮件配置"""
        try:
            data = request.get_json() or {}
            test_email = data.get('email')

            if not test_email:
                return error_response("缺少测试邮箱地址", 400)

            success = app.email_notifier.test_email_config(test_email)

            if success:
                return success_response({"sent": True}, "测试邮件发送成功")
            else:
                return error_response("测试邮件发送失败", 500)

        except Exception as e:
            logger.error(f"测试邮件API错误: {e}")
            return error_response("测试邮件时发生错误", 500)

    # 编译相关API
    @app.route(f'{api_prefix}/compiler/clone', methods=['POST'])
    def clone_source():
        """克隆LEDE源码"""
        try:
            data = request.get_json() or {}
            force_update = data.get('force_update', False)

            result = app.compiler_manager.clone_source(force_update)

            if result['success']:
                return success_response(result, "源码克隆操作完成")
            else:
                return error_response(result['message'], 400)

        except Exception as e:
            logger.error(f"克隆源码API错误: {e}")
            return error_response("克隆源码时发生错误", 500)

    @app.route(f'{api_prefix}/compiler/feeds/update', methods=['POST'])
    def update_feeds():
        """更新feeds（支持iStore和多用户）"""
        try:
            data = request.get_json() or {}
            enable_istore = data.get('enable_istore', True)
            username = data.get('username')  # 可选的用户名

            result = app.compiler_manager.update_feeds(enable_istore, username)

            if result['success']:
                return success_response(result, "feeds更新完成")
            else:
                return error_response(result['message'], 400)

        except Exception as e:
            logger.error(f"更新feeds API错误: {e}")
            return error_response("更新feeds时发生错误", 500)

    @app.route(f'{api_prefix}/compiler/feeds/install', methods=['POST'])
    def install_feeds():
        """安装feeds"""
        try:
            result = app.compiler_manager.install_feeds()

            if result['success']:
                return success_response(result, "feeds安装完成")
            else:
                return error_response(result['message'], 400)

        except Exception as e:
            logger.error(f"安装feeds API错误: {e}")
            return error_response("安装feeds时发生错误", 500)

    @app.route(f'{api_prefix}/compiler/compile', methods=['POST'])
    def start_compile():
        """开始编译"""
        try:
            data = request.get_json() or {}
            task_id = data.get('task_id', f"compile_{int(time.time())}")
            config = data.get('config', {})

            result = app.compiler_manager.start_compile(task_id, config)

            if result['success']:
                return success_response(result, "编译任务已启动")
            else:
                return error_response(result['message'], 400)

        except Exception as e:
            logger.error(f"启动编译API错误: {e}")
            return error_response("启动编译时发生错误", 500)

    @app.route(f'{api_prefix}/compiler/tasks/<task_id>', methods=['GET'])
    def get_task_status(task_id):
        """获取任务状态"""
        try:
            task_status = app.compiler_manager.get_task_status(task_id)

            if task_status:
                return success_response(task_status, "获取任务状态成功")
            else:
                return error_response("任务不存在", 404)

        except Exception as e:
            logger.error(f"获取任务状态API错误: {e}")
            return error_response("获取任务状态时发生错误", 500)

    @app.route(f'{api_prefix}/compiler/tasks', methods=['GET'])
    def list_tasks():
        """列出所有任务"""
        try:
            tasks = app.compiler_manager.list_tasks()
            return success_response({"tasks": tasks}, "获取任务列表成功")

        except Exception as e:
            logger.error(f"获取任务列表API错误: {e}")
            return error_response("获取任务列表时发生错误", 500)

    @app.route(f'{api_prefix}/compiler/repository', methods=['GET'])
    def get_repository_status():
        """获取仓库状态"""
        try:
            repo_status = app.compiler_manager.get_repository_status()
            return success_response(repo_status, "获取仓库状态成功")

        except Exception as e:
            logger.error(f"获取仓库状态API错误: {e}")
            return error_response("获取仓库状态时发生错误", 500)

    # 配置管理相关API
    @app.route(f'{api_prefix}/config/templates', methods=['GET'])
    def get_templates():
        """获取配置模板列表"""
        try:
            templates = app.config_manager.get_templates()
            return success_response({"templates": templates}, "获取模板列表成功")

        except Exception as e:
            logger.error(f"获取模板列表API错误: {e}")
            return error_response("获取模板列表时发生错误", 500)

    @app.route(f'{api_prefix}/config/templates/<template_id>', methods=['GET'])
    def get_template_config(template_id):
        """获取模板配置"""
        try:
            template_config = app.config_manager.get_template_config(template_id)

            if template_config:
                return success_response(template_config, "获取模板配置成功")
            else:
                return error_response("模板不存在", 404)

        except Exception as e:
            logger.error(f"获取模板配置API错误: {e}")
            return error_response("获取模板配置时发生错误", 500)

    @app.route(f'{api_prefix}/config/apply-template', methods=['POST'])
    def apply_template():
        """应用配置模板"""
        try:
            data = request.get_json() or {}
            template_id = data.get('template_id')
            config_name = data.get('config_name')

            if not template_id:
                return error_response("缺少template_id参数", 400)

            result = app.config_manager.apply_template(template_id, config_name)

            if result['success']:
                return success_response(result, "模板应用成功")
            else:
                return error_response(result['message'], 400)

        except Exception as e:
            logger.error(f"应用模板API错误: {e}")
            return error_response("应用模板时发生错误", 500)

    @app.route(f'{api_prefix}/config/<config_name>', methods=['GET'])
    def get_config(config_name):
        """获取配置详情"""
        try:
            result = app.config_manager.load_config(config_name)

            if result['success']:
                return success_response(result, "获取配置成功")
            else:
                return error_response(result['message'], 404)

        except Exception as e:
            logger.error(f"获取配置API错误: {e}")
            return error_response("获取配置时发生错误", 500)

    @app.route(f'{api_prefix}/config/<config_name>', methods=['PUT'])
    def update_config(config_name):
        """更新配置"""
        try:
            data = request.get_json() or {}
            config_data = data.get('config_data', {})
            metadata = data.get('metadata')

            result = app.config_manager.save_config(config_name, config_data, metadata)

            if result['success']:
                return success_response(result, "配置更新成功")
            else:
                return error_response(result['message'], 400)

        except Exception as e:
            logger.error(f"更新配置API错误: {e}")
            return error_response("更新配置时发生错误", 500)

    @app.route(f'{api_prefix}/config/<config_name>', methods=['DELETE'])
    def delete_config(config_name):
        """删除配置"""
        try:
            result = app.config_manager.delete_config(config_name)

            if result['success']:
                return success_response(result, "配置删除成功")
            else:
                return error_response(result['message'], 400)

        except Exception as e:
            logger.error(f"删除配置API错误: {e}")
            return error_response("删除配置时发生错误", 500)

    # WebSocket相关API
    @app.route(f'{api_prefix}/websocket/clients', methods=['GET'])
    def get_websocket_clients():
        """获取WebSocket客户端列表"""
        try:
            clients = app.websocket_handler.get_connected_clients()
            return success_response({"clients": clients}, "获取客户端列表成功")

        except Exception as e:
            logger.error(f"获取WebSocket客户端API错误: {e}")
            return error_response("获取客户端列表时发生错误", 500)

    @app.route(f'{api_prefix}/websocket/stats', methods=['GET'])
    def get_websocket_stats():
        """获取WebSocket统计信息"""
        try:
            stats = app.websocket_handler.get_stats()
            message_stats = app.websocket_handler.message_queue.get_stats()

            return success_response({
                "websocket_stats": stats,
                "message_queue_stats": message_stats
            }, "获取WebSocket统计信息成功")

        except Exception as e:
            logger.error(f"获取WebSocket统计API错误: {e}")
            return error_response("获取WebSocket统计时发生错误", 500)

    @app.route(f'{api_prefix}/websocket/rooms', methods=['GET'])
    def get_websocket_rooms():
        """获取WebSocket房间信息"""
        try:
            rooms = app.websocket_handler.get_room_info()
            return success_response({"rooms": rooms}, "获取房间信息成功")

        except Exception as e:
            logger.error(f"获取WebSocket房间API错误: {e}")
            return error_response("获取房间信息时发生错误", 500)

    # 文件管理相关API
    @app.route(f'{api_prefix}/files/firmware', methods=['GET'])
    def get_firmware_list():
        """获取固件文件列表"""
        try:
            result = app.file_manager.get_firmware_list()

            if result['success']:
                return success_response(result, "获取固件列表成功")
            else:
                return error_response(result['message'], 400)

        except Exception as e:
            logger.error(f"获取固件列表API错误: {e}")
            return error_response("获取固件列表时发生错误", 500)

    @app.route(f'{api_prefix}/files/configs', methods=['GET'])
    def get_config_files():
        """获取配置文件列表"""
        try:
            result = app.file_manager.get_config_list()

            if result['success']:
                return success_response(result, "获取配置文件列表成功")
            else:
                return error_response(result['message'], 400)

        except Exception as e:
            logger.error(f"获取配置文件列表API错误: {e}")
            return error_response("获取配置文件列表时发生错误", 500)

    @app.route(f'{api_prefix}/files/storage', methods=['GET'])
    def get_storage_info():
        """获取存储空间信息"""
        try:
            result = app.file_manager.get_storage_info()

            if result['success']:
                return success_response(result, "获取存储信息成功")
            else:
                return error_response(result['message'], 400)

        except Exception as e:
            logger.error(f"获取存储信息API错误: {e}")
            return error_response("获取存储信息时发生错误", 500)

    @app.route(f'{api_prefix}/files/<file_type>/<filename>', methods=['GET'])
    def download_file(file_type, filename):
        """下载文件"""
        try:
            return app.file_manager.download_file(file_type, filename)

        except Exception as e:
            logger.error(f"文件下载API错误: {e}")
            return error_response("文件下载时发生错误", 500)

    @app.route(f'{api_prefix}/files/configs/<filename>', methods=['POST'])
    def upload_config_file(filename):
        """上传配置文件"""
        try:
            if 'file' not in request.files:
                return error_response("没有上传文件", 400)

            file = request.files['file']
            if file.filename == '':
                return error_response("没有选择文件", 400)

            overwrite = request.form.get('overwrite', 'false').lower() == 'true'

            result = app.file_manager.upload_config_file(file.stream, filename, overwrite)

            if result['success']:
                return success_response(result, "文件上传成功")
            else:
                return error_response(result['message'], 400)

        except Exception as e:
            logger.error(f"文件上传API错误: {e}")
            return error_response("文件上传时发生错误", 500)

    @app.route(f'{api_prefix}/files/<file_type>/<filename>', methods=['DELETE'])
    def delete_file(file_type, filename):
        """删除文件"""
        try:
            result = app.file_manager.delete_file(file_type, filename)

            if result['success']:
                return success_response(result, "文件删除成功")
            else:
                return error_response(result['message'], 400)

        except Exception as e:
            logger.error(f"文件删除API错误: {e}")
            return error_response("文件删除时发生错误", 500)

    @app.route(f'{api_prefix}/files/<file_type>/<filename>/info', methods=['GET'])
    def get_file_info(file_type, filename):
        """获取文件详细信息"""
        try:
            result = app.file_manager.get_file_info(file_type, filename)

            if result['success']:
                return success_response(result, "获取文件信息成功")
            else:
                return error_response(result['message'], 400)

        except Exception as e:
            logger.error(f"获取文件信息API错误: {e}")
            return error_response("获取文件信息时发生错误", 500)

    @app.route(f'{api_prefix}/files/<file_type>/<filename>/validate', methods=['POST'])
    def validate_file(file_type, filename):
        """验证文件完整性"""
        try:
            data = request.get_json() or {}
            expected_md5 = data.get('md5')
            expected_sha256 = data.get('sha256')

            result = app.file_manager.validate_file(
                file_type, filename, expected_md5, expected_sha256
            )

            if result['success']:
                return success_response(result, "文件验证完成")
            else:
                return error_response(result['message'], 400)

        except Exception as e:
            logger.error(f"文件验证API错误: {e}")
            return error_response("文件验证时发生错误", 500)

    @app.route(f'{api_prefix}/files/cleanup', methods=['POST'])
    def cleanup_temp_files():
        """清理临时文件"""
        try:
            result = app.file_manager.cleanup_temp_files()

            if result['success']:
                return success_response(result, "临时文件清理成功")
            else:
                return error_response(result['message'], 400)

        except Exception as e:
            logger.error(f"清理临时文件API错误: {e}")
            return error_response("清理临时文件时发生错误", 500)


# SocketIO事件处理已移至WebSocket处理器


# 创建应用实例
app, socketio = create_app()


@click.command()
@click.option('--host', default='127.0.0.1', help='Host to bind to')
@click.option('--port', default=5000, help='Port to bind to')
@click.option('--debug', is_flag=True, help='Enable debug mode')
@click.option('--config', default='development', help='Configuration name')
def run_server(host, port, debug, config):
    """启动开发服务器"""
    
    # 重新创建应用以应用新配置
    global app, socketio
    app, socketio = create_app(config)
    
    if debug:
        app.config['DEBUG'] = True
    
    print(f"🚀 Starting OpenWrt Compiler Backend...")
    print(f"🌐 Server: http://{host}:{port}")
    print(f"⚙️  Config: {config}")
    print(f"🔧 Debug: {debug}")
    print(f"📁 Workspace: {app.config['WORKSPACE_DIR']}")
    print(f"📝 Press Ctrl+C to stop")
    
    try:
        socketio.run(
            app,
            host=host,
            port=port,
            debug=debug,
            use_reloader=debug
        )
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")


if __name__ == '__main__':
    run_server()
