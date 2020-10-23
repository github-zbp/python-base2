# coding=utf-8

from inspect import getgeneratorstate

# 计算移动平均值
def averager():
    total = 0    # 数据值总和
    count = 0    # 传进协程的数据个数
    average = None

    while True:
        number = yield average    # 用number接收主程序发送的数据
        count += 1
        total += number
        average = total/count

avg = averager()    # 返回一个协程
next(avg)           # 激活协程
print(avg.send(10))     # “10”
print(avg.send(20))     # "15"
print(avg.send(33))     # "21"
