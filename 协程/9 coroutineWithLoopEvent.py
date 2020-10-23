# coding=utf-8

from selectors import DefaultSelector, EVENT_READ, EVENT_WRITE
from urllib.parse import urlparse
import socket
import os

# 使用多路复用 + 事件循环 + 协程的方式实现并发http请求

# 定义一个Future类，一个Future对象代表一个尚未完成的事件A（读事件或者写事件）
# Future对象的作用时存储一个未完成事件的回调函数，并在事件就绪时执行回调
class Future:
    def __init__(self):
        self.callbacks = []      # 存放着事件A对应的回调函数，在事件循环的时候监控到事件A就绪时就会调用这些回调函数（在本例中self.callbacks其实只会存一个回调函数Task.step）

    def runCallback(self):
        for cb in self.callbacks:
            cb()

# 定义一个Task任务类，一次url请求就是一个任务，就会调用一次getUrl方法（就会创建一个协程），也会创建一个任务类
# Task任务类的作用是驱动协程，让协程执行某些需要等待但不会阻塞的操作时暂停(通过yield)，在这个操作完成后（事件就绪后）恢复协程运行(通过next)
class Task:
    def __init__(self, coroutine):  # 需要传入一个协程对象
        self.coroutine = coroutine
        self.step()     # 预激活协程

    # step方法的作用：驱动协程恢复运行。只有当事件就绪时，该方法才会被调用,所以准确的说是事件循环驱动step的调用从而驱动协程的恢复。
    def step(self):
        try:
            f = next(self.coroutine)     # 恢复协程，协程恢复后肯定会注册一个新的事件，需要协程把这个新事件（Future对象）产出并交给Task类的f变量接收
        except StopIteration as e:      # 协程运行结束
            return
        f.callbacks.append(self.step)   # 把下一次驱动协程恢复的方法放在等待事件f的回调中，当事件就绪时f.callbacks中的方法step就会被调用，协程就会恢复运行

# 定义一个爬虫类, 这个爬虫类很简单，传入一个url，爬虫负责将这个url的内容获取到即可
class Crawler:
    select = DefaultSelector()        # 定义一个selector对象存在类变量中, 目前在windows环境，所以自动选择select多路复用器
    finished = False                      # 爬取是否结束，该变量用于控制停止事件循环监听，如果爬取完所有url则停止loopEvents()的循环（停止监听事件）

    # urls是要爬取的url列表
    def __init__(self, url):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.setblocking(False)  # 设置为非阻塞状态
        self.url = url
        self.response = b''         # 用于累积保存本次请求接收到的所有数据
        global urls

    # 爬取单个页面, 这是个协程方法
    def getUrl(self):
        # 解析url，构建请求报文
        self.__parseUrl()

        # 连接服务器,这里必须用try
        try:
            self.client.connect((self.host, 80))
        except:
            pass

        # 连接是一个未完成的事件，所以要创建一个Future对象
        f = Future()

        # 注册监听写事件,对于客户端而言，与服务器建立好连接后可视为写就绪，写就绪后就可以发送请求报文
        # self.select.register(self.client, EVENT_WRITE, data=self.__sendReq)  # 这是回调版本的注册事件代码，下面是协程版本的注册事件代码
        self.select.register(self.client, EVENT_WRITE, data=f)  # 这里我把事件的回调设置为f对象，函数引用是对象，f也是一个对象，所以这里是可以这样做的

        # 暂停协程，直到事件就绪，f对象中的Task对象的step方法被调用才会恢复协程
        # 必须先register注册事件，才能yield f暂停协程。如果先暂停就会永远触发不了事件的回调，因为事件都没注册怎么可能监控得到事件呢，监控不到事件怎么去触发它的回调step呢，这样的结果就是协程一直处于暂停状态
        yield f     # 产出Future给Task，Task会存放一个step回调给f对象

        self.select.unregister(self.client)     # 这里有一个注意点，select.unregister解除监听写事件必须在client.send之前，否则会在下面的while循环中报错说socket连接关闭（原因是写事件就绪协程恢复运行去recv接收响应，但是其实读事件没有就绪，所以recv到了空字节，所以执行了后面的client.close()），这里花了我一点时间排雷

        # 运行到这里，说明协程被恢复，写事件就绪，可以发送请求给服务器了
        self.client.send(self.send_msg.encode('utf-8'))  # 发送请求报文

        # 发送请求又是一个还未完成的事件（读事件未就绪），此时又需要创建一个新的Future对象，一个Future对象对应一个事件嘛
        # f = Future()    # 这里的创建f对象包含在了下面的while循环中,所以就把这条冗余代码注释掉

        # 发送请求报文后，就要接收响应，不过要等到读事件就绪（就是说等到服务端把响应发过来，client的内核缓冲区有数据可读的时候）
        # 所以我们可以监听读事件是否就绪（用modify更改监听写事件为监听读事件）
        # self.select.modify(self.client, EVENT_READ, data=f)

        while True:     # 循环读取，响应报文内容可能很多，一次recv无法读取完，每次recv前都要执行一次yield暂停协程等待读事件就绪
            f = Future()
            self.select.register(self.client, EVENT_READ, data=f)       # 为什么每循环一次都要重新注册一次读事件？因为每循环一次都需要往register中传入一个新的Future对象
            yield f  # 暂停协程

            # 协程被恢复，说明客户端读就绪，可以解除上一次监听的读事件并开始接收响应
            self.select.unregister(self.client)
            data = self.client.recv(1024)
            if data:
                self.response += data
            else:  # 数据接收完毕
                self.client.close()  # 关闭连接

                # 获取完url的内容后，删除self.urls中的该url
                urls.remove(self.url)

                self.__class__.finished = False if len(urls) else True

                self.__saveHtml()

                break   # 跳出循环，终止协程

    # 根据url解析主机和爬取的路径，已经构建请求报文
    def __parseUrl(self):
        url_component = urlparse(self.url)
        self.host = url_component.netloc  # url的主机名
        self.path = '/' if url_component.path == '' else url_component.path
        self.send_msg = "GET %s HTTP/1.1\r\nHost: %s\r\nConnection: close\r\n\r\n" % (self.path, self.host)

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

        finally:    # 最后无论如何都要销毁自身这个 Crawler 类，不然每请求一个url就创建一个crawler类又不销毁，浪费内存
            del self


    # 循环监听事件（阻塞），在这个类方法中，多路复用器会开始监听所有客户端socket的事件状态；事件就绪后回调函数也是在这个方法里面调用的
    # 回调函数step被调用会恢复协程的运行
    @classmethod
    def loopEvents(cls):
        while not cls.finished:
            events = cls.select.select()     # 监听所有socket的事件，该过程是阻塞的;返回一个包含多个元组的列表
            for key, mask in events:    # key是selectorKey对象,包含该事件的回调函数（data属性，在这里data属性放着的是Future对象），mask是事件的类型，是一个整型
                f = key.data     # 调用register监听client事件时传入的Future对象，一个register的事件对应一个Future
                f.runCallback()     # callback做的事情是恢复协程的运行

if __name__ == "__main__":
    # 定义要爬取的url
    urls = [
        "http://zbpblog.com/blog-192.html",
        "http://zbpblog.com/blog-191.html",
        "http://zbpblog.com/blog-190.html",
        "http://zbpblog.com/",
        "http://zbpblog.com/cate-php",
        "http://zbpblog.com/cate-python",
    ]

    for url in urls:    # 每爬一个url就要创建一个crawler类，创建一个coro协程，创建一个任务对象和多个Future对象（Future对象是在协程中创建的）
        crawler = Crawler(url)
        coro = crawler.getUrl()     # 创建一个协程
        Task(coro)              # 创建一个Task类用于驱动coro协程, Task的__init__已经激活了协程，协程开始运行

    Crawler.loopEvents()    # 开始循环监听事件（事件循环）

# 上面使用了协程之后，连接、发请求、接收响应就都按顺序写在一个代码块里面的，实现了同步的代码编写形式。
# 这个例子由于时IO密集型操作，所以时间基本上都花在了cls.select.select()的阻塞等待，cpu资源其实消耗的很少。像这种io密集型操作很适合用多线程和协程来完成。而协程又比多线程的消耗少，切换速度快（协程切换是函数的切换，而多线程是线程间切换）
# Future和Task这两个概念很重要，之后要学习的asyncio包中也是通过这两个类对象完成驱动协程和事件回调调用的。