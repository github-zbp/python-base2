#coding=utf-8

# chain函数可以传入多个可迭代对象，并将这些可迭代对象中的元素统一产出
def chain(*iterables):
    for iterable in iterables:
        for item in iterable:
            yield item

# 使用yield from改进chain函数
def improved_chain(*iterables):
    for iterable in iterables:
        yield from iterable

a_list = [1,2,3]
a_dict = {"a":"A", "b":"B"}
a_tuple = (8,9,0)

for i in chain(a_list, a_dict, a_tuple):
    print(i)

for i in improved_chain(a_list, a_dict, a_tuple):
    print(i)