# coding=utf-8
"""
@Author: Liang Chao
@Email: nobody_team@outlook.com
@File: otest.py
@Created: 2020/11/27 11:04
@Desc:
"""
import threading
import traceback
from collections import namedtuple
from functools import wraps
from types import FunctionType
from typing import List

from nobody.builtin import get_target_py
from nobody.design_pattern import singleton
from nobody.log import logger, setup_logger

# region 核心定义

_Test = namedtuple('Test', ('o', 'fn'))


class TestStatus:
    """测试状态"""
    name = None
    default = None
    choices = []

    def __init__(self):
        self._value = None  # 当前值
        self.initial_value = None  # 初始值，它不一定是默认值
        self._prev_value = None
        self._listeners = []

    @property
    def value(self):
        return self._value

    @property
    def changed(self):
        return self._value is not None and (self.initial_value or self.default) != self._value

    def set_value(self, value, *args, **kwargs):
        if self.choices and value not in self.choices:
            raise NotSupportedStatusError(value)
        self._set_value(value, *args, **kwargs)
        self._prev_value, self._value = self._value, value
        if self.changed:
            for listener in self._listeners:
                listener.on_status_changed(self, self._prev_value, self._value, *args, **kwargs)  # 触发app状态改变事件

    def _set_value(self, value, *args, **kwargs):
        raise NotImplementedError

    def reset(self, *args, **kwargs):
        if not self.changed:
            return False
        value = self.initial_value or self.default
        if value is not None:
            result = kwargs.get('result')
            result.logger.debug(f'恢复状态：{self.name or self.__class__.__name__} -> {value}')
            self._set_value(value, *args, **kwargs)
            return True
        return False

    def add_listener(self, listener):
        self._listeners.append(listener)
        return self

    def remove_listener(self, listener):
        self._listeners.remove(listener)
        return self


# endregion

# region 装饰器

def require_status(status: TestStatus, value=None):
    """状态依赖"""
    if isinstance(status, type):
        status = status()

    def deco(o):
        if isinstance(o, type) and not isinstance(o, FunctionType):
            ctx = context.get_or_create_context(o)

            @wraps(o)
            def wrapper(*args, **kwargs):
                return o(*args, **kwargs)
        else:
            @wraps(o)
            def wrapper(*args, **kwargs):
                c = context.get_or_create_context(wrapper)
                if c.result:
                    c.result.set_status(status, value, *args, **kwargs)
                else:
                    status.set_value(value, *args, **kwargs)
                if not hasattr(o, '__wrapped__'):
                    c.result.logger.info(f'执行测试逻辑：{c.result.test_name}')
                return o(*args, **kwargs)

            ctx = context.get_or_create_context(wrapper)
        ctx.status_dependencies.append((status, value))
        return wrapper

    return deco


# endregion

# region 执行

class _StatusFailRecord:
    def __init__(self, status, value, o, fn):
        self.status = status
        self.value = value
        self.test = _Test(o, fn)


class _TestResult:
    """测试结果"""

    def __init__(self, o, fn, log_file=None, **kwargs):
        self.o = o
        self.fn = fn
        self._listeners: List[TestListener] = []
        self._status_fail_records = []  # 状态设置失败记录
        self.__test_name = f'{self.o.__class__.__name__}, {self.fn}'
        self.logger = setup_logger(log_file or f'[{self.o.__class__.__name__}][{self.fn}].log')

    @property
    def fn(self):
        return self._fn

    @fn.setter
    def fn(self, value):
        self._fn = value
        if isinstance(self._fn, FunctionType):
            setattr(self._fn, 'result', self)

    @property
    def test_name(self):
        return self.__test_name

    def add_listener(self, listener):
        self._listeners.append(listener)

    def remove_listener(self, listener):
        if listener and isinstance(listener, str):  # 按名称移除，使远端管理成为可能
            for item in self._listeners:
                if item.name == listener:
                    self._listeners.remove(item)
                    return
        self._listeners.remove(listener)

    def on_create_result(self, *args, **kwargs):
        pass

    def start(self, *args, **kwargs):
        """"""
        self.logger.debug(f'开始测试：{self.__test_name}')
        for listener in self._listeners:
            listener.on_start(self, *args, **kwargs)

    def run_fn(self, *args, **kwargs):
        try:
            self.logger.debug(f'执行测试：{self.__test_name}')
            self.fn(*args, **kwargs)
            for listener in self._listeners:
                listener.on_test_passed(self, *args, **kwargs)
        except:
            logger.debug(traceback.format_exc())
            for listener in self._listeners:
                listener.on_test_failed(self, *args, **kwargs)

    def set_status(self, status, value, *args, **kwargs):
        """"""
        try:
            self.logger.debug(f'设置状态：{status.name or status.__class__.__name__} -> {value}')
            status.set_value(value, *args, **kwargs)
        except:
            logger.debug(traceback.format_exc())
            for listener in self._listeners:
                listener.on_test_blocked(self, *args, **kwargs)
            # 检查之前的测试里面哪个没擦好屁股
            for record in self._status_fail_records:
                if record.status == status:
                    pass  # TODO 记录擦屁股失败

    def reset_status(self, status, *args, **kwargs):
        """"""
        try:
            status.reset(*args, **kwargs)
        except:
            self._status_fail_records.append(_StatusFailRecord(status, None, self.o, self.fn))

    def finish(self, *args, **kwargs):
        """"""
        self.logger.debug(f'完成测试：{self.__test_name}')
        for listener in self._listeners:
            listener.on_finished(self, *args, **kwargs)


class TestListener:
    name = None

    def on_status_changed(self, status, prev, cur, *args, **kwargs):
        """"""

    def on_start(self, result, *args, **kwargs):
        pass

    def on_test_start(self, fn, *args, **kwargs):
        """"""

    def on_test_passed(self, fn, *args, **kwargs):
        """"""

    def on_test_failed(self, fn, *args, **kwargs):
        """"""

    def on_test_blocked(self, fn, *args, **kwargs):
        """"""

    def on_test_finished(self, fn, *args, **kwargs):
        """"""

    def on_test_error(self, fn, *args, **kwargs):
        """"""

    def on_cleanup_failed(self, fn, *args, **kwargs):
        """"""

    def on_finished(self, result, *args, **kwargs):
        pass


def test(o=None, fn='test', *args, **kwargs):
    """"""
    if isinstance(fn, list):
        for _fn in fn:
            test(o, _fn, *args, **kwargs)
        return
    kwargs['result'] = result = _TestResult(o, fn, **kwargs)
    result.start(*args, **kwargs)
    if o:
        o_ctx = context.get_or_create_context(o.__class__)
        if o_ctx:
            for status, value in o_ctx.status_dependencies:
                result.set_status(status, value, *args, **kwargs)
    if fn:
        _fn = fn
        if o and isinstance(fn, str):
            _fn = getattr(o, fn)
        else:
            assert callable(fn)
            _fn = fn
        if o and isinstance(fn, str):
            fn_ctx = context.get_or_create_context(getattr(o.__class__, fn))
        else:
            fn_ctx = context.get_or_create_context(_fn)
        fn_ctx.result = result

        result.fn = _fn
        result.run_fn(*args, **kwargs)
        for status, value in fn_ctx.status_dependencies:
            result.reset_status(status, *args, **kwargs)
    if o:
        o_ctx = context.get_or_create_context(o.__class__)
        if o_ctx:
            for status, value in o_ctx.status_dependencies:
                result.reset_status(status, *args, **kwargs)

    result.finish(*args, **kwargs)


# endregion

# region Context

class _ObjectContext:
    """"""

    def __init__(self, o=None):
        self.status_dependencies: List[TestStatus] = []
        self.o = o
        self.result = None


@singleton
class _ContextManager:
    """上下文管理器"""

    def __init__(self):
        self._contexts = {}

    def get_or_create_context(self, o):
        """为被测对象创建上下文"""
        key = f'{id(_get_wrapped_fn(o))}-{id(threading.currentThread())}'
        if key not in self._contexts:
            ctx = _ObjectContext(o)
            self._contexts[key] = ctx
        return self._contexts[key]


context = _ContextManager()


# endregion

# region Errors


class TestError(Exception):
    """"""


class TestNotFoundError(TestError):
    """"""


class NotSupportedStatusError(TestError):
    """"""


class TestBlockedError(TestError):
    """"""


class TestFailedError(TestError):
    """"""

    def __init__(self, *args, optional=False):
        self.optional = optional
        super().__init__(*args)


class TestSkippedError(TestError):
    """"""


# endregion


# region Utils

def _get_wrapped_fn(fn):
    temp = fn
    while hasattr(temp, '__wrapped__'):
        _id = id(temp)
        temp = getattr(temp, '__wrapped__')
        if id(temp) == _id:
            break

    return temp

# endregion
