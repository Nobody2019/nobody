# coding=utf-8
"""
@Author: Liang Chao
@Email: nobody_team@outlook.com
@File: design_pattern.py
@Created: 2020/10/23 19:25
@Desc:
"""

import threading

from tsrunner.utils.thread import synchronized


def singleton(cls):
    instances = {}

    @synchronized
    def get_instance(*args, **kw):
        if cls not in instances:
            instances[cls] = cls(*args, **kw)
        return instances[cls]

    return get_instance


# class SingletonType(type):
#     _instance_lock = threading.Lock()
#
#     def __call__(cls, *args, **kwargs):
#         if not hasattr(cls, "_instance"):
#             with SingletonType._instance_lock:
#                 if not hasattr(cls, "_instance"):
#                     cls._instance = super(SingletonType, cls).__call__(*args, **kwargs)
#         return cls._instance


class SingletonType(type):
    # _instance_lock = threading.Lock()

    def __call__(cls, *args, **kwargs):
        if not hasattr(cls, "_instance"):
            cls._instance = super(SingletonType, cls).__call__(*args, **kwargs)
        return cls._instance


class Singleton:
    __instance = None

    def __new__(cls, *args, **kwargs):
        """"""
        if not cls.__instance:
            cls.__instance = object.__new__(cls)
        return cls.__instance
