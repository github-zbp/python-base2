# coding=utf-8

# 基于迭代器实现的可迭代对象

# 这个Sentence类的作用很简单，能遍历句子中的每个单词即可
class Sentence:     # 这是一个可迭代对象的类
    def __init__(self, sentence):
        self.sentence = sentence
        self.words = self.sentence.split()

    def __iter__(self):
        return SentenceIterator(self.words)

class SentenceIterator:     # 这是一个迭代器类
    def __init__(self, words):
        self.words = words
        self.index = 0

    def __iter__(self):
        return self

    def __next__(self):     # __next__不接受其他参数
        try:
            word = self.words[self.index]
            self.index += 1
            return word
        except:
            self.index = 0
            raise StopIteration

st = "I am so handsome so that I have no friend"    # 我太帅了以至于我没有朋友
sentence = Sentence(st)    # 返回一个可迭代对象

for word in sentence:
    print(word)

for word in sentence:
    print(word)