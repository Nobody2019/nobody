# coding=utf-8
"""
@Author: Liang Chao
@Email: nobody_team@outlook.com
@File: check.py
@Created: 2020/9/4 18:14
@Desc:
"""
import re
from typing import Union


class Check:
    def __init__(self, target):
        self._target = target

    def contains_any(self, values: Union[list, tuple, str]):
        if isinstance(values, str):
            values = [values]
        for item in values:
            if item in self._target:
                return True
        return False

    def contains_all(self, values: Union[list, tuple, str]):
        if isinstance(values, str):
            values = [values]
        for item in values:
            if item not in self._target:
                return False
        return True

    def test(self, **kwargs):
        """
        检查对象是否满足条件

        :param kwargs:
        :return:
        """
        for k, v in kwargs.items():
            attr, method = tuple(k.split('__')) if '__' in k else (k, None)
            if isinstance(self._target, dict):
                value = self._target.get(attr)
            else:
                value = getattr(self._target, attr)
            if method and method.startswith('not_'):
                no = True
                method = method[4:]
            else:
                no = False
            if method and method.startswith('i'):
                if isinstance(value, str):
                    value = value.lower()
                v = v.lower()
                method = method[1:]
            if value is None:
                if method == 'is_none':
                    return True
                else:
                    return False
            if not method:
                if value != v:
                    return False
            elif method == 'in':
                if (value not in v and not no) or (value in v and no):
                    return False
            elif method == 'contains':
                if (v not in value and not no) or (v in value and no):
                    return False
            elif method == 'startswith':
                if (not value.startswith(v) and not no) or (value.startswith(v) and no):
                    return False
            elif method == 'endswith':
                if (not value.endswith(v) and not no) or (value.endswith(v) and no):
                    return False
            elif method == 'contains_any':
                if (not Check(value).contains_any(v) and not no) or (Check(value).contains_any(v) and no):
                    return False
            elif method == 'matches':
                if (not re.match(re.compile(v), value) and not no) or (re.match(re.compile(v), value) and no):
                    return False
            elif method == 'type':
                if (not isinstance(value, v) and not no) or (isinstance(value, v) and no):
                    return False
            elif method == 'lt':
                return value < v
        return True
