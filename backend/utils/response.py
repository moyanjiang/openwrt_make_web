"""
API响应工具
"""

from flask import jsonify
from typing import Any, Dict, Optional


class APIResponse:
    """API响应类"""
    
    @staticmethod
    def success(data: Any = None, message: str = "Success", code: int = 200) -> Dict:
        """成功响应"""
        response = {
            "success": True,
            "code": code,
            "message": message,
            "timestamp": None  # 将在Flask应用中添加时间戳
        }
        
        if data is not None:
            response["data"] = data
            
        return response
    
    @staticmethod
    def error(message: str = "Error", code: int = 400, error_code: Optional[str] = None) -> Dict:
        """错误响应"""
        response = {
            "success": False,
            "code": code,
            "message": message,
            "timestamp": None  # 将在Flask应用中添加时间戳
        }
        
        if error_code:
            response["error_code"] = error_code
            
        return response


def success_response(data: Any = None, message: str = "Success", code: int = 200):
    """返回成功的JSON响应"""
    return jsonify(APIResponse.success(data, message, code)), code


def error_response(message: str = "Error", code: int = 400, error_code: Optional[str] = None):
    """返回错误的JSON响应"""
    return jsonify(APIResponse.error(message, code, error_code)), code
