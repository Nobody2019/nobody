# coding=utf-8

"""
@Author: LiangChao
@Email: nobody_team@outlook.com
@File: decorators
@Created: 2020/6/10
@Desc: 
"""
import threading
import time
import traceback
from functools import wraps

from nobody.log import logger


def ignore_errors(*errors):
    """
    忽略指定异常，不指定则忽略所有异常

    :param errors:
    :return:
    """
    errors = errors or Exception

    def deco(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except errors:
                logger.debug(traceback.format_exc())

        return wrapper

    return deco


def timeout(seconds, interval=0.5, errors=None):
    def decorator(func):
        @wraps(func)
        def inner(*args, **kwargs):
            deadline = time.time() + seconds
            _e = None
            while time.time() < deadline:
                try:
                    return func(*args, **kwargs)
                except errors or Exception as e:
                    _e = e
                if interval:
                    time.sleep(interval)
            raise _e

        return inner

    return decorator


def during(seconds, interval=None):
    """
    使被装饰的方法反复执行一段时间，除非原方法抛出异常，否则不会提前终止

    :param seconds:
    :param interval:
    :return:
    """

    def decorator(func):
        @wraps(func)
        def inner(*args, **kwargs):
            deadline = time.time() + seconds
            while time.time() < deadline:
                func(*args, **kwargs)
                if interval:
                    time.sleep(interval)

        return inner

    return decorator


def condition(check):
    """
    条件装饰器，接收一个条件检查器，接收到的参数与被修饰的方法一样

    :param check:
    :return:
    """
    if not callable(check):
        raise Exception('条件装饰器只能接收 callable 对象作为参数！')

    def deco(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if check(*args, **kwargs):
                return func(*args, **kwargs)

        return wrapper

    return deco


def thread(name=None, daemon=True):
    def deco(func):
        @wraps(func)
        def inner(*args, **kwargs):
            threading.Thread(name=name, target=func, args=args, kwargs=kwargs, daemon=daemon).start()
            if name:
                logger.debug(f'开启线程：{name}')

        return inner

    return deco


def synchronized(func):
    func.__lock__ = threading.Lock()

    def synced_func(*args, **kws):
        with func.__lock__:
            return func(*args, **kws)

    return synced_func
