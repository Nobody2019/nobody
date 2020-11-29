# coding=utf-8

"""
@Author: LiangChao
@Email: nobody_team@outlook.com
@File: module
@Created: 2020/6/25
@Desc: 
"""
import os
import sys


def load(filename):
    _dir = os.path.dirname(filename)
    sys.modules.pop(os.path.basename(filename).replace('.py', ''), None)  # 移除以便加载最新版本
    if _dir in sys.path:
        sys.path.remove(_dir)
    if _dir not in sys.path:
        sys.path.insert(0, _dir)
    name = os.path.basename(os.path.basename(filename)).replace('.py', '')
    module = __import__(name)
    names = dir(module)
    for name in names:
        if name.startswith('_'):
            continue
        m = getattr(module, name)
        yield name, m

