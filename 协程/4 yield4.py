def actived(coro_func):
    def autoActiveCoro(*args, **kwargs):
        corotinue = coro_func()  # 返回一个协程
        next(corotinue)
        return corotinue

    return autoActiveCoro  # 返回改造后的协程函数


@actived
def averager():  # 在定义 averager 函数后自动隐式执行了 averager = actived(averager)
    total = 0
    count = 0
    average = None

    while True:
        number = yield average
        count += 1
        total += number
        average = total / count


avg = averager()  # 创建协程avg时自动激活
print(avg.send(10))
print(avg.send(20))
print(avg.send(30))
avg.close()
print(avg.send(100))