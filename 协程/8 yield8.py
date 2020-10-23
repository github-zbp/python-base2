# coding=utf-8

# 子生成器函数（协程函数）
def averager():
    count = 0
    total = 0
    average = None

    while True:
        number = yield      # 只接收数据，不产出数据
        if number == None:  # 如果发送过来的数据为None则跳出循环终止协程
            break
        total += number
        count += 1
        average = total / count

    return count, average

# 委派生成器函数, 需要传入一个全局的results保存求得的平均值结果
def grouper(key):
    while True:
        results[key] = yield from averager()        # while每循环一次，都会创建一个新的averager子生成器（averager协程）


# 调用方，用于驱动协程的运行
def main():
    for key, d in data.items():
        print("用于计算 %s 的协程创建" % key)
        group = grouper(key)        # 返回一个委派生成器，其实是一个协程
        next(group)                 # 激活group协程， grouper内部会在运行到yield from averager()时创建一个averager协程然后暂停
        for item in d:
            group.send(item)        # 向group协程发送数据，grouper内部会把item数据转发给averager协程

        # 发送完一组数据的所有项时，通知average协程终止
        group.send(None)
        print("用于计算 %s 的协程终止" % key)

    print("所有计算结束，计算结果如下：", results)



# 学生身高体重数据
data = {
	"boy_weight": [130,125,135,160,120,170,149],
	"boy_height": [166,170,190,185,179,168,172],
	"girl_weight": [100,97,88,120,140,102,90,89,112],
	"girl_height": [160,165,155,170,174,167,157,149,170]
}

# results用于记录结果
results = {}

if __name__ == "__main__":
    main()
    # print(results)