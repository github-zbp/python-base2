# coding=utf-8

import asyncio, aioredis

# 既然aioredis里面的方法都是异步非阻塞的，那么肯定要放在协程函数中运行才可以啦，所以定义一个协程函数execute()
async def execute(address):
    print("开始连接redis")
    redis = await aioredis.create_redis(address)    # 创建一个redis对象，这里会发生网络IO等待（是这个协程在等，整个线程不会去等的，肯定会切换到其他线程去运行），所以要await。此时如果事件循环的任务列表中还有其他协程就可以切换到其他协程运行，而不会干等着了。

    # 下面的读写操作都会发生网络IO，都要await
    await redis.set("a", "a")

    result = await redis.get("a")

    # 关闭连接
    redis.close()

    # 等待关闭完成
    await redis.wait_closed()

    print("结束")

task_list = [execute("127.0.0.1:6379") for i in range(5)]   # 创建5个协程
asyncio.run(asyncio.wait(task_list))    # 把这5个协程注册到事件循环中还行