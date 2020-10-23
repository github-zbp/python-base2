# coding=utf-8

from inspect import getgeneratorstate

# 创建一个协程函数
def simple_coro2(a):
    print("协程开始运行, 传入a：%s" % str(a))
    b = yield a
    print("协程接收到数据b：%s" % str(b))
    c = yield a + b
    print("协程接收到数据c：%s" % str(c))

coro2 = simple_coro2(10)    # 返回一个协程

print(getgeneratorstate(coro2))     # 获取协程状态

print(next(coro2))      # 10

print(getgeneratorstate(coro2))     # 此时一定是暂停状态而不是运行状态，因为能回到主程序执行代码说明子程序已经经历了暂停和切换。要时刻记得这是个单线程而不是多线程

print(coro2.send(20))   # 返回30

coro2.send(100)     # “协程接收到数据c：100”