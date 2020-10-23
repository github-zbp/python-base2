# coding=utf-8

import asyncio,random,time,requests

class Reader:
    def __init__(self, n):
        self.maxcount = n
        self.count = 0

    async def readline(self):
        await asyncio.sleep(1)    # 模拟读取文本中的一行
        self.count += 1

        if self.count >= self.maxcount:
            return None

        return self.count

    def __aiter__(self):
        return self

    # __anext__ 必须是一个用async声明的协程函数
    async def __anext__(self):
        val = await self.readline()     # 凡是遇到阻塞的地方都要用 await 等待
        if val is None:
            raise StopAsyncIteration
        return val

# 由于async for必须在一个协程中运行，而不能在调用方运行，所以这里定义一个协程函数main
async def main():
    obj = Reader(10)
    async for line in obj:  # 遍历这个异步可迭代对象
        print(line)

asyncio.run(main())