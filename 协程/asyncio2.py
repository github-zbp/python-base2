import asyncio


# 定义一个协程函数
async def func():
    print("开始运行协程")
    print("协程运行完毕")


coro = func()  # 创建一个协程
loop = asyncio.get_event_loop()  # 获取一个事件循环对象

loop.run_until_complete(coro)  # 将协程或者任务放到“任务列表”中，并开始事件循环