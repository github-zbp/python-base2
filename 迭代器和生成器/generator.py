# coding=utf-8

# 基于生成器实现的可迭代对象

class Sentence:     # 这是一个可迭代对象的类
    def __init__(self, sentence):
        self.sentence = sentence
        self.words = self.sentence.split()

    # 直接将 __iter__ 方法定义成一个生成器函数
    def __iter__(self):
        for word in self.words:
            yield word

        return

# 无需定义一个迭代器类

sentence = Sentence("I am so handsome so that I have no friend")    # 返回一个可迭代对象

for word in sentence:
    print(word)

for word in sentence:
    print(word)