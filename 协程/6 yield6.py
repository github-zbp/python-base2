def actived(coro_func):
    def autoActiveCoro(*args, **kwargs):
        corotinue = coro_func()
        next(corotinue)
        return corotinue

    return autoActiveCoro


@actived
def averager():
    total = 0
    count = 0
    average = None

    while True:
        number = yield      # 不产出任何值给主程序
        if number == None:  # 当主程序发送None给协程时，跳出循环
            break
        count += 1
        total += number
        average = total / count

    return average


avg = averager()  # 创建协程avg时自动激活
avg.send(10)
avg.send(20)
avg.send(30)
try:
    avg.send(None)  # 会抛出StopIteration异常
except StopIteration as e:
    print("平均值结果为：%s" % e.value)