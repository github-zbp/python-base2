# coding=utf-8

import asyncio


async def func(i):
    print("开始")
    await asyncio.sleep(1)
    print("结束")

    return i

# 协程完成后会自动调用该回调函数，并且传入一个future对象
def cb(future):
    print("执行回调函数，协程返回值为： %s" % future.result())

loop = asyncio.get_event_loop()  # 开启事件循环必须放在create_task之前否则会报错
task_list = [loop.create_task(func(i)) for i in range(5)]   # 将任务放入任务列表中（或者说把协程放到协程池中调度）
for task in task_list:
    task.add_done_callback(cb)    # 让协程结束后自动调用一个回调函数
loop.run_until_complete(asyncio.wait(task_list))  # 等待协程运行，这个方法会阻塞
