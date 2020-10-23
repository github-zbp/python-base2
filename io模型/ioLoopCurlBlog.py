# coding=utf-8

from selectors import DefaultSelector, EVENT_READ, EVENT_WRITE
from urllib.parse import urlparse
import socket
import os

# 使用多路复用 + 事件循环 + 回调的方式实现并发http请求

# 定义一个爬虫类, 这个爬虫类很简单，传入一个url，爬虫负责将这个url的内容获取到即可
class Crawler:
    select = DefaultSelector()        # 定义一个selector对象存在类变量中, 目前在windows环境，所以自动选择select多路复用器
    finished = False                      # 爬取是否结束，该变量用于控制停止事件循环监听，如果爬取完所有url则停止loopEvents()的循环（停止监听事件）

    # 开始批量爬取
    @classmethod
    def start(cls, urls):
        cls.urls = urls

        for url in cls.urls:
            crawler = cls(url)
            crawler.getUrl()

    # urls是要爬取的url列表
    def __init__(self, url):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.setblocking(False)  # 设置为非阻塞状态
        self.url = url
        self.response = b''         # 用于累积保存本次请求接收到的所有数据

    # 爬取单个页面
    def getUrl(self):
        # 解析url，构建请求报文
        self.__parseUrl()

        # 连接服务器,这里必须用try
        try:
            self.client.connect((self.host, 80))
        except:
            pass

        # 注册监听写事件,对于客户端而言，与服务器建立好连接后可视为写就绪，写就绪后就可以发送请求报文
        self.select.register(self.client, EVENT_WRITE, self.__sendReq)  # 设置写就绪后的回调动作是发起请求

    # 根据url解析主机和爬取的路径，已经构建请求报文
    def __parseUrl(self):
        url_component = urlparse(self.url)
        self.host = url_component.netloc  # url的主机名
        self.path = '/' if url_component.path == '' else url_component.path
        self.send_msg = "GET %s HTTP/1.1\r\nHost: %s\r\nConnection: close\r\n\r\n" % (self.path, self.host)

    # 连接建立后，发起请求
    def __sendReq(self, key):   # key是我们待会要手动往回调函数传入的SelectorKey对象，该对象包含了触发了事件的socket，可以对这个socket做出相关操作
        client = key.fileobj
        client.send(self.send_msg.encode('utf-8'))      # 发送请求报文

        # 发送请求报文后，就要接收响应，不过要等到读事件就绪（就是说等到服务端把响应发过来，client的内核缓冲区有数据可读的时候）
        # 所以我们可以监听读事件是否就绪（用modify更改监听写事件为监听读事件）
        self.select.modify(client, EVENT_READ, self.__recvResponse)

    # 服务器返回响应，客户端读就绪，开始接收响应
    def __recvResponse(self, key):
        client = key.fileobj
        data = client.recv(1024)
        if data:
            self.response += data
        else:   # 数据接收完毕
            # print("客户端： %s" % str(key.fd))
            self.select.unregister(client)     # 解除监听
            client.close()                     # 关闭连接

            # 获取完url的内容后，删除self.urls中的该url
            self.__class__.urls.remove(self.url)

            self.__class__.finished = False if len(self.urls) else True

            self.__saveHtml()

    # 保存页面到文件
    def __saveHtml(self):
        try:
            dir_path = './crawled_page/'
            fname = 'index.html' if self.path =='/' else self.path.strip('/').strip('.html') + '.html'
            content_arr = self.response.decode('utf-8').split("\r\n\r\n")        # 第一个元素是响应头，应该去掉，只留响应体的内容
            content_arr[0] = ''
            content = ''.join(content_arr)

            if not os.path.isdir(dir_path):
                os.mkdir(dir_path)

            with open(dir_path + fname, 'w', encoding='utf-8') as f:
                f.write(content)
            print("%s 爬取成功" % str(fname))
        except BaseException as e:
            print(e)

    # 循环监听事件（阻塞），在这个类方法中，多路复用器会开始监听所有客户端socket的事件状态；事件就绪后回调函数也是在这个方法里面调用的
    @classmethod
    def loopEvents(cls):
        while not cls.finished:
            events = cls.select.select()     # 监听所有socket的事件，该过程是阻塞的;返回一个包含多个元组的列表
            for key, mask in events:    # key是selectorKey对象，mask是事件的类型，是一个整型
                callback = key.data     # 调用register监听client事件时传入的回调函数，一个register对应一个callback
                callback(key)

# 定义要爬取的url
urls = [
    "http://zbpblog.com/blog-192.html",
    "http://zbpblog.com/blog-191.html",
    "http://zbpblog.com/blog-190.html",
    "http://zbpblog.com/",
    "http://zbpblog.com/cate-php",
    "http://zbpblog.com/cate-python",
]

Crawler.start(urls)     # 开始建立连接（但是start中开没开始发请求，发请求发生在下面的loopEvents中）
Crawler.loopEvents()    # 开始监听事件
