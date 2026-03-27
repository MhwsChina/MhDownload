import socket
import threading
import json
import time
import sys
out=print
class WebSocketServer:
    def __init__(self, host='localhost', port=14431,send=print):
        self.host = host
        self.port = port
        self.send=send
        self.server_socket = None
        self.clients = []
        self.running = False
        self.client_lock = threading.Lock()
        
    def start(self):
        """启动WebSocket服务器"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.running = True
            
            out(f"MhDownload 浏览器插件服务已启动")
            out("等待浏览器插件连接...")
            
            # 接受客户端连接的线程
            accept_thread = threading.Thread(target=self.accept_clients)
            accept_thread.daemon = True
            accept_thread.start()
            
                
        except Exception as e:
            out(f"服务器启动失败: {e}")
            self.stop()
    
    def accept_clients(self):
        """接受客户端连接"""
        while self.running:
            try:
                client_socket, client_address = self.server_socket.accept()
                out(f"浏览器插件连接: {client_address}")
                
                # 为每个客户端创建处理线程
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, client_address)
                )
                client_thread.daemon = True
                client_thread.start()
                
            except Exception as e:
                if self.running:
                    out(f"接受浏览器连接失败: {e}")
                break
    
    def handle_client(self, client_socket, client_address):
        """处理单个客户端连接"""
        try:
            # 处理WebSocket握手
            handshake = client_socket.recv(1024).decode('utf-8')
            
            if not self.perform_handshake(client_socket, handshake):
                out(f"WebSocket握手失败: {client_address}")
                client_socket.close()
                return
            
            out(f"与浏览器连接成功: {client_address}")
            
            # 添加到客户端列表
            with self.client_lock:
                self.clients.append(client_socket)
            
            # 接收消息
            while self.running:
                try:
                    # 接收WebSocket帧
                    data = self.receive_websocket_frame(client_socket)
                    if data:
                        self.handle_message(data, client_address)
                except Exception as e:
                    out(f"接收消息失败: {e}")
                    break
                    
        except Exception as e:
            out(f"处理浏览器连接失败: {e}")
        finally:
            # 移除客户端
            with self.client_lock:
                if client_socket in self.clients:
                    self.clients.remove(client_socket)
            client_socket.close()
            print(f"浏览器断开连接: {client_address}")
    
    def perform_handshake(self, client_socket, handshake):
        """执行WebSocket握手"""
        try:
            lines = handshake.split('\r\n')
            key = None
            
            for line in lines:
                if line.startswith('Sec-WebSocket-Key:'):
                    key = line.split(':')[1].strip()
                    break
            
            if not key:
                return False
            
            import hashlib
            import base64
            
            # 计算WebSocket接受密钥
            magic = '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'
            accept = base64.b64encode(
                hashlib.sha1((key + magic).encode()).digest()
            ).decode()
            
            # 发送握手响应
            response = (
                'HTTP/1.1 101 Switching Protocols\r\n'
                'Upgrade: websocket\r\n'
                'Connection: Upgrade\r\n'
                f'Sec-WebSocket-Accept: {accept}\r\n\r\n'
            )
            
            client_socket.send(response.encode())
            return True
            
        except Exception as e:
            out(f"握手处理失败: {e}")
            return False
    
    def receive_websocket_frame(self, client_socket):
        """接收WebSocket帧"""
        try:
            # 接收第一个字节（FIN, RSV, OPCODE）
            header = client_socket.recv(2)
            if len(header) < 2:
                return None
            
            first_byte = header[0]
            second_byte = header[1]
            
            # 获取opcode
            opcode = first_byte & 0x0F
            
            # 获取掩码和长度
            masked = (second_byte & 0x80) != 0
            payload_len = second_byte & 0x7F
            
            # 读取扩展长度
            if payload_len == 126:
                ext_len = client_socket.recv(2)
                payload_len = int.from_bytes(ext_len, byteorder='big')
            elif payload_len == 127:
                ext_len = client_socket.recv(8)
                payload_len = int.from_bytes(ext_len, byteorder='big')
            
            # 读取掩码密钥
            mask_key = None
            if masked:
                mask_key = client_socket.recv(4)
            
            # 读取负载数据
            payload = client_socket.recv(payload_len)
            
            # 解码数据
            if masked and mask_key:
                decoded = bytearray(payload)
                for i in range(len(decoded)):
                    decoded[i] ^= mask_key[i % 4]
                payload = bytes(decoded)
            
            # 关闭连接帧
            if opcode == 0x08:
                return None
            
            return payload.decode('utf-8')
            
        except Exception as e:
            out(f"接收帧失败: {e}")
            return None
    
    def send_websocket_frame(self, client_socket, data):
        """发送WebSocket帧"""
        try:
            payload = data.encode('utf-8')
            payload_len = len(payload)
            
            # 构建帧头
            frame = bytearray()
            frame.append(0x81)  # FIN + 文本帧
            
            if payload_len <= 125:
                frame.append(payload_len)
            elif payload_len <= 65535:
                frame.append(126)
                frame.extend(payload_len.to_bytes(2, byteorder='big'))
            else:
                frame.append(127)
                frame.extend(payload_len.to_bytes(8, byteorder='big'))
            
            # 添加负载
            frame.extend(payload)
            
            client_socket.send(frame)
            return True
            
        except Exception as e:
            out(f"发送帧失败: {e}")
            return False
    
    def handle_message(self, message, client_address):
        """处理接收到的消息"""
        try:
            data = json.loads(message)
            msg_type = data.get('type')
            
            if msg_type == 'download':
                url = data.get('url')
                timestamp = data.get('timestamp')
                self.send(url)
                
                # 这里可以调用你的下载器函数
                # 例如: your_downloader.add_task(url)
                
                # 发送确认消息
                response = {
                    'type': 'ack',
                    'status': 'received',
                    'url': url
                }
                
                # 向客户端发送确认
                with self.client_lock:
                    for client in self.clients:
                        self.send_websocket_frame(client, json.dumps(response))
                
        except json.JSONDecodeError:
            out(f"收到无效JSON: {message}")
        except Exception as e:
            out(f"处理消息失败: {e}")
    
    def stop(self):
        """停止服务器"""
        out("\n正在停止服务器...")
        
        # 关闭所有客户端连接
        with self.client_lock:
            for client in self.clients:
                try:
                    client.close()
                except:
                    pass
            self.clients.clear()
        
        # 关闭服务器socket
        if self.server_socket:
            self.server_socket.close()
        
        out("服务器已停止")

'''def main():
    """主函数"""
    server = WebSocketServer('localhost', 14431)
    
    try:
        server.start()'''
