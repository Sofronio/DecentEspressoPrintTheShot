#!/usr/bin/env python3
"""
PrintTheShot Server - 支持JSON格式上传、自动打印和Web管理
接收DECENT咖啡机上传的冲泡数据，支持打印控制和数据展示
"""

import http.server
import socketserver
import json
import time
import os
import threading
import tempfile
import subprocess
import signal
import sys
import urllib.parse
from datetime import datetime
from io import BytesIO

# 第三方库导入
try:
    import matplotlib
    matplotlib.use('Agg')  # 使用非交互式后端
    import matplotlib.pyplot as plt
    import numpy as np
    from PIL import Image
except ImportError as e:
    print(f"❌ 缺少必要的库: {e}")
    print("💡 请安装: pip install matplotlib pillow numpy")
    sys.exit(1)

# 全局配置
DATA_DIR = "shots_data"
IMAGE_DIR = "shots_images"
PRINT_ENABLED = True  # 默认启用打印
MAX_USERS = 5  # 最大并发用户数
received_shots = []
server_start_time = datetime.now()

def parse_multipart_form_data(post_data, content_type):
    """解析 multipart/form-data 数据，替代弃用的 cgi 模块"""
    try:
        # 提取 boundary
        if 'boundary=' not in content_type:
            raise ValueError("No boundary found in content-type")
        
        boundary = content_type.split('boundary=')[1].encode()
        boundary_line = b'--' + boundary
        
        # 分割数据
        parts = post_data.split(boundary_line)
        
        for part in parts:
            if b'name="file"' in part and (b'.json' in part or b'application/json' in part):
                # 找到文件数据部分
                header_end = part.find(b'\r\n\r\n')
                if header_end != -1:
                    file_data = part[header_end+4:]
                    # 移除结尾的 boundary 和换行符
                    file_data = file_data.split(b'\r\n--')[0]
                    return file_data
        
        raise ValueError("No file data found in multipart form")
        
    except Exception as e:
        raise ValueError(f"Error parsing multipart data: {str(e)}")

class PrintTheShotHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.semaphore = threading.Semaphore(MAX_USERS)
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """处理 GET 请求 - 显示服务状态和管理界面"""
        with self.semaphore:
            if self.path == '/':
                self.show_management_interface()
            elif self.path == '/api/status':
                self.send_api_status()
            elif self.path == '/api/queue':
                self.send_queue_status()
            elif self.path.startswith('/images/'):
                self.serve_image()
            elif self.path == '/api/shots':
                self.send_shots_list()
            elif self.path == '/plugin/plugin.tcl':  # 新增插件文件服务
                self.serve_plugin_file()
            else:
                super().do_GET()

    def do_POST(self):
        """处理 POST 请求 - 接收上传的冲泡数据"""
        with self.semaphore:
            if self.path == '/upload' or self.path.startswith('/upload'):
                try:
                    content_type = self.headers.get('Content-Type', '')
                    content_length = int(self.headers.get('Content-Length', 0))
                    post_data = self.rfile.read(content_length)
                    
                    if 'application/json' in content_type:
                        self.handle_json_upload(post_data)
                    elif 'multipart/form-data' in content_type:
                        self.handle_multipart_upload(post_data, content_type)
                    else:
                        self.send_error(400, "Unsupported content type")
                        
                except Exception as e:
                    print(f"❌ 处理上传时出错: {e}")
                    self.send_error(500, f"Server error: {str(e)}")
                    
            elif self.path == '/api/print':
                self.handle_print_control()
            else:
                self.send_error(404, "Endpoint not found")

    def do_DELETE(self):
        """处理DELETE请求 - 清空打印队列"""
        with self.semaphore:
            if self.path == '/api/queue':
                self.handle_clear_queue()
            else:
                self.send_error(404, "Endpoint not found")

    def serve_plugin_file(self):
        """提供插件文件下载"""
        try:
            plugin_path = "./plugin/plugin.tcl"
            if os.path.exists(plugin_path):
                self.send_response(200)
                self.send_header('Content-type', 'application/x-tcl')
                self.send_header('Content-Disposition', 'attachment; filename="plugin.tcl"')
                self.end_headers()
                
                with open(plugin_path, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                self.send_error(404, "Plugin file not found")
        except Exception as e:
            self.send_error(500, f"Error serving plugin file: {str(e)}")

    def show_management_interface(self):
        """显示管理界面"""
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        status_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>PrintTheShot Server</title>
            <meta charset="utf-8">
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
                .container { max-width: 1200px; margin: 0 auto; }
                .header { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                .card { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                .status-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }
                .status-item { background: #f8f9fa; padding: 15px; border-radius: 5px; text-align: center; }
                .shot-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; }
                .shot-card { border: 1px solid #ddd; border-radius: 8px; padding: 15px; background: white; }
                .shot-image { max-width: 100%; height: 200px; object-fit: cover; border-radius: 4px; cursor: pointer; transition: opacity 0.3s ease; }
                .shot-image:hover { opacity: 0.8; }
                .controls { display: flex; gap: 10px; margin: 10px 0; flex-wrap: wrap; }
                .btn { padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; }
                .btn-primary { background: #007bff; color: white; }
                .btn-success { background: #28a745; color: white; }
                .btn-warning { background: #ffc107; color: black; }
                .btn-danger { background: #dc3545; color: white; }
                .btn-info { background: #17a2b8; color: white; }
                .form-group { margin: 10px 0; }
                label { display: block; margin-bottom: 5px; font-weight: bold; }
                select, input { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
                .upload-area { border: 2px dashed #007bff; padding: 40px; text-align: center; border-radius: 8px; margin: 20px 0; }
                .success { color: #28a745; }
                .error { color: #dc3545; }
                .warning { color: #ffc107; }
                .info { color: #17a2b8; }
                .queue-info { background: #e8f4fd; padding: 15px; border-radius: 5px; margin: 10px 0; }
                .queue-item { background: #f8f9fa; padding: 8px 12px; margin: 5px 0; border-radius: 4px; border-left: 4px solid #007bff; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🍳 PrintTheShot Server</h1>
                    <p>接收DECENT咖啡机数据，支持自动打印和数据分析</p>
                </div>
                
                <div class="card">
                    <h2>📊 服务器状态</h2>
                    <div class="status-grid" id="statusGrid">
                        <!-- 动态状态信息 -->
                    </div>
                </div>
                
                <div class="card">
                    <h2>🖨️ 打印控制</h2>
                    <div class="queue-info">
                        <h3>打印队列状态</h3>
                        <div id="queueStatus">
                            <p>加载中...</p>
                        </div>
                        <div class="controls">
                            <button class="btn btn-info" onclick="refreshQueue()">刷新队列</button>
                            <button class="btn btn-warning" onclick="clearQueue()">清空打印队列</button>
                            <button class="btn btn-primary" onclick="togglePrinting()" id="printToggle">启用打印</button>
                            <a href="./plugin/plugin.tcl" download class="btn btn-success">📥 下载DE1插件</a>
                        </div>
                        <!-- 插件说明 -->
                        <div style="margin-top: 15px; padding: 10px; background: #f0f8ff; border-radius: 5px; border-left: 4px solid #007bff;">
                            <h4>🔌 DE1 插件安装说明</h4>
                            <p><strong>安装步骤：</strong></p>
                            <ol style="margin: 5px 0; padding-left: 20px;">
                                <li>点击"下载DE1插件"按钮获取 plugin.tcl 文件</li>
                                <li>在平板的SD卡中找到目录：<code>/de1plus/plugins/print_the_shot/</code></li>
                                <li>将下载的 plugin.tcl 文件放入该目录</li>
                                <li>重启De1App，插件将自动加载</li>
                            </ol>
                            <p><small>💡 插件功能：自动将冲泡数据上传到PrintTheShot服务器进行打印</small></p>
                        </div>
                    </div>
                    <div class="form-group">
                        <label>选择打印机:</label>
                        <select id="printerSelect">
                            <option value="">默认打印机</option>
                        </select>
                    </div>
                </div>
                
                <div class="card">
                    <h2>📤 数据上传</h2>
                    <div class="upload-area">
                        <p>拖放JSON文件到这里或点击选择文件</p>
                        <input type="file" id="fileInput" accept=".json" style="display: none;">
                        <button class="btn btn-primary" onclick="document.getElementById('fileInput').click()">选择文件</button>
                        <div id="uploadStatus" style="margin-top: 10px;"></div>
                    </div>
                    <p>或者使用API端点: <code>POST /upload</code> (Content-Type: application/json)</p>
                </div>
                
                <div class="card">
                    <h2>📈 最近接收的数据</h2>
                    <div class="shot-grid" id="shotsGrid">
                        <!-- 动态数据卡片 -->
                    </div>
                </div>
            </div>
            
            <script>
                let printEnabled = true;
                
                // 加载初始数据
                document.addEventListener('DOMContentLoaded', function() {
                    loadStatus();
                    loadShots();
                    loadPrinters();
                    loadQueueStatus();
                    
                    // 设置文件上传
                    document.getElementById('fileInput').addEventListener('change', handleFileUpload);
                    
                    // 定期刷新数据
                    setInterval(loadStatus, 5000);
                    setInterval(loadShots, 10000);
                    setInterval(loadQueueStatus, 8000);
                });
                
                async function loadStatus() {
                    try {
                        const response = await fetch('/api/status');
                        const data = await response.json();
                        
                        document.getElementById('statusGrid').innerHTML = `
                            <div class="status-item">
                                <h3>🟢 状态</h3>
                                <p>运行中</p>
                            </div>
                            <div class="status-item">
                                <h3>⏰ 启动时间</h3>
                                <p>${data.start_time}</p>
                            </div>
                            <div class="status-item">
                                <h3>📊 接收数据</h3>
                                <p>${data.shot_count} 条记录</p>
                            </div>
                            <div class="status-item">
                                <h3>👥 并发用户</h3>
                                <p>${data.active_users}/${data.max_users}</p>
                            </div>
                            <div class="status-item">
                                <h3>🖨️ 打印状态</h3>
                                <p id="printStatus">${data.print_enabled ? '已启用' : '已禁用'}</p>
                            </div>
                            <div class="status-item">
                                <h3>📋 打印队列</h3>
                                <p>${data.print_queue_count} 个任务</p>
                            </div>
                        `;
                        
                        printEnabled = data.print_enabled;
                        updatePrintToggle();
                        
                    } catch (error) {
                        console.error('Error loading status:', error);
                    }
                }
                
                async function loadQueueStatus() {
                    try {
                        const response = await fetch('/api/queue');
                        const data = await response.json();
                        
                        let queueHTML = '';
                        if (data.queue_count === 0) {
                            queueHTML = '<p class="success">✅ 打印队列为空</p>';
                        } else {
                            queueHTML = `
                                <p><strong>队列中有 ${data.queue_count} 个打印任务:</strong></p>
                                <div id="queueItems">
                                    ${data.queue_items ? data.queue_items.map(item => `
                                        <div class="queue-item">
                                            <strong>${item.filename}</strong><br>
                                            <small>状态: ${item.status} | 添加时间: ${item.added_time}</small>
                                        </div>
                                    `).join('') : ''}
                                </div>
                            `;
                        }
                        
                        document.getElementById('queueStatus').innerHTML = queueHTML;
                        
                    } catch (error) {
                        console.error('Error loading queue status:', error);
                        document.getElementById('queueStatus').innerHTML = '<p class="error">❌ 无法获取队列状态</p>';
                    }
                }
                
                async function clearQueue() {
                    if (!confirm('确定要清空打印队列吗？这将取消所有待处理的打印任务。')) {
                        return;
                    }
                    
                    try {
                        const response = await fetch('/api/queue', {
                            method: 'DELETE'
                        });
                        
                        const result = await response.json();
                        if (result.success) {
                            alert('✅ 打印队列已清空');
                            loadQueueStatus();
                            loadStatus();
                        } else {
                            alert('❌ 清空队列失败: ' + result.message);
                        }
                    } catch (error) {
                        alert('❌ 清空队列错误: ' + error);
                    }
                }
                
                async function refreshQueue() {
                    await loadQueueStatus();
                    alert('✅ 队列状态已刷新');
                }
                
                async function togglePrinting() {
                    try {
                        const response = await fetch('/api/print', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ enabled: !printEnabled })
                        });
                        
                        const result = await response.json();
                        if (result.success) {
                            printEnabled = !printEnabled;
                            updatePrintToggle();
                            loadStatus();
                            loadQueueStatus();
                        } else {
                            alert('❌ 切换打印状态失败: ' + result.message);
                        }
                    } catch (error) {
                        console.error('Error toggling print:', error);
                        alert('❌ 切换打印状态错误: ' + error);
                    }
                }
                
                function updatePrintToggle() {
                    const btn = document.getElementById('printToggle');
                    if (printEnabled) {
                        btn.textContent = '禁用打印';
                        btn.className = 'btn btn-danger';
                    } else {
                        btn.textContent = '启用打印';
                        btn.className = 'btn btn-success';
                    }
                }
                
                async function loadShots() {
                    try {
                        const response = await fetch('/api/shots');
                        const shots = await response.json();
                        
                        let shotsHTML = '';
                        shots.forEach(shot => {
                            const imageUrl = shot.image_exists ? `/images/${shot.filename.replace('.json', '.png')}` : '';
                            const printBtn = printEnabled ? 
                                `<button class="btn btn-success" onclick="printShot('${shot.filename}')">打印</button>` : 
                                `<button class="btn btn-warning" onclick="printShot('${shot.filename}')" disabled>打印已禁用</button>`;
                            
                            shotsHTML += `
                                <div class="shot-card">
                                    <h4>${shot.profile}</h4>
                                    <p><strong>时间:</strong> ${shot.timestamp}</p>
                                    <p><strong>文件:</strong> ${shot.filename}</p>
                                    ${imageUrl ? `<a href="${imageUrl}" target="_blank"><img src="${imageUrl}" alt="Chart" class="shot-image"></a>` : '<p>无图表</p>'}
                                    <div class="controls">
                                        ${printBtn}
                                        <button class="btn btn-primary" onclick="viewDetails('${shot.filename}')">详情</button>
                                    </div>
                                </div>
                            `;
                        });
                        
                        document.getElementById('shotsGrid').innerHTML = shotsHTML || '<p>暂无数据</p>';
                        
                    } catch (error) {
                        console.error('Error loading shots:', error);
                    }
                }
                
                async function loadPrinters() {
                    // 这里可以扩展为从系统获取打印机列表
                    // 目前使用默认打印机
                }
                
                async function handleFileUpload(event) {
                    const file = event.target.files[0];
                    if (!file) return;
                    
                    const statusDiv = document.getElementById('uploadStatus');
                    statusDiv.innerHTML = '<p class="warning">上传中...</p>';
                    
                    try {
                        const formData = new FormData();
                        formData.append('file', file);
                        
                        const response = await fetch('/upload', {
                            method: 'POST',
                            body: formData
                        });
                        
                        const result = await response.json();
                        if (response.ok) {
                            statusDiv.innerHTML = `<p class="success">✅ ${result.message}</p>`;
                            loadShots();
                        } else {
                            statusDiv.innerHTML = `<p class="error">❌ ${result.message || '上传失败'}</p>`;
                        }
                    } catch (error) {
                        statusDiv.innerHTML = `<p class="error">❌ 上传错误: ${error}</p>`;
                    }
                    
                    event.target.value = '';
                }
                
                async function printShot(filename) {
                    if (!printEnabled) {
                        alert('打印功能已禁用');
                        return;
                    }
                    
                    try {
                        const response = await fetch('/api/print', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ 
                                action: 'print_shot',
                                filename: filename 
                            })
                        });
                        
                        const result = await response.json();
                        if (result.success) {
                            alert('打印任务已发送');
                            loadQueueStatus();
                        } else {
                            alert('打印失败: ' + result.message);
                        }
                    } catch (error) {
                        alert('打印错误: ' + error);
                    }
                }
                
                function viewDetails(filename) {
                    alert('查看详情: ' + filename);
                    // 这里可以扩展为显示详细数据
                }
                
                function refreshPrinters() {
                    alert('刷新打印机列表功能待实现');
                }
            </script>
        </body>
        </html>
        """
        self.wfile.write(status_html.encode('utf-8'))

    def send_api_status(self):
        """发送API状态信息"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        queue_count = self.get_print_queue_count()
        
        status_data = {
            'status': 'running',
            'start_time': server_start_time.strftime('%Y-%m-%d %H:%M:%S'),
            'shot_count': len(received_shots),
            'active_users': MAX_USERS - self.semaphore._value,
            'max_users': MAX_USERS,
            'print_enabled': PRINT_ENABLED,
            'print_queue_count': queue_count,
            'data_dir': os.path.abspath(DATA_DIR),
            'image_dir': os.path.abspath(IMAGE_DIR)
        }
        
        self.wfile.write(json.dumps(status_data).encode('utf-8'))

    def send_queue_status(self):
        """发送打印队列状态"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        queue_info = self.get_print_queue_info()
        self.wfile.write(json.dumps(queue_info).encode('utf-8'))

    def send_shots_list(self):
        """发送shots列表"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        shots_data = []
        for shot in received_shots[-20:]:
            image_filename = shot['filename'].replace('.json', '.png')
            image_path = os.path.join(IMAGE_DIR, image_filename)
            
            shot_info = {
                'id': shot['id'],
                'filename': shot['filename'],
                'timestamp': shot['timestamp'],
                'profile': shot.get('profile', 'unknown'),
                'clock': shot.get('clock', 'unknown'),
                'data_size': shot.get('data_size', 0),
                'image_exists': os.path.exists(image_path)
            }
            shots_data.append(shot_info)
        
        self.wfile.write(json.dumps(shots_data[::-1]).encode('utf-8'))

    def serve_image(self):
        """提供图像文件服务"""
        try:
            filename = self.path.split('/')[-1]
            filepath = os.path.join(IMAGE_DIR, filename)
            
            if os.path.exists(filepath) and filename.endswith('.png'):
                self.send_response(200)
                self.send_header('Content-type', 'image/png')
                self.end_headers()
                
                with open(filepath, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                self.send_error(404, "Image not found")
                
        except Exception as e:
            self.send_error(500, f"Error serving image: {str(e)}")

    def handle_json_upload(self, post_data):
        """处理JSON格式的上传"""
        global received_shots
        
        try:
            shot_data = json.loads(post_data.decode('utf-8'))
            shot_id = int(time.time())
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"shot_{timestamp}_{shot_id}.json"
            filepath = os.path.join(DATA_DIR, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(shot_data, f, indent=2, ensure_ascii=False)
            
            # 先发送响应，避免客户端超时
            response = {
                'status': 'success',
                'id': shot_id,
                'message': f'Shot data received and saved as {filename}',
                'timestamp': timestamp,
                'image_generated': False,
                'auto_printed': PRINT_ENABLED
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            try:
                self.wfile.write(json.dumps(response).encode('utf-8'))
                self.wfile.flush()
            except BrokenPipeError:
                print("⚠️ 客户端提前断开连接，但数据已保存")
                return
            
            # 然后在后台处理图表生成和打印
            def background_processing(shots_list):
                try:
                    # 生成图表
                    image_filename = filename.replace('.json', '.png')
                    image_path = os.path.join(IMAGE_DIR, image_filename)
                    image_generated = self.create_coffee_plot(filepath, image_path)
                    
                    # 记录接收信息
                    shot_info = {
                        'id': shot_id,
                        'timestamp': timestamp,
                        'filename': filename,
                        'data_size': len(post_data),
                        'clock': shot_data.get('clock', 'unknown'),
                        'profile': shot_data.get('profile', {}).get('title', 'unknown') if isinstance(shot_data.get('profile'), dict) else shot_data.get('profile', 'unknown'),
                        'success': True,
                        'upload_type': 'json'
                    }
                    
                    received_shots.append(shot_info)
                    # 注意：这里不需要重新赋值，直接操作原列表
                    if len(shots_list) > 50:
                        del shots_list[:-50]
                    
                    # 打印接收信息
                    self.print_shot_info(shot_info)
                    
                    # 自动打印（如果启用）
                    if PRINT_ENABLED and image_generated:
                        print("🖨️ 开始在后台打印...")
                        self.print_image(image_path)
                    
                    print(f"✅ 后台处理完成: {filename}")
                    
                except Exception as e:
                    print(f"❌ 后台处理出错: {e}")
            
            # 在后台线程中处理
            threading.Thread(target=background_processing, args=(received_shots,), daemon=True).start()
                
        except json.JSONDecodeError as e:
            self.send_error(400, f"Invalid JSON: {str(e)}")
        except Exception as e:
            self.send_error(500, f"Error processing JSON: {str(e)}")

    def handle_multipart_upload(self, post_data, content_type):
        """处理multipart格式的上传"""
        global received_shots
        
        try:
            # 使用自定义的 multipart 解析器替代 cgi
            file_data = parse_multipart_form_data(post_data, content_type)
            
            shot_id = int(time.time())
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"shot_{timestamp}_{shot_id}.json"
            filepath = os.path.join(DATA_DIR, filename)
            
            with open(filepath, 'wb') as f:
                f.write(file_data)
            
            # 先发送响应
            response = {
                'status': 'success',
                'id': shot_id,
                'message': f'Shot data received and saved as {filename}',
                'timestamp': timestamp,
                'upload_type': 'multipart',
                'auto_printed': PRINT_ENABLED
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            try:
                self.wfile.write(json.dumps(response).encode('utf-8'))
                self.wfile.flush()
            except BrokenPipeError:
                print("⚠️ 客户端提前断开连接，但数据已保存")
                return
            
            # 后台处理
            def background_processing(shots_list):
                try:
                    # 生成图表
                    image_filename = filename.replace('.json', '.png')
                    image_path = os.path.join(IMAGE_DIR, image_filename)
                    image_generated = self.create_coffee_plot(filepath, image_path)
                    
                    # 解析JSON数据
                    try:
                        shot_data = json.loads(file_data.decode('utf-8'))
                        shot_info = {
                            'id': shot_id,
                            'timestamp': timestamp,
                            'filename': filename,
                            'data_size': len(file_data),
                            'clock': shot_data.get('clock', 'unknown'),
                            'profile': shot_data.get('profile', {}).get('title', 'unknown') if isinstance(shot_data.get('profile'), dict) else shot_data.get('profile', 'unknown'),
                            'success': True,
                            'upload_type': 'multipart'
                        }
                    except json.JSONDecodeError:
                        shot_info = {
                            'id': shot_id,
                            'timestamp': timestamp,
                            'filename': filename,
                            'data_size': len(file_data),
                            'clock': 'unknown',
                            'profile': 'unknown',
                            'success': True,
                            'note': 'Binary data (non-JSON)',
                            'upload_type': 'multipart'
                        }
                    
                    shots_list.append(shot_info)
                    if len(shots_list) > 50:
                        del shots_list[:-50]
                    
                    self.print_shot_info(shot_info)
                    
                    # 自动打印（如果启用）
                    if PRINT_ENABLED and image_generated:
                        print("🖨️ 开始在后台打印...")
                        self.print_image(image_path)
                    
                    print(f"✅ 后台处理完成: {filename}")
                    
                except Exception as e:
                    print(f"❌ 后台处理出错: {e}")
            
            threading.Thread(target=background_processing, args=(received_shots,), daemon=True).start()
                
        except Exception as e:
            self.send_error(500, f"Error processing multipart: {str(e)}")

    # 其他方法保持不变...
    def handle_print_control(self):
        """处理打印控制请求"""
        global PRINT_ENABLED
        
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            request_data = json.loads(post_data.decode('utf-8'))
            
            if 'enabled' in request_data:
                PRINT_ENABLED = request_data['enabled']
                response = {
                    'success': True,
                    'print_enabled': PRINT_ENABLED,
                    'message': f'Printing {"enabled" if PRINT_ENABLED else "disabled"}'
                }
                
            elif 'action' in request_data and request_data['action'] == 'print_shot':
                filename = request_data.get('filename')
                if filename:
                    json_path = os.path.join(DATA_DIR, filename)
                    image_path = os.path.join(IMAGE_DIR, filename.replace('.json', '.png'))
                    
                    if os.path.exists(image_path):
                        bmp_path = self.generate_print_image(image_path)
                        success = self.print_image(bmp_path)
                        response = {
                            'success': success,
                            'message': 'Print job sent' if success else 'Print failed'
                        }
                    else:
                        response = {
                            'success': False,
                            'message': 'Image file not found'
                        }
                else:
                    response = {
                        'success': False,
                        'message': 'No filename provided'
                    }
            else:
                response = {
                    'success': False,
                    'message': 'Invalid action'
                }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
            
        except Exception as e:
            self.send_error(500, f"Print control error: {str(e)}")

    def handle_clear_queue(self):
        """处理清空打印队列请求"""
        try:
            success = self.clear_print_queue()
            
            response = {
                'success': success,
                'message': '打印队列已清空' if success else '清空打印队列失败'
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
            
        except Exception as e:
            self.send_error(500, f"Clear queue error: {str(e)}")

    def get_print_queue_count(self):
        """获取打印队列任务数量"""
        try:
            result = subprocess.run(['lpstat', '-o'], capture_output=True, text=True)
            if result.returncode == 0:
                lines = [line for line in result.stdout.split('\n') if line.strip()]
                return len(lines)
            return 0
        except:
            return 0

    def get_print_queue_info(self):
        """获取详细的打印队列信息"""
        try:
            result = subprocess.run(['lpstat', '-o'], capture_output=True, text=True)
            queue_items = []
            
            if result.returncode == 0:
                lines = [line for line in result.stdout.split('\n') if line.strip()]
                for line in lines:
                    parts = line.split()
                    if len(parts) >= 5:
                        queue_items.append({
                            'job_id': parts[0],
                            'filename': parts[4] if len(parts) > 4 else 'Unknown',
                            'status': '等待中',
                            'added_time': datetime.now().strftime('%H:%M:%S')
                        })
            
            return {
                'queue_count': len(queue_items),
                'queue_items': queue_items
            }
        except Exception as e:
            return {
                'queue_count': 0,
                'queue_items': [],
                'error': str(e)
            }

    def clear_print_queue(self):
        """清空打印队列"""
        try:
            result = subprocess.run(['cancel', '-a', '-x'], capture_output=True, text=True)
            return result.returncode == 0
        except Exception as e:
            print(f"❌ 清空打印队列失败: {e}")
            return False

    def create_coffee_plot(self, input_file, output_file):
        """从Decent咖啡机JSON数据创建适合小票打印机的黑白位图"""
        try:
            print(f"📊 Generating chart: {input_file}")
            
            with open(input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            elapsed = list(map(float, data['elapsed']))
            pressure = list(map(float, data['pressure']['pressure']))
            flow = list(map(float, data['flow']['flow']))
            flow_by_weight = list(map(float, data['flow']['by_weight']))
            basket_temp = list(map(float, data['temperature']['basket']))
            
            min_length = min(len(elapsed), len(pressure), len(flow), len(flow_by_weight), len(basket_temp))
            elapsed = elapsed[:min_length]
            pressure = pressure[:min_length]
            flow = flow[:min_length]
            flow_by_weight = flow_by_weight[:min_length]
            basket_temp = basket_temp[:min_length]
            
            print(f"  Data length: {min_length} samples")
            """576"""
            multiplier = 1
            width_px = 576 * multiplier
            height_px = int(width_px * 180 / 80)
            dpi = 203
            fig_width = width_px / dpi
            fig_height = height_px / dpi
            
            fig = plt.figure(figsize=(fig_height, fig_width), dpi=dpi)

            font_m = 8 * multiplier
            font_l = 10 * multiplier
            
            gs = plt.GridSpec(1, 2, width_ratios=[0.65, 0.35])
            
            ax_left = fig.add_subplot(gs[0])
            ax_right = ax_left.twinx()
            ax_temp = ax_left.twinx()
            
            ax_temp.spines['left'].set_position(('axes', -0.15))
            ax_temp.yaxis.set_ticks_position('left')
            ax_temp.yaxis.set_label_position('left')
            
            plt.style.use('grayscale')
            
            line_width = 1.25 * multiplier
            
            ax_left.plot(elapsed, pressure, linestyle='-', linewidth=line_width, 
                         label='Pressure', color='black')
            ax_right.plot(elapsed, flow, linestyle='--', linewidth=line_width, 
                          label='Water Flow', color='black')
            ax_right.plot(elapsed, flow_by_weight, linestyle=':', linewidth=line_width, 
                          label='Coffee Flow', color='black')
            ax_temp.plot(elapsed, basket_temp, 
                         linestyle='-.', linewidth=line_width, 
                         label='Basket Temp', color='black')
            
            ax_left.set_ylim(0, 12)
            ax_left.set_ylabel('Pressure (Bar)', fontsize=font_m)
            
            flow_max = max(max(flow), max(flow_by_weight)) * 1.1
            ax_right.set_ylim(0, flow_max)
            ax_right.set_ylabel('Flow Rate (g/s)', fontsize=font_m)
            
            temp_min = min(basket_temp) * 0.95
            temp_max = max(basket_temp) * 1.05
            ax_temp.set_ylim(temp_min, temp_max)
            ax_temp.set_ylabel('Temp (°C)', fontsize=font_m)
            
            ax_left.set_xlabel('Time (s)', fontsize=font_m)
            
            lines_left, labels_left = ax_left.get_legend_handles_labels()
            lines_right, labels_right = ax_right.get_legend_handles_labels()
            lines_temp, labels_temp = ax_temp.get_legend_handles_labels()
            
            all_lines = lines_left + lines_right + lines_temp
            all_labels = labels_left + labels_right + labels_temp
            
            ax_left.legend(all_lines, all_labels, 
                           fontsize=font_m, loc='upper right', frameon=True, 
                           fancybox=False, framealpha=0.8,
                           ncol=2)
            
            ax_left.grid(True, linestyle='--', alpha=0.5, linewidth=line_width / 2)
            
            ax_left.tick_params(axis='both', which='major', labelsize=font_m)
            ax_right.tick_params(axis='y', which='major', labelsize=font_m)
            ax_temp.tick_params(axis='y', which='major', labelsize=font_m)
            
            for spine in ax_left.spines.values():
                spine.set_linewidth(line_width)
            for spine in ax_right.spines.values():
                spine.set_linewidth(line_width)
            for spine in ax_temp.spines.values():
                spine.set_linewidth(line_width)
            
            ax_text = fig.add_subplot(gs[1])
            ax_text.axis('off')
            
            profile_title = data['profile'].get('title', 'Unknown Profile')
            in_weight = data['meta'].get('in', 'N/A')
            out_weight = data['meta'].get('out', 'N/A')
            shot_time = data['meta'].get('time', 'N/A')
            grinder_setting = data['meta'].get('grinder', {}).get('setting', 'N/A')
            
            date_str = data.get('date', '')
            timestamp = data.get('timestamp', '')
            
            if date_str:
                try:
                    date_obj = datetime.strptime(date_str, '%a %b %d %H:%M:%S CST %Y')
                    formatted_date = date_obj.strftime('%Y-%m-%d')
                    formatted_time = date_obj.strftime('%H:%M:%S')
                except:
                    formatted_date = 'N/A'
                    formatted_time = 'N/A'
            elif timestamp:
                try:
                    date_obj = datetime.fromtimestamp(float(timestamp))
                    formatted_date = date_obj.strftime('%Y-%m-%d')
                    formatted_time = date_obj.strftime('%H:%M:%S')
                except:
                    formatted_date = 'N/A'
                    formatted_time = 'N/A'
            else:
                formatted_date = 'N/A'
                formatted_time = 'N/A'
            
            initial_basket_temp = basket_temp[0]
            
            text_content = [
                "Date & Time",
                "──────",
                formatted_date,
                formatted_time,
                "",
                "Profile",
                "──────",
                profile_title[:18] + "..." if len(profile_title) > 18 else profile_title,
                "",
                "Extraction",
                "──────",
                f"In: {in_weight}g",
                f"Out: {out_weight}g", 
                f"Time: {shot_time}s",
                "",
                "Grinder & Temp",
                "──────",
                f"Grind: {grinder_setting}",
                f"Temp: {initial_basket_temp:.1f}°C"
            ]
            
            for i, text in enumerate(text_content):
                if text in ["Date & Time", "Profile", "Extraction", "Grinder & Temp"]:
                    fontsize = font_l
                    weight = 'bold'
                elif text == "──────":
                    fontsize = font_m
                    weight = 'normal'
                elif text == "":
                    continue
                else:
                    fontsize = font_m
                    weight = 'normal'
                
                ax_text.text(0.05, 0.98 - i * 0.05, text, 
                            fontsize=fontsize, ha='left', va='top',
                            transform=ax_text.transAxes,
                            weight=weight)
            
            plt.tight_layout(pad=1.0)
            plt.savefig(output_file, dpi=dpi, bbox_inches='tight', 
                        facecolor='white', edgecolor='none',
                        pad_inches=0.1)
            plt.close(fig)
            
            print(f"✅ Chart generated: {output_file}")
            return True
            
        except Exception as e:
            print(f"❌ Chart generation failed: {str(e)}")
            return False

    def generate_print_image(self, png_path):
        """为打印生成专门的BMP文件"""
        try:
            bmp_path = png_path.replace('.png', '_print.bmp')
            
            target_width = 576 * 4
            target_height = int(target_width * 180 / 80)
            
            img = Image.open(png_path)
            img = img.convert('L')
            img = img.resize((target_height, target_width), Image.LANCZOS)
            img_rotated = img.rotate(90, expand=True)
            
            threshold = 200
            img_rotated = img_rotated.point(lambda p: 255 if p > threshold else 0)
            img_rotated = img_rotated.convert('1')
            
            img_rotated.save(bmp_path, 'BMP')
            
            print(f"🖨️ Print image generated: {bmp_path}")
            return bmp_path
            
        except Exception as e:
            print(f"❌ Print image generation failed: {str(e)}")
            return png_path

    def print_image(self, image_path):
        """打印图像"""
        if not PRINT_ENABLED:
            print("🖨️ Printing disabled, skipping")
            return False
            
        try:
            print("🖨️ Sending print job...")
            
            # 使用优化的打印命令减少走纸
            cmd = [
                'lpr', 
                image_path,
                '-o', 'media=Custom.80x180mm',
                '-o', 'fit-to-page',
                '-o', 'margin-top=0',
                '-o', 'margin-bottom=0'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Print job sent successfully")
                
                if image_path.endswith('_print.bmp') and os.path.exists(image_path):
                    os.remove(image_path)
                    
                return True
            else:
                # 备用打印命令
                cmd = [
                    'lp',
                    image_path,
                    '-o', 'media=Custom.80x180mm',
                    '-o', 'fit-to-page',
                    '-o', 'margin-top=0'
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    print("✅ Print job sent (using lp command)")
                    if image_path.endswith('_print.bmp') and os.path.exists(image_path):
                        os.remove(image_path)
                    return True
                else:
                    print(f"❌ Print failed: {result.stderr}")
                    return False
                    
        except Exception as e:
            print(f"❌ Print error: {str(e)}")
            return False

    def print_shot_info(self, shot_info):
        """打印接收信息"""
        print("=" * 60)
        print("🎯 接收到新的冲泡数据!")
        print("=" * 60)
        print(f"📁 文件: {shot_info['filename']}")
        print(f"🆔 ID: {shot_info['id']}")
        print(f"⏰ 时间: {shot_info['timestamp']}")
        print(f"📊 数据大小: {shot_info['data_size']} bytes")
        print(f"📤 上传方式: {shot_info.get('upload_type', 'unknown')}")
        
        if shot_info.get('clock') != 'unknown':
            print(f"🕐 冲泡时钟: {shot_info['clock']}")
        
        if shot_info.get('profile') != 'unknown':
            print(f"👤 冲煮方案: {shot_info['profile']}")
            
        print(f"🖨️ 自动打印: {'启用' if PRINT_ENABLED else '禁用'}")
        print("✅ 数据保存成功!")
        print("=" * 60)

    def log_message(self, format, *args):
        """自定义日志格式"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] {format % args}")

def ensure_directories():
    """确保必要的目录存在"""
    for directory in [DATA_DIR, IMAGE_DIR]:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"📁 创建目录: {directory}")

def print_server_info(port):
    """打印服务器信息"""
    print("")
    print("🍳 " + "=" * 60)
    print("🍳           PrintTheShot Server - 完整版")
    print("🍳 " + "=" * 60)
    print(f"🍳  服务器运行在: http://localhost:{port}")
    print(f"🍳  管理界面: http://localhost:{port}/")
    print(f"🍳  上传端点: http://localhost:{port}/upload")
    print(f"🍳  数据目录: {os.path.abspath(DATA_DIR)}")
    print(f"🍳  图片目录: {os.path.abspath(IMAGE_DIR)}")
    print(f"🍳  最大用户数: {MAX_USERS}")
    print(f"🍳  打印功能: {'启用' if PRINT_ENABLED else '禁用'}")
    print(f"🍳  启动时间: {server_start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("🍳 " + "=" * 60)
    print("🍳  按 Ctrl+C 停止服务器")
    print("")

def main():
    """主函数"""
    port = 8000
    
    ensure_directories()
    print_server_info(port)
    
    def signal_handler(sig, frame):
        print("\n\n🛑 服务器被用户中断")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        # 创建支持端口复用的服务器
        class ReuseTCPServer(socketserver.TCPServer):
            allow_reuse_address = True  # 关键设置
            
        with ReuseTCPServer(("", port), PrintTheShotHandler) as httpd:
            print(f"✅ 服务器启动成功，监听端口 {port}")
            print("🔄 等待连接...")
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\n🛑 服务器停止")
    except Exception as e:
        print(f"❌ 服务器错误: {e}")
    finally:
        print("👋 服务器已停止")

if __name__ == "__main__":
    main()
