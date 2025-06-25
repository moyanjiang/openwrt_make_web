# OpenWrt 编译器 API 文档

## 概述

OpenWrt编译器提供了完整的RESTful API接口，支持源码管理、配置管理、编译控制、文件管理等功能。所有API都返回JSON格式的响应。

## 基础信息

- **Base URL**: `http://localhost:5000/api`
- **API版本**: v1
- **认证方式**: 暂无（开发阶段）
- **内容类型**: `application/json`
- **响应格式**: 统一JSON格式
- **时间戳**: ISO 8601格式

## 通用响应格式

### 成功响应
```json
{
  "success": true,
  "data": {},
  "message": "操作成功"
}
```

### 错误响应
```json
{
  "success": false,
  "error": "错误信息",
  "code": "ERROR_CODE"
}
```

## API 接口列表

### 1. 系统状态

#### 获取系统状态
```http
GET /api/status
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "server": "running",
    "version": "1.0.0",
    "config": "development",
    "workspace": "./workspace",
    "lede_installed": false
  },
  "message": "System status retrieved successfully",
  "timestamp": "2025-06-25T10:30:00.000Z"
}
```

#### 健康检查
```http
GET /api/health
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "status": "healthy"
  },
  "message": "Service is healthy",
  "timestamp": "2025-06-25T10:30:00.000Z"
}
```

### 2. 编译器管理

#### 克隆源码
```http
POST /api/compiler/clone
```

**请求体**:
```json
{
  "force_update": false
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "status": "cloning",
    "message": "开始克隆LEDE源码..."
  },
  "message": "源码克隆操作完成",
  "timestamp": "2025-06-25T10:30:00.000Z"
}
```

#### 获取仓库状态
```http
GET /api/compiler/repository
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "cloned": true,
    "path": "./workspace/lede",
    "branch": "master",
    "last_update": "2025-06-25T10:30:00Z",
    "feeds_updated": true
  },
  "message": "获取仓库状态成功",
  "timestamp": "2025-06-25T10:30:00.000Z"
}
```

#### 更新Feeds
```http
POST /api/compiler/feeds/update
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "status": "updating",
    "message": "正在更新feeds..."
  },
  "message": "feeds更新完成",
  "timestamp": "2025-06-25T10:30:00.000Z"
}
```

#### 安装Feeds
```http
POST /api/compiler/feeds/install
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "status": "installing",
    "message": "正在安装feeds..."
  },
  "message": "feeds安装完成",
  "timestamp": "2025-06-25T10:30:00.000Z"
}
```

### 3. 配置管理

#### 获取配置模板列表
```http
GET /api/config/templates
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "templates": {
      "x86_64": {
        "name": "x86_64通用配置",
        "description": "适用于x86_64架构的通用配置",
        "target": "x86/64",
        "file": "x86_64.json"
      },
      "raspberry_pi": {
        "name": "树莓派4B配置",
        "description": "适用于树莓派4B的配置",
        "target": "bcm27xx/bcm2711",
        "file": "raspberry_pi.json"
      },
      "router_generic": {
        "name": "通用路由器配置",
        "description": "适用于通用路由器的基础配置",
        "target": "generic",
        "file": "router_generic.json"
      }
    }
  },
  "message": "获取配置模板成功",
  "timestamp": "2025-06-25T10:30:00.000Z"
}
```

#### 应用配置模板
```http
POST /api/config/apply-template
```

**请求体**:
```json
{
  "template_id": "x86_64",
  "config_name": "my_x86_config"
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "config_name": "my_x86_config",
    "applied": true
  },
  "message": "配置模板应用成功"
}
```

#### 获取配置列表
```http
GET /api/configs
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "configs": [
      {
        "name": "my_x86_config",
        "created_at": "2025-06-25T10:30:00Z",
        "size": 1024,
        "target": "x86/64"
      }
    ]
  }
}
```

#### 获取配置详情
```http
GET /api/config/{config_name}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "name": "my_x86_config",
    "content": "CONFIG_TARGET_x86=y\nCONFIG_TARGET_x86_64=y\n...",
    "metadata": {
      "target": "x86/64",
      "created_at": "2025-06-25T10:30:00Z",
      "size": 1024
    }
  }
}
```

#### 更新配置
```http
PUT /api/config/{config_name}
```

**请求体**:
```json
{
  "config_data": "CONFIG_TARGET_x86=y\nCONFIG_TARGET_x86_64=y\n...",
  "metadata": {
    "target": "x86/64",
    "description": "更新的配置"
  }
}
```

#### 删除配置
```http
DELETE /api/config/{config_name}
```

### 4. 编译管理

#### 开始编译
```http
POST /api/compile/start
```

**请求体**:
```json
{
  "config_name": "my_x86_config",
  "target": "all",
  "threads": "auto",
  "verbose": true,
  "clean": false
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "task_id": "compile_123456",
    "status": "started",
    "config": "my_x86_config"
  },
  "message": "编译已开始"
}
```

#### 停止编译
```http
POST /api/compile/stop
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "stopped": true
  },
  "message": "编译已停止"
}
```

#### 获取编译状态
```http
GET /api/compile/status
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "status": "compiling",
    "progress": 45.5,
    "start_time": "2025-06-25T10:30:00Z",
    "elapsed_time": 1800,
    "current_step": "Building kernel modules",
    "task_id": "compile_123456"
  }
}
```

#### 获取编译日志
```http
GET /api/compile/logs
```

**查询参数**:
- `lines`: 返回的日志行数（默认100）
- `follow`: 是否持续获取新日志（默认false）

**响应示例**:
```json
{
  "success": true,
  "data": {
    "logs": [
      {
        "timestamp": "2025-06-25T10:30:00Z",
        "level": "info",
        "message": "Starting compilation..."
      }
    ],
    "total_lines": 1500
  }
}
```

### 5. 文件管理

#### 获取固件文件列表
```http
GET /api/files/firmware
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "files": [
      {
        "name": "openwrt-x86-64-generic-squashfs-combined.img",
        "size": 104857600,
        "size_human": "100.0 MB",
        "created_time": 1719302400,
        "modified_time": 1719302400,
        "md5": "d41d8cd98f00b204e9800998ecf8427e",
        "download_url": "/api/files/firmware/openwrt-x86-64-generic-squashfs-combined.img"
      }
    ],
    "total": 1
  }
}
```

#### 获取配置文件列表
```http
GET /api/files/configs
```

#### 获取存储信息
```http
GET /api/files/storage
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "storage": {
      "available_space": 107374182400,
      "available_space_human": "100.0 GB",
      "used_space": 10737418240,
      "used_space_human": "10.0 GB",
      "firmware_size": 5368709120,
      "firmware_size_human": "5.0 GB",
      "configs_size": 1048576,
      "configs_size_human": "1.0 MB"
    }
  }
}
```

#### 下载文件
```http
GET /api/files/{type}/{filename}
```

**路径参数**:
- `type`: 文件类型（firmware/config）
- `filename`: 文件名

**响应**: 文件二进制数据

#### 上传配置文件
```http
POST /api/files/configs/{filename}
```

**请求体**: multipart/form-data
- `file`: 文件数据
- `overwrite`: 是否覆盖（可选，默认false）

#### 删除文件
```http
DELETE /api/files/{type}/{filename}
```

#### 获取文件信息
```http
GET /api/files/{type}/{filename}/info
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "file_info": {
      "name": "openwrt-x86-64-generic-squashfs-combined.img",
      "size": 104857600,
      "size_human": "100.0 MB",
      "created_time": 1719302400,
      "modified_time": 1719302400,
      "md5": "d41d8cd98f00b204e9800998ecf8427e",
      "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "mime_type": "application/octet-stream"
    }
  }
}
```

#### 验证文件完整性
```http
POST /api/files/{type}/{filename}/validate
```

**请求体**:
```json
{
  "md5": "d41d8cd98f00b204e9800998ecf8427e",
  "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
}
```

#### 清理临时文件
```http
POST /api/files/cleanup
```

### 6. WebSocket管理

#### 获取WebSocket统计
```http
GET /api/websocket/stats
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "websocket_stats": {
      "connected_clients": 3,
      "total_connections": 15,
      "total_messages_sent": 1500,
      "total_errors": 2
    },
    "message_queue_stats": {
      "pending_messages": 0,
      "processed_messages": 1500,
      "failed_messages": 2
    }
  }
}
```

#### 获取连接的客户端
```http
GET /api/websocket/clients
```

#### 获取WebSocket房间信息
```http
GET /api/websocket/rooms
```

## WebSocket 事件

### 客户端事件

#### 连接事件
```javascript
socket.on('connect', () => {
  console.log('Connected to server');
});
```

#### 订阅事件
```javascript
socket.emit('subscribe', {
  events: ['compile_log', 'compile_progress', 'compile_complete']
});
```

#### 加入房间
```javascript
socket.emit('join_room', {
  room: 'compile_room'
});
```

#### 心跳检测
```javascript
socket.emit('ping');
socket.on('pong', (data) => {
  console.log('Pong received:', data);
});
```

### 服务器事件

#### 编译日志
```javascript
socket.on('compile_log', (data) => {
  console.log('Compile log:', data.line);
});
```

#### 编译进度
```javascript
socket.on('compile_progress', (data) => {
  console.log('Progress:', data.progress + '%');
});
```

#### 编译完成
```javascript
socket.on('compile_complete', (data) => {
  console.log('Compilation completed:', data.files);
});
```

#### 编译错误
```javascript
socket.on('compile_error', (data) => {
  console.error('Compilation error:', data.error);
});
```

## 错误代码

| 代码 | 说明 |
|------|------|
| `INVALID_REQUEST` | 请求参数无效 |
| `RESOURCE_NOT_FOUND` | 资源不存在 |
| `OPERATION_FAILED` | 操作失败 |
| `COMPILATION_ERROR` | 编译错误 |
| `GIT_ERROR` | Git操作错误 |
| `FILE_ERROR` | 文件操作错误 |
| `CONFIG_ERROR` | 配置错误 |
| `SYSTEM_ERROR` | 系统错误 |

## 限制说明

- **请求频率**: 每分钟最多100个请求
- **文件大小**: 上传文件最大100MB
- **并发编译**: 同时只能进行一个编译任务
- **WebSocket连接**: 每个IP最多10个并发连接

## 示例代码

### Python示例
```python
import requests

# 获取系统状态
response = requests.get('http://localhost:5000/api/status')
data = response.json()
print(data)

# 开始编译
compile_data = {
    'config_name': 'my_config',
    'target': 'all',
    'threads': 'auto'
}
response = requests.post('http://localhost:5000/api/compile/start', json=compile_data)
print(response.json())
```

### JavaScript示例
```javascript
// 使用fetch API
async function getStatus() {
  const response = await fetch('/api/status');
  const data = await response.json();
  console.log(data);
}

// 使用Socket.IO
const socket = io();
socket.on('compile_log', (data) => {
  console.log(data.line);
});
```
