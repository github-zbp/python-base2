# coding=utf-8

import asyncio,random,time

# 协程函数：请求一个页面
async def request_url(url):
    print("请求url %s" % url)
    await asyncio.sleep(1)      # 模拟io请求
    print("完成请求 %s" % url)

    if url.find("detail") == -1:    # 如果这个url是一个列表页则获取详情页链接
        detail_urls = ["%s/detail%s" % (url, str(random.randint(1,100))) for i in range(5)]
        return detail_urls
    else:   # 如果url不是列表页则直接返回html内容
        return url + "的html内容"

# 协程函数：爬取一个列表页下所有详情页内容
async def crawl(list_url):
    print("start crawl")

    detail_urls = await request_url(list_url)

    for detail_url in detail_urls:
        detail_html = await request_url(detail_url)
        print("详情页内容： %s" % detail_html)

st = time.time()
asyncio.run(crawl("/list1"))
print("用时: %.5f" % (time.time() - st))		# 用时: 6.04015