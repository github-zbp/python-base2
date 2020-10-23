# coding=utf-8

import asyncio, time

# 用asyncio.coroutine装饰器声明func函数是一个协程函数
async def func1():
    print(1)
    await asyncio.sleep(2)     # 用sleep()模拟io请求
    print(2)

async def func2():
    print(3)
    await asyncio.sleep(2)     # 用sleep()模拟io请求
    print(4)

# 封装2个协程到tasks中
tasks = [
    asyncio.ensure_future(func1()),
    asyncio.ensure_future(func2())
]
loop = asyncio.get_event_loop()     # 创建事件循环对象
loop.run_until_complete(asyncio.wait(tasks))       # 开始事件循环