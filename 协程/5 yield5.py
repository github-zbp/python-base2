from sys import maxsize

# 为做实验而自定义的异常
class DemoException(Exception):
    pass

# 定义自动激活装饰器
def actived(func):
    def autoActivedCoro(*args, **kwargs):
        coro = func(*args, **kwargs)
        res = next(coro)        # res是0，由协程yiled产出
        return coro

    return autoActivedCoro

# 传入n限定产出的次数
@actived
def coro_exec_demo(n = None):
    n = n if n else maxsize

    for i in range(n):
        try:
            recv_data = yield i
        except DemoException as e:
            print("yield处发生异常")
        else:
            print("接收到数据 %s " % str(recv_data))

    print("协程结束")

coro = coro_exec_demo(3)    # 创建协程并自动激活，限定yield 3次，自动激活已经yield 1次了
print(coro.send(100))       # yield 产出 1
# print(coro.throw(DemoException))     # 向协程发送一个普通异常，throw直接接收到yield 2
print(coro.throw(ZeroDivisionError))     # 向协程发送一个普通异常，throw直接接收到yield 2
# print(coro.close())
print(coro.send(200))       # 协程最终跳出循环，抛出 StopIteration

