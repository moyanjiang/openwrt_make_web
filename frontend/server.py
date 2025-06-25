#!/usr/bin/env python3
"""
前端静态文件服务器
在端口9963上提供前端静态文件服务
"""

import os
import sys
import http.server
import socketserver
from pathlib import Path
import argparse
import webbrowser
import threading
import time

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """自定义HTTP请求处理器"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(Path(__file__).parent), **kwargs)
    
    def end_headers(self):
        """添加CORS头"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        super().end_headers()
    
    def do_OPTIONS(self):
        """处理OPTIONS请求"""
        self.send_response(200)
        self.end_headers()
    
    def log_message(self, format, *args):
        """自定义日志格式"""
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {format % args}")

def start_frontend_server(port=9963, host='0.0.0.0', open_browser=False):
    """启动前端服务器"""
    try:
        # 确保在正确的目录
        frontend_dir = Path(__file__).parent
        os.chdir(frontend_dir)
        
        # 创建服务器
        with socketserver.TCPServer((host, port), CustomHTTPRequestHandler) as httpd:
            print(f"🌐 前端服务器启动成功")
            print(f"📍 服务地址: http://{host}:{port}")
            print(f"📁 服务目录: {frontend_dir}")
            print(f"🔗 访问地址: http://localhost:{port}")
            print("按 Ctrl+C 停止服务器")
            
            # 自动打开浏览器
            if open_browser:
                def open_browser_delayed():
                    time.sleep(1)
                    webbrowser.open(f'http://localhost:{port}')
                
                threading.Thread(target=open_browser_delayed, daemon=True).start()
            
            # 启动服务器
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\n🛑 服务器已停止")
    except OSError as e:
        if e.errno == 98:  # Address already in use
            print(f"❌ 端口 {port} 已被占用，请使用其他端口")
            print(f"💡 尝试: python3 server.py --port {port + 1}")
        else:
            print(f"❌ 启动服务器失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 服务器错误: {e}")
        sys.exit(1)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='OpenWrt编译器前端服务器')
    parser.add_argument('--port', '-p', type=int, default=9963,
                       help='服务器端口 (默认: 9963)')
    parser.add_argument('--host', '-H', default='0.0.0.0',
                       help='服务器主机 (默认: 0.0.0.0)')
    parser.add_argument('--open', '-o', action='store_true',
                       help='自动打开浏览器')
    parser.add_argument('--dev', action='store_true',
                       help='开发模式 (自动打开浏览器)')
    
    args = parser.parse_args()
    
    # 开发模式自动打开浏览器
    if args.dev:
        args.open = True
    
    print("🚀 OpenWrt编译器前端服务器")
    print("=" * 40)
    
    start_frontend_server(
        port=args.port,
        host=args.host,
        open_browser=args.open
    )

if __name__ == '__main__':
    main()
