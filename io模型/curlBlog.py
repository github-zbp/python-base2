# coding=utf-8

import socket

# 使用socket请求我自己的博客的首页
host = "zbpblog.com"
port = 80

# 创建socket
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# 建立tcp连接，三次握手
client.connect((host, port))

# 发送请求报文, 请求报文可以不用自己写，直接在chrome浏览器F12即可查看
# 报文内容只需要请求头（GET /xxx HTTP/1.1）和请求行中的Host和Connection字段即可，具体要看你请求的页面要求必须有哪些请求行字段。报文最后必须使用两个\r\n表示请求报文结束，否则运行到下面recv的时候会一直阻塞，因为服务端会认为你的报文没发完（所以服务端就不执行send，所以客户端recv就阻塞住了）

# request_msg = "GET / HTTP/1.1\r\nHost: zbpblog.com\r\nConnection: close\r\n\r\n"    # Connection为close，表示使用短连接的方式
request_msg = "GET / HTTP/1.1\r\nHost: zbpblog.com\r\nConnection: keep-alive\r\n\r\n"    # Connection为keep-alive，表示使用长连接的方式

client.sendall(request_msg.encode("utf-8"))     # 发送数据, 发送的数据得是字节流而不能是字符串，所以要对字符串编码一下转为byte类型
client.sendall(request_msg.encode("utf-8"))

# 等待服务器返回响应,返回的数据可能大于1024字节，所以要调用多次recv直到接收完全部的数据
data = b""      # 接收到的字节流数据
while True:
    res = client.recv(1024)     # 该recv会阻塞直到服务端有响应返回

    if res:
        data += res
    else:
        break

print(data.decode("utf-8"))
client.close()