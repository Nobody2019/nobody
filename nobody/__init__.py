# coding=utf-8
"""
@Author: Liang Chao
@Email: nobody_team@outlook.com
@File: __init__.py.py
@Created: 2020/10/23 9:36
@Desc:
"""


def get(o, attr, default=None):
    """
    获取对象属性值，作用类似于C#语法 o?.attr

    :param o:
    :param attr:
    :param default:
    :return:
    """
    return getattr(o, attr, default) if o else default
