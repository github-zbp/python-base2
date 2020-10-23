# coding=utf-8

import asyncio,random,time,requests

class AsyncContextManager:
    async def __aenter__(self):
        # 做数据库连接的操作
        # self.conn = await 数据库连接()    # 连接这个行为必须是异步的才行
        await asyncio.sleep(1)      # 用睡眠模拟连接的过程
        pass

    async def do_something(self):
        # 操作数据库
        await asyncio.sleep(1)
        return 666

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()       # 这个close方法也必须是异步非阻塞的才行


async def func():
    async with AsyncContextManager() as f:
        result = await f.do_something()  # 这里必须要await
        print(result)


asyncio.run(func())