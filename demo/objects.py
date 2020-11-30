# coding=utf-8

"""
@Author: LiangChao
@Email: nobody_team@outlook.com
@File: objects
@Created: 2020/11/29
@Desc: 
"""
from nobody.otest import TestStatus, require_status, test


class BaseStatus(TestStatus):
    def _set_value(self, value, *args, **kwargs):
        result = kwargs.get('result')
        result.logger.info(f'{self.__class__.__name__} {value}')


class Status1(BaseStatus):
    """"""
    default = 2


class Status2(BaseStatus):
    """"""
    default = 'a'


class Test1:
    @require_status(Status1, 2)
    @require_status(Status2, 'b')
    def test(self, result, *args, **kwargs):
        result.logger.info('Test1.test')


test(Test1())
