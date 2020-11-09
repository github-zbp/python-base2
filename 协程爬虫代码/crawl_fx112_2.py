# coding=utf-8

import asyncio, aiohttp, aiomysql, re, hashlib, os, aiofiles, time
from asyncio import Queue
from bs4 import BeautifulSoup

class Crawler:
    def __init__(self, baseUrl, dbCfg, listUrlInfo, picPath = './pic2', pageRows=10, maxCoroNum = 20, tcpConnNum = 20, maxMonitorCount = 10, insertRows = 20):
        self.baseUrl = baseUrl.strip('/') + "/"
        self.picPath = picPath              # 下载图片到本地的目录
        self.queue = Queue(maxsize=50)     # 队列，用于放要爬取的url，长度为50
        self.dbCfg = dbCfg
        self.sem = asyncio.Semaphore(maxCoroNum)     # 使用信号量限制并发的coro协程的最大数量
        self.tcpConnNum = tcpConnNum    # tcp连接池中最大并发连接数
        self.session = None             # 存放会话连接池的session对象
        self.dbPool = None              # Mysql连接池
        self.listUrlInfo = listUrlInfo
        self.pageRows = pageRows        # 每页列表页有多少篇文章
        self.crawledUrl = set()         # 用于去重的url集合
        self.loop = None                # 事件循环对象
        self.lockForSql = asyncio.Lock()    # 用于同步多个数据入库的协程的锁
        self.monitorCount = 0       # 任务监控计数器
        self.maxMonitorCount = maxMonitorCount

        ############################################
        self.dbQueue = Queue(maxsize=500)       # 存放数据入库任务
        self.dbSem = asyncio.Semaphore(maxCoroNum)      # 用于限制并发的 insertDb 协程的最大数量

    # 开启事件循环(启动协程)
    def startLoop(self):
        self.loop = asyncio.get_event_loop()
        asyncio.ensure_future(self.start())         # 这里用create_task()会报错,但是ensure_future()不会,两个方法都可以将协程放到事件循环中运行.
        self.loop.run_forever()                     # 必须使用run_forever()不能用run_until_complete()
        # self.loop.run_until_complete(self.start())          # 将主协程放入事件循环的任务列表中开始运行主携程，这行代码会等待
        # self.loop.run_until_complete(asyncio.sleep(0.25))   # 所有协程结束运行后，睡个0.25秒，让所有tcp连接，mysql连接都断开后才结束整个线程以免报警告

    # 主协程
    async def start(self):
        # 在开始爬取之前，先创建mysql连接池
        self.pool = await aiomysql.create_pool(loop=self.loop, maxsize = 50, minsize = 50, **self.dbCfg)

        # 开启 produceListUrl 和 consume 这两个协程，将他们加入到任务列表中开始执行
        asyncio.create_task(self.produceListUrl())
        asyncio.create_task(self.consume())
        asyncio.create_task(self.dbConsume())       # 开启 dbConsume 协程不断生成 insertDb子协程进行数据入库

        # 开启一个monitor协程用于所有任务完成的时候停止事件循环
        # asyncio.create_task(self.monitor())

    # 用于监控任务队列 self.queue 是否长时间没有任务, 如果检查到self.queue为空的次数超过self.maxMonitorCount规定的次数则停止事件循环,结束整个线程
    async def monitor(self):
        while True:
            if self.queue.qsize() == 0:
                self.monitorCount += 1
            else:
                self.monitorCount = 0

            if self.monitorCount >= self.maxMonitorCount:
                print("所有任务已完成, 事件循环停止")
                self.pool.close()           # 先关闭mysql连接池
                await self.session.close()           # 先关闭tcp连接池
                self.loop.stop()            # 然后才关闭事件循环

            # 每0.5秒检测一次任务队列
            await asyncio.sleep(0.5)


    # 生成列表页url（是api接口）
    async def produceListUrl(self):
        for listName, listInfo in self.listUrlInfo.items():
            for page in range(int(listInfo['page'])):
                listUrl = self.baseUrl + "artlist.php?tid=" + str(listInfo['tid']) + "&start=" + str(int(page) * self.pageRows)

                # 将listUrl放到要爬取的url队列中,这个过程可能发生等待
                await self.queue.put({ "url": listUrl, "tname":listName})

    # 消费者，用于从url队列中取出url进行爬取
    async def consume(self):
        # 在开始爬取之前，先创建tcp连接池
        connector = aiohttp.TCPConnector(ssl=False, limit=self.tcpConnNum)
        async with aiohttp.ClientSession(connector=connector) as self.session:
            while True:     # 不停的从self.queue中取出task任务,task任务是我自己封装的一个字典,包含要爬取的url和其他属性
                task = await self.queue.get()  # 从自定义的asyncio队列中取出任务，这个操作可能发生等待（当队列中没有任务时，get方法会等待）

                self.sem.acquire()
                print("取出任务：" + str(task))
                if task['url'].find('images') > 0 or task['url'].find('img') > 0:  # 说明该任务是爬取图片
                    coro = self.crawlPicture(task)
                elif task['url'].find('view') > 0:  # 该url是详情页页url
                    coro = self.crawlDetailUrl(task)
                    self.crawledUrl.add(task['url'])  # 将这个详情页url设为已爬取过的url
                else:
                    coro = self.crawlListUrl(task)

                # 上面这几句只是生成一个协程对象而已,下面这句才是将协程放到任务队列中并发运行
                asyncio.create_task(coro)

    # 爬取单个url, type为1返回utf-8的编码格式，2是返回json格式，3是返回二进制格式
    async def getUrl(self, url, type=1):
        # async with self.sem:  # 信号量限制getUrl协程的个数，当并发的getUrl协程数量超过 maxCoroNum的时候，此行代码会发生等待而切换协程
        try:
            async with self.session.get(url) as resp:  # 请求url，返回resp对象内含响应内容
                if resp.status in [200, 201]:
                    if type == 1:
                        responseBody = await resp.text()
                    elif type == 2:
                        # 这里有个小坑，resp.json()方法有一个参数content_type默认为'application/json'，如果爬取到的页面的content-type和json方法的content_type参数不同就会报错（详情可以查看resp.json源码）
                        # 而我要爬的列表页的响应头的content-type是"text/html", 所以这里应该将content_type参数设置为None，即不校验 content-type
                        responseBody = await resp.json(content_type=None, encoding='utf-8')
                    else:
                        responseBody = await resp.read()
                    print("成功爬取 " + url)
                    return responseBody
                else:
                    print("响应码错误:%s | %s" % (str(resp.status), resp.url))
                    return None
        except BaseException as e:
            print("连接发生错误：", e)
            return None

    # 爬取列表页url,获取其中的详情页url
    async def crawlListUrl(self, task):
        try:
            listUrl, tname = task['url'], task['tname']
            json_data = await self.getUrl(listUrl, type=2)   # 返回的是json字典,里面包含多个详情页url的id

            for data in json_data:
                detailUrl = self.__joinUrl(data['id'], tname)       # 根据详情页id得到详情页url

                if task['url'] in self.crawledUrl:  # 判断详情页url是否已经爬取过
                    continue
                else:
                    await self.queue.put({"url" : detailUrl})     # 将详情页url放入队列待爬取
        except BaseException as e:
            print(task)
            print("出现错误: " , e)
        finally:
            self.sem.release()

    # 爬取详情页url
    async def crawlDetailUrl(self, task):
        try:
            html = await self.getUrl(task['url'])

            # 解析html中的内容,返回data字典和imgSrc列表
            data, imgSrcs = self.parseHtml(html, task['url'])     # 纯cpu操作，没有io，无需await

            await self.dbQueue.put(data)  # 添加 数据入库 任务

            # 将图片放入到url队列中，让负责下载图片的那个协程从队列取出url下载图片
            # (await self.queue.put({ "url": src, "fp":localPath}) for localPath, src in imgSrcs.items())    # 傻呀,用什么生成器表达式呀,生成器表达式定义的时候,里面的代码不会执行的!
            [await self.queue.put({ "url": src, "fp":localPath}) for localPath, src in imgSrcs.items()]
        except BaseException as e:
            print("爬取详情页发生错误： ", e)
        finally:
            self.sem.release()

    # 爬取详情页中的图片
    async def crawlPicture(self, task):
        print("爬取图片")
        print(task)
        src, localPath = task['url'], task['fp']
        localPathList = localPath.split('/')
        localPathList.pop()
        dirPath = '/'.join(localPathList)

        if not os.path.exists(dirPath):
            os.makedirs(dirPath)

        # 下载图片
        blob = await self.getUrl(src, type = 3)

        # 将图片异步写入到本地文件
        try:
            async with aiofiles.open(localPath, mode='wb') as f:
                await f.write(blob)
        except BaseException as e:
            print("图片写入本地错误:", e)
        finally:
            self.sem.release()
            f.close()

    # 数据入库任务的消费者
    async def dbConsume(self):
        while True:     # 循环取出dbQueue任务
            dbTask = await self.dbQueue.get()

            self.dbSem.acquire()
            asyncio.create_task(self.insertDb(dbTask))


    # 数据入库
    async def insertDb(self, data):
        try:
            async with self.pool.acquire() as conn:   # 从mysql连接池获取一个连接
                cursor = await conn.cursor()    # 获取光标
                # async with conn.cursor() as cursor:    # 获取光标
                data['id'] = None
                content = data.pop("content")   # 将content字段从字典中取出

                fieldNameStr = '`,`'.join(data.keys())    # 拼接字段名
                fieldNameStr = '(`' + fieldNameStr + "`)"
                fieldValueStr = '%s,' * len(data)
                fieldValueStr = "(" + fieldValueStr.strip(",") + ")"
                sqlArt = "insert ignore into article " + fieldNameStr + " values " + fieldValueStr
                sqlArtContent = 'insert into art_content (`aid`, `content`) values (%s, %s)'

                # 数据插入文章表 和 文章详情表，由于需要获取插入到文章表的id作为下次插入文章详情表的aid，所以需要把这两条插入语句作为1个原子操作
                # 可以通过加锁的方式把这两句插入语句的执行作为原子操作
                async with self.lockForSql:
                    try:
                        await cursor.execute(sqlArt, tuple(data.values()))      #数据插入文章表
                        await cursor.execute(sqlArtContent, (cursor.lastrowid, content))    # 文章内容插入文章详情表
                        print("数据入库成功: %s" % data['url'])
                    except BaseException as e:
                        print("数据插入报错")
                        print(e)
                    finally:
                        # 关闭cursor
                        await cursor.close()
        except BaseException as e:
            print("mysql 连接错误:", e)
            print("mysql连接错误对应url %s" % data['url'])
        finally:
            self.dbSem.release()

    # 拼接详情页url
    def __joinUrl(self, article_id, cate_name):
        return self.baseUrl.strip("/") + "/" + cate_name + '/' + 'view/' + str(article_id) + ".html"

    # 解析详情页html内容
    def parseHtml(self, html, detailUrl):
        soup = BeautifulSoup(html, "html.parser")
        data = {}

        data['title'] = soup.find('h1').get_text()
        artInfo = soup.find('div', class_="artinfo").find_all("span")  # 文章的发布时间，观看数和来源
        data['time'] = self.__strtotime(artInfo[0].get_text())
        data['view'] = int(artInfo[1].get_text().strip(''))
        data['source'] = artInfo[2].get_text().replace("来源：", '') if len(artInfo) > 2 else ''
        data['url'] = detailUrl
        data['tid'] = str([val['tid'] for key, val in self.listUrlInfo.items() if key in detailUrl][0])

        # content字段单独处理
        content = str(soup.find('div', class_='article'))
        data['content'], imgSrcs = self.handleContent(content)  # 该方法会将content中的图片地址获取，并将content中的<img>标签替换为图片下载后的本地路径（但是不会执行下载图片）

        return data, imgSrcs

    # 处理文章Content，搜集文章内容中的图片并返回
    def handleContent(self, content):
        # 用正则将content中的img标签都提取出来
        pattern = re.compile('<img.*?src=["\'](.*?)["\'].*?>', re.DOTALL)

        # 将内容标签变为字符串类型
        contentStr = str(content)

        # 正则替换contentStr中的图片src为下载到本地后的图片地址。并将远程图片的Src记录下来放到队列中待爬
        imgSrcs = {}  # 存放远程图片Src用于之后爬取图片
        regRes = pattern.findall(contentStr)

        for src in regRes:
            localPath = self.renamePic(src, self.picPath)
            imgSrcs[localPath] = src
            contentStr = contentStr.replace(src, localPath)
        # contentStr = pattern.sub(lambda x: (imgSrcs.append(x.group(1)), x.group(0).replace(x.group(1), self.renamePic(x.group(1))))[-1],contentStr)

        return contentStr, imgSrcs

    # 替换文章Src
    def renamePic(self, picUrl, dirPath):
        dirPath = dirPath.strip('/') + '/'  # 存放下载图片的目录路径
        m = hashlib.md5()
        m.update(picUrl.encode())
        fn = m.hexdigest()
        fn = fn[8:24] + '.jpg'

        return dirPath + fn

    def __strtotime(self, strTime):
        # 先转换为时间数组
        timeArray = time.strptime(strTime, "%Y-%m-%d %H:%M:%S")

        # 转换为时间戳
        timeStamp = int(time.mktime(timeArray))
        return timeStamp

if __name__ == "__main__":
    dbCfg = {
        "host" : "127.0.0.1",
        "port" : 3306,
        "user" : 'root',
        "password" : 'jqsf573234044',
        "db" : 'test',
        "charset" : "utf8",
        "autocommit" : True     # 自动提交事务
    }

    # 爬取3类列表页，每类列表页爬100页
    listUrlInfo = {
        'bitcoin':{'tid':10, 'page':300},
        'pme':{'tid':9, 'page':300},
        'arts':{'tid':1, 'page':300}
    }

    crawler = Crawler("https://www.fx112.com/", dbCfg, listUrlInfo, maxCoroNum = 50, tcpConnNum = 40, maxMonitorCount = 100)
    crawler.startLoop()
