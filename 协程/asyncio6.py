# coding=utf-8

import asyncio,random,time

def func():
    time.sleep(2)   # 模拟io操作
    return "666"

async def main():
    loop = asyncio.get_running_loop()   # 获取事件循环

    # run_in_executor方法做了两件事
    # 1.调用ThreadPoolExecutor的submit方法去线程池申请一个线程执行func函数，并返回一个concurrent.futures.Future对象
    # 2.调用asyncio.wrap_future将多线程的Future对象包装为asyncio的Future对象，因为asyncio的future对象才支持await语法
    fut = loop.run_in_executor(None, func)  # 第一参传一个线程池或进程池对象，None则默认线程池
    result = await fut    # 会阻塞等待func返回666才继续
    print(result)

asyncio.run(main())