# coding=utf-8

import asyncio, aiohttp, aiomysql
from asyncio import Queue

class Crawler:
    def __init__(self, baseUrl, dbCfg):
        self.baseUrl = baseUrl
        self.queue = Queue(maxsize=2000)     # 队列，用于放要爬取的url，长度为2000
        self.dbCfg = dbCfg

    # 爬取单个url
    async def getUrl(url):
        pass

    # 生成列表页url（是api接口）
    async def produceListUrl(self):
        pass

    # 爬取列表页url,获取其中的详情页url
    async def crawlListUrl(self):
        pass

    # 爬取详情页url
    async def crawlDetailUrl(self):
        pass

    # 爬取详情页中的图片
    async def crawlPicture(self):
        pass


    # 主协程
    async def start(self, loop):
        # 创建mysql连接池
        self.pool = await aiomysql.create_pool(loop=loop, **self.dbCfg)

        # 开启 生成列表页url 和 爬取列表页url 这两个协程，将他们加入到任务列表中开始执行
        asyncio.create_task(produceListUrl())
        pass

if __name__ == "__main__":
    dbCfg = {
        "host" : "127.0.0.1",
        "port" : 3306,
        "user" : 'root',
        "password" : 'jqsf573234044',
        "db" : 'test',
        "charset" : "utf8"
    }

