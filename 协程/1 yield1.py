# coding=utf-8

# 创建一个协程函数（协程的生成器函数，我把它叫做协程函数，但它不是协程）
def simple_coroutine():
    print("开始协程")
    x = yield
    print("接收到数据x为: " + str(x))

coro = simple_coroutine()       # 实例化一个协程（其实就是个生成器）
output = next(coro)             # 调用next()开始子程序代码的运行，并将yield产出的值赋给output
print("协程产出了", output)       # None
coro.send(100)                  # 主程序向子程序发送数据