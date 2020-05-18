# coding=utf-8


class Student():
    __sum=0     # 不希望sum在类外被修改，所以设成私有类变量

    def __init__(self,name,age):
        self.name=name
        self.age=age
        self.__score=0    # score分数每个人都不同，所以不能设置为类变量
        self.__class__.__plus_sum()
        print("学生人数："+str(self.__class__.__sum))

    def log_score(self,score):
        if score<0:
            return
        self.__score=score
        print(self.name+"同学的分数是："+str(self.__score))

    @classmethod
    def __plus_sum(cls):    # 不希望plus_sum在类外被调用，而是只有实例化学生是才调用，所以设为私有类方法
        cls.__sum+=1


stu1 = Student("zbp",18)
stu1.log_score(80)
print(stu1.__dict__)        # {'name': 'zbp', 'age': 18, '_Student__score': 80}
stu1.__score=10   # 不会报错
print(stu1.__score)
