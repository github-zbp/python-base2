# coding=utf-8

import asyncio

async def func(i):
    print("开始")
    await asyncio.sleep(1)
    print("结束")

    return i

loop = asyncio.get_event_loop()     # 开启事件循环必须放在create_task之前否则会报错
task_list = [loop.create_task(func(i)) for i in range(5)]
loop.run_until_complete(asyncio.wait(task_list))    # 这个方法会阻塞

print(123)

for task in task_list:
    print(task.result())    # 获取协程的返回值,这个方法会阻塞，直到协程return了才会被唤醒