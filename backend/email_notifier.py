"""
邮箱通知系统
编译完成后自动发送邮件通知，包含下载链接
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
import os

from utils.logger import setup_logger


class EmailNotifier:
    """邮箱通知器"""
    
    def __init__(self, config, logger=None):
        self.config = config
        self.logger = logger or setup_logger(__name__)
        
        # 邮箱配置
        self.smtp_server = config.MAIL_SERVER
        self.smtp_port = config.MAIL_PORT
        self.use_tls = config.MAIL_USE_TLS
        self.username = config.MAIL_USERNAME
        self.password = config.MAIL_PASSWORD
        self.default_sender = config.MAIL_DEFAULT_SENDER or config.MAIL_USERNAME
        self.download_base_url = config.DOWNLOAD_BASE_URL
        
        # 检查配置
        self.enabled = config.ENABLE_MAIL_NOTIFICATIONS
        if not self.enabled:
            self.logger.warning("邮箱通知功能未启用，请检查邮箱配置")
    
    def send_compile_notification(self, user_email: str, username: str, 
                                compile_result: Dict[str, Any]) -> bool:
        """发送编译完成通知"""
        if not self.enabled or not user_email:
            return False
        
        try:
            # 准备邮件内容
            subject = self._generate_subject(compile_result)
            html_content = self._generate_html_content(username, compile_result)
            text_content = self._generate_text_content(username, compile_result)
            
            # 创建邮件
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.default_sender
            message["To"] = user_email
            
            # 添加文本和HTML内容
            text_part = MIMEText(text_content, "plain", "utf-8")
            html_part = MIMEText(html_content, "html", "utf-8")
            
            message.attach(text_part)
            message.attach(html_part)
            
            # 发送邮件
            self._send_email(message, user_email)
            
            self.logger.info(f"编译通知邮件已发送给用户: {username} ({user_email})")
            return True
            
        except Exception as e:
            self.logger.error(f"发送编译通知邮件失败: {e}")
            return False
    
    def _generate_subject(self, compile_result: Dict[str, Any]) -> str:
        """生成邮件主题"""
        success = compile_result.get("success", False)
        device_name = compile_result.get("device_name", "未知设备")
        
        if success:
            return f"✅ OpenWrt编译成功 - {device_name}"
        else:
            return f"❌ OpenWrt编译失败 - {device_name}"
    
    def _generate_html_content(self, username: str, compile_result: Dict[str, Any]) -> str:
        """生成HTML邮件内容"""
        success = compile_result.get("success", False)
        device_name = compile_result.get("device_name", "未知设备")
        compile_time = compile_result.get("compile_time", "未知")
        start_time = compile_result.get("start_time", "")
        end_time = compile_result.get("end_time", "")
        firmware_files = compile_result.get("firmware_files", [])
        error_message = compile_result.get("error_message", "")
        
        # 状态图标和颜色
        status_icon = "✅" if success else "❌"
        status_color = "#28a745" if success else "#dc3545"
        status_text = "编译成功" if success else "编译失败"
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>OpenWrt编译通知</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                          color: white; padding: 20px; border-radius: 8px 8px 0 0; text-align: center; }}
                .content {{ background: #f8f9fa; padding: 20px; border-radius: 0 0 8px 8px; }}
                .status {{ font-size: 24px; font-weight: bold; color: {status_color}; text-align: center; margin: 20px 0; }}
                .info-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                .info-table th, .info-table td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
                .info-table th {{ background-color: #e9ecef; font-weight: bold; }}
                .download-section {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; }}
                .download-btn {{ display: inline-block; background: #007bff; color: white; 
                               padding: 12px 24px; text-decoration: none; border-radius: 4px; 
                               font-weight: bold; margin: 5px; }}
                .download-btn:hover {{ background: #0056b3; }}
                .error-section {{ background: #f8d7da; border: 1px solid #f5c6cb; 
                                 color: #721c24; padding: 15px; border-radius: 4px; margin: 20px 0; }}
                .footer {{ text-align: center; color: #666; font-size: 12px; margin-top: 30px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔧 OpenWrt 编译器</h1>
                    <p>Debian版 - 编译通知</p>
                </div>
                
                <div class="content">
                    <div class="status">
                        {status_icon} {status_text}
                    </div>
                    
                    <p>亲爱的 <strong>{username}</strong>，</p>
                    <p>您的OpenWrt固件编译任务已完成。以下是详细信息：</p>
                    
                    <table class="info-table">
                        <tr><th>设备型号</th><td>{device_name}</td></tr>
                        <tr><th>编译状态</th><td style="color: {status_color}; font-weight: bold;">{status_text}</td></tr>
                        <tr><th>开始时间</th><td>{start_time}</td></tr>
                        <tr><th>结束时间</th><td>{end_time}</td></tr>
                        <tr><th>编译耗时</th><td>{compile_time}</td></tr>
                    </table>
        """
        
        if success and firmware_files:
            html += """
                    <div class="download-section">
                        <h3>📦 固件下载</h3>
                        <p>编译成功！您可以点击下面的链接下载固件文件：</p>
            """
            
            for file_info in firmware_files:
                file_name = file_info.get("name", "")
                file_size = file_info.get("size", "")
                download_url = f"{self.download_base_url}/api/download/firmware/{file_info.get('id', '')}"
                
                html += f"""
                        <div style="margin: 10px 0;">
                            <a href="{download_url}" class="download-btn">
                                📥 下载 {file_name}
                            </a>
                            <span style="color: #666; font-size: 14px;">({file_size})</span>
                        </div>
                """
            
            html += """
                        <p style="color: #666; font-size: 14px; margin-top: 20px;">
                            💡 提示：固件文件将保留7天，请及时下载。
                        </p>
                    </div>
            """
        
        elif not success and error_message:
            html += f"""
                    <div class="error-section">
                        <h4>❌ 错误信息</h4>
                        <p>{error_message}</p>
                        <p>请检查配置后重新编译，或联系管理员获取帮助。</p>
                    </div>
            """
        
        html += f"""
                    <div class="footer">
                        <p>此邮件由 OpenWrt编译器 自动发送</p>
                        <p>访问编译器: <a href="{self.download_base_url}">{self.download_base_url}</a></p>
                        <p>发送时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _generate_text_content(self, username: str, compile_result: Dict[str, Any]) -> str:
        """生成纯文本邮件内容"""
        success = compile_result.get("success", False)
        device_name = compile_result.get("device_name", "未知设备")
        compile_time = compile_result.get("compile_time", "未知")
        start_time = compile_result.get("start_time", "")
        end_time = compile_result.get("end_time", "")
        firmware_files = compile_result.get("firmware_files", [])
        error_message = compile_result.get("error_message", "")
        
        status_text = "编译成功" if success else "编译失败"
        
        text = f"""
OpenWrt 编译器 - 编译通知

亲爱的 {username}，

您的OpenWrt固件编译任务已完成。

编译信息：
- 设备型号: {device_name}
- 编译状态: {status_text}
- 开始时间: {start_time}
- 结束时间: {end_time}
- 编译耗时: {compile_time}
        """
        
        if success and firmware_files:
            text += "\n固件下载链接：\n"
            for file_info in firmware_files:
                file_name = file_info.get("name", "")
                download_url = f"{self.download_base_url}/api/download/firmware/{file_info.get('id', '')}"
                text += f"- {file_name}: {download_url}\n"
            
            text += "\n提示：固件文件将保留7天，请及时下载。"
        
        elif not success and error_message:
            text += f"\n错误信息：\n{error_message}\n"
            text += "请检查配置后重新编译，或联系管理员获取帮助。"
        
        text += f"""

访问编译器: {self.download_base_url}
发送时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

此邮件由 OpenWrt编译器 自动发送
        """
        
        return text.strip()
    
    def _send_email(self, message: MIMEMultipart, recipient: str):
        """发送邮件"""
        context = ssl.create_default_context()
        
        with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
            if self.use_tls:
                server.starttls(context=context)
            
            server.login(self.username, self.password)
            server.sendmail(self.default_sender, recipient, message.as_string())
    
    def test_email_config(self, test_email: str) -> bool:
        """测试邮箱配置"""
        if not self.enabled:
            return False
        
        try:
            test_result = {
                "success": True,
                "device_name": "测试设备",
                "compile_time": "5分钟",
                "start_time": "2024-01-01 10:00:00",
                "end_time": "2024-01-01 10:05:00",
                "firmware_files": [
                    {"name": "test-firmware.bin", "size": "8.5MB", "id": "test123"}
                ]
            }
            
            return self.send_compile_notification(test_email, "测试用户", test_result)
            
        except Exception as e:
            self.logger.error(f"邮箱配置测试失败: {e}")
            return False
