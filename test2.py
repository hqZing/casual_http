
import socket
import ssl

hostname = "www.baidu.com"
port = 443

# 创建默认上下文，可以进行证书认证
context = ssl.create_default_context()

# 创建一个被包装过的套接字
ssock = context.wrap_socket(socket.socket(socket.AF_INET), server_hostname=hostname)

# 连接主机
ssock.connect((hostname, port))

# 打印证书信息
cert = ssock.getpeercert()
print(cert)

# 发送HTTP请求
ssock.sendall(b"GET / HTTP/1.1\r\nHost: " + hostname.encode() + b"\r\nConnection: close\r\n\r\n")

# 接收HTTP数据
buffer = b""
while 1:
    d = ssock.recv(1024)
    if d:
        buffer += d
    else:
        break

print(buffer)
