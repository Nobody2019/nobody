# coding=utf-8
"""
@Author: Liang Chao
@Email: nobody_team@outlook.com
@File: schedule.py
@Created: 2020/10/30 18:25
@Desc:
"""


def every(interval=1):
    pass


class Schedule:
    def __init__(self):
        self._next_time = None
        self._interval = None
        self._unit = None
        self._relative_time = None

    def at(self, dt):
        self._next_time = dt

    def next_time(self):
        return self._next_time

    def every(self, interval):
        self._interval = interval

    def years(self):
        self._unit = 'years'
        return self

    def months(self):
        self._unit = 'months'
        return self
