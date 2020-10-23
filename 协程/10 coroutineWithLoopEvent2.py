from selectors import DefaultSelector, EVENT_READ, EVENT_WRITE
from urllib.parse import urlparse
import socket
import os

class Future:
    def __init__(self):
        self.callbacks = []      

    def runCallback(self):
        for cb in self.callbacks:
            cb()

class Task:
    def __init__(self, coroutine):  
        self.coroutine = coroutine
        self.step()     

    def step(self):
        try:
            f = next(self.coroutine)     
        except StopIteration as e:      
            return
        f.callbacks.append(self.step)   

class Crawler:
    select = DefaultSelector()        
    finished = False                      

    def __init__(self, url):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.setblocking(False)  
        self.url = url
        self.response = b''         
        global urls

    # getUrl 这个委派生成器中创建的了3个yield from 通道用于调用方和3个子生成器的通信。
    # 但是这3个通道不是同时建立的，而是先建立一个完了再建立下一个，同一时刻只有一个通道存在。也就是说同一时刻调用方只和1个子生成器通信（同一时刻调用方只运行1个协程）
    def getUrl(self):
        self.__parseUrl()

        # 先暂停执行连接
        yield from self.__connect()

        # 连接完成后暂停执行发请求
        yield from self.__sendReq()

        # 发送请求后执行接收响应
        yield from self.__recvResponse()

    def __connect(self):
        try:
            self.client.connect((self.host, 80))
        except:
            pass

        f = Future()

        self.select.register(self.client, EVENT_WRITE, data=f)

        yield f

    def __sendReq(self):
        self.select.unregister(self.client)
        
        self.client.send(self.send_msg.encode('utf-8'))

        f = Future()

        self.select.register(self.client, EVENT_READ, data=f)

        yield f

    def __recvResponse(self):
        while True:
            self.select.unregister(self.client)
            data = self.client.recv(1024)


            if data:
                self.response += data
                f = Future()
                self.select.register(self.client, EVENT_READ, data=f)
                yield f
            else:
                self.client.close()

                urls.remove(self.url)

                self.__class__.finished = False if len(urls) else True

                self.__saveHtml()

                break



    def __parseUrl(self):
        url_component = urlparse(self.url)
        self.host = url_component.netloc  
        self.path = '/' if url_component.path == '' else url_component.path
        self.send_msg = "GET %s HTTP/1.1\r\nHost: %s\r\nConnection: close\r\n\r\n" % (self.path, self.host)

    def __saveHtml(self):
        try:
            dir_path = './crawled_page2/'
            fname = 'index.html' if self.path =='/' else self.path.strip('/').strip('.html') + '.html'
            content_arr = self.response.decode('utf-8').split("\r\n\r\n")        
            content_arr[0] = ''
            content = ''.join(content_arr)

            if not os.path.isdir(dir_path):
                os.mkdir(dir_path)

            with open(dir_path + fname, 'w', encoding='utf-8') as f:
                f.write(content)
            print("%s 爬取成功" % str(fname))
        except BaseException as e:
            print(e)

        finally:    
            del self

    @classmethod
    def loopEvents(cls):
        while not cls.finished:
            events = cls.select.select()     
            for key, mask in events:    
                f = key.data     
                f.runCallback()     

if __name__ == "__main__":
    urls = [
        "http://zbpblog.com/blog-192.html",
        "http://zbpblog.com/blog-191.html",
        "http://zbpblog.com/blog-190.html",
        "http://zbpblog.com/",
        "http://zbpblog.com/cate-php",
        "http://zbpblog.com/cate-python",
    ]

    for url in urls:    
        crawler = Crawler(url)
        coro = crawler.getUrl()     
        Task(coro)              

    Crawler.loopEvents()    



