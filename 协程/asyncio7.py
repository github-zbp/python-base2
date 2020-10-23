# coding=utf-8

import asyncio,random,time,requests

# 爬一个url就开一个协程
async def getUrl(url):
    result = requests.get(url)

    print(result.text)

urls = [
    "https://www.zbpblog.com/",
    "https://www.zbpblog.com/blog-196.html",
    "https://www.zbpblog.com/blog-195.html",
    "https://www.zbpblog.com/blog-194.html",
]

# 创建协程
task_list = [getUrl(url) for url in urls]

# 创建事件循环
loop = asyncio.get_event_loop()

# 将协程放入任务列表中监控
loop.run_until_complete(asyncio.wait(task_list))