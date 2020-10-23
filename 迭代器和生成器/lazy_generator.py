# coding=utf-8

# 基于生成器实现的可迭代对象,懒加载,节省内存

class Sentence:     # 这是一个可迭代对象的类
    def __init__(self, sentence):
        self.sentence = sentence

    # 直接将 __iter__ 方法定义成一个生成器函数
    def __iter__(self):
        start_index = 0
        last_space_pos = 0
        while True:
            space_pos = self.sentence.find(" ", start_index)
            if space_pos != -1:
                yield self.sentence[start_index:space_pos]
                start_index = space_pos + 1
            else:
                yield self.sentence[start_index:]
                break
        return

# 无需定义一个迭代器类

sentence = Sentence("I am so handsome so that I have no friend")    # 返回一个可迭代对象

for word in sentence:
    print(word)