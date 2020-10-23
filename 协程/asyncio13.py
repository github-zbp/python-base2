# coding=utf-8

import asyncio


async def func(i):
    print("开始")
    await asyncio.sleep(i)
    print("结束")

    return i



loop = asyncio.get_event_loop()  # 开启事件循环必须放在create_task之前否则会报错
task_list = [loop.create_task(func(i)) for i in range(5)]   # 将任务放入任务列表中（或者说把协程放到协程池中调度）
loop.run_until_complete(asyncio.wait(task_list))  # 等待协程运行，这个方法会阻塞
