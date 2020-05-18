import abc


class Person(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def work(self, job):
        pass


class Student(Person):
    pass


class Engineer(Person):
    def work(self, job):  # 还是没有实现work方法
        pass


class Police(Person):
    def work(self, job):
        print("We are Police.My primary job is to " + job)


stu = Student()     # 马上报错
# engineer = Engineer()  # 也会报错
police = Police()
police.work("catch bad guy")