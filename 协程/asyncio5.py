# coding=utf-8

import asyncio,random,time

# 需要传入一个future对象作为参数
async def set_after(fut):
    await asyncio.sleep(2)
    fut.set_result("666")       # 在一个协程完成之后，在future对象中设置结果

async def main():
    # 获取当前事件循环
    loop = asyncio.get_running_loop()

    # 创建一个空的Future对象
    fut = loop.create_future()

    await asyncio.create_task(set_after(fut))

    result = await fut      # 得到666

    print(result)

asyncio.run(main())

