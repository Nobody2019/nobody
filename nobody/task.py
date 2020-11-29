# coding=utf-8

"""
@Author: LiangChao
@Email: nobody_team@outlook.com
@File: task
@Created: 2020/9/5
@Desc: 
"""
import itertools
import os
import threading
import time
import traceback
import uuid
from collections import namedtuple
from concurrent.futures.thread import ThreadPoolExecutor
from datetime import datetime
from functools import wraps
from queue import Queue
from typing import Optional, List, Dict

from tsrunner.error import BaseError
from tsrunner.utils.log import logger
from tsrunner.utils.schedule import Schedule
from tsrunner.utils.thread import thread

RUNNING = 'running'  # 执行中
TERMINATED = 'terminated'  # 终止
PAUSED = 'paused'  # 暂停
FINISHED = 'finished'  # 已完成
CANCELED = 'canceled'  # 已取消

TaskItem = namedtuple('TaskItem', ('task', 'args', 'kwargs'))


def pausable(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        obj = args[0]
        if hasattr(obj, 'task_handler') and obj.task_handler:
            obj.task_handler.wait()
        return func(*args, **kwargs)

    return wrapper


class _TaskHandler(object):
    """
    任务控制器
    """

    def __init__(self):
        self._thread_event = threading.Event()
        self._thread_event.set()
        self._force_stop = False
        self._stop_reason = None
        self._pause_timeout = None

    def wait(self, timeout=None):
        if self._force_stop:
            raise TaskTerminatedError(self._stop_reason)
        self._thread_event.wait(timeout or self._pause_timeout)

    def pause(self, timeout=None):
        """
        暂停执行

        :return:
        """
        self._pause_timeout = timeout
        self._thread_event.clear()

    def resume(self):
        """
        恢复执行

        :return:
        """
        self._thread_event.set()

    def stop(self):
        pass

    def force_stop(self, reason=None):
        """
        强行停止

        :return:
        """
        self._force_stop = True
        self._stop_reason = reason

    def handle(self, target, *args, **kwargs):
        obj = target(*args, **kwargs) if isinstance(target, type) else target
        setattr(obj, 'task_handler', self)
        return obj


class _Task:
    def __init__(self, target, *args, **kwargs):
        self.id = str(uuid.uuid4())
        self.task_handler = _TaskHandler()
        self.parent: Optional[_Task] = None  # 父任务
        self.subs: List[_Task] = []  # 子任务
        self.future = None
        self.begin_time = None
        self.finish_time = None
        self.schedule: Optional[Schedule] = None
        self._status = None
        self._target = target
        self._args = args
        self._kwargs = kwargs
        self.__sub_finish_count = 0
        self._listeners = []
        self.__subs_paused = False

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, value):
        self._status = value
        for listener in self._listeners:
            if not isinstance(listener, TaskListener):
                continue
            method = getattr(listener, f'on_status_changed')
            if method:
                method(task=self, status=value)
        if value == FINISHED and self.parent:
            self.parent._sub_finish(sub=self)

        logger.debug(f'task {value}: {self.id}')

    @property
    def cost(self):
        """
        耗时

        :return:
        """
        if self.begin_time:
            return ((self.finish_time or datetime.now()) - self.begin_time).total_seconds()
        else:
            raise TaskError("Task does not start!")

    @property
    def ready(self):
        """
        是否就绪

        :return:
        """
        if self.schedule:
            return self.schedule.next_run <= datetime.now()
        else:
            return True

    def run(self):
        if self.status:
            return
        if not self.ready:
            raise TaskNotReadyError(self.id)
        self.status = RUNNING
        try:
            self._target(*self._args, **self._kwargs)
            self.status = FINISHED
        except TaskTerminatedError:
            self.status = TERMINATED
        except:
            logger.error(traceback.format_exc())
            raise

    def add_sub(self, sub):
        self.subs.append(sub)
        sub.parent = self
        # sub.task_handler = self.task_handler
        return self

    def pause(self, timeout=None, include_subs=True):
        """
        暂停任务

        :param timeout:
        :param include_subs: 是否包含子任务
        :return:
        """
        if self.status != RUNNING:
            return False
        if include_subs:
            for sub in self.subs:
                sub.pause(timeout)
            self.__subs_paused = True
        self.task_handler.pause(timeout)
        self.status = PAUSED
        return True

    def resume(self, *args, **kwargs):
        if self.status != PAUSED:
            return False
        if self.__subs_paused:
            for sub in self.subs:
                sub.resume()
        logger.debug(f'唤醒任务：{self.id}')
        self.task_handler.resume()
        for listener in self._listeners:
            listener.on_resumed(self, *args, **kwargs)
        return True

    def stop(self, reason=None, *args, **kwargs):
        """
        终止任务

        :param reason:
        :return:
        """
        assert self.status == RUNNING, f'只能终止执行中的任务！'
        self.task_handler.force_stop(reason)
        self.status = TERMINATED
        for listener in self._listeners:
            listener.on_stop(self, *args, **kwargs)

    def cancel(self):
        """
        取消任务

        :return:
        """
        if self.future:
            if not self.future.cancel():
                return False
        if not self.status:
            self.status = CANCELED
            return True
        return self.status == CANCELED

    def wait(self, timeout=None):
        self.task_handler.wait(timeout)

    def wait_sub_finished(self):
        """
        等待子任务完成

        :return:
        """
        logger.debug('等待子任务完成')
        self.pause(include_subs=False)
        self.task_handler.wait()

    def _sub_finish(self, sub):
        for listener in self._listeners:
            listener.on_sub_finished(task=self, sub=sub)
        self.__sub_finish_count += 1
        if self.__sub_finish_count >= len(self.subs) and self._status == PAUSED:
            logger.debug(f'{self.__sub_finish_count}')
            self.task_handler.resume()
            # self.__sub_finish_count = 0

    def add_listener(self, listener):
        """
        添加任务监听器

        :param listener:
        :return:
        """
        self._listeners.append(listener)


class TaskPoolExecutor(ThreadPoolExecutor):
    """
    任务池执行器
    """
    _counter = itertools.count().__next__

    def __init__(self, max_workers=None, thread_name_prefix=''):
        super().__init__(max_workers, thread_name_prefix)

    @property
    def max_workers(self):
        return self._max_workers or (os.cpu_count() or 1) * 5

    def submit(self, fn, *args, **kwargs):
        pass


class __TaskService(object):
    def __init__(self):
        self._tasks: Dict[str, _Task] = {}
        self._queue = Queue()
        self._max_workers = None
        self._task_executor = ThreadPoolExecutor()
        self._working = False
        self._stopping_self = False
        self.daemon = True
        self.stop_self_timeout = 600
        self._self_stop_thread = None

    @property
    def working(self):
        return self._working

    @property
    def tasks(self):
        return self._tasks.keys()

    @property
    def max_workers(self):
        return self._max_workers or (os.cpu_count() or 1) * 5

    def get_task(self, task_id):
        """
        获取任务

        :param task_id:
        :return:
        """
        return self._tasks.get(task_id).task

    def submit(self, target, *args, **kwargs):
        task = _Task(target, *args, **kwargs)
        self._tasks[task.id] = task
        # try:
        #     setattr(target, '__task', task)
        # except:
        #     pass
        if not self.working:
            self.start()
        return task

    def pause_task(self, task_id, timeout=None):
        """
        暂停任务

        :param task_id:
        :param timeout:
        :return:
        """
        task: _Task = self._tasks.get(task_id)
        if task:
            task.pause(timeout)
        else:
            raise TaskNotFoundError(task_id)

    def resume_task(self, task_id):
        """
        恢复任务

        :param task_id:
        :return:
        """
        task: _Task = self._tasks.get(task_id)
        if task:
            task.resume()
        else:
            raise TaskNotFoundError(task_id)

    def stop_task(self, task_id, reason):
        """
        终止任务

        :param task_id:
        :param reason:
        :return:
        """
        task: _Task = self._tasks.get(task_id)
        if task:
            task.stop(reason)
        else:
            raise TaskNotFoundError(task_id)

    def cancel_task(self, task_id):
        """
        取消任务

        :param task_id:
        :return:
        """
        task: _Task = self._tasks.get(task_id)
        if task:
            task.cancel()
            task.stop()
        else:
            raise TaskNotFoundError(task_id)

    def start(self):
        def callback(f):
            task_id = getattr(f, 'task_id')
            self._tasks[task_id].status = FINISHED
            self.has_unfinished_tasks()

        @thread(name='任务池', daemon=self.daemon)
        def _work():
            while self._working:
                for task in self.__get_ready_tasks():
                    future = self._task_executor.submit(task.run)
                    task.future = future
                    setattr(future, 'task_id', task.id)
                    future.add_done_callback(callback)
                time.sleep(1)

        self._working = True
        _work()

    def stop(self):
        self._working = False

    def stop_self(self):
        """
        线程自停逻辑，即10分钟内没有新任务，会停止

        :return:
        """

        class _StopSelfThread(threading.Thread):
            def __init__(self, service):
                super().__init__()
                self._event = threading.Event()
                self._event.set()
                self.service = service
                self.daemon = True

            def run(self) -> None:
                self._event.clear()
                self._event.wait(self.service.stop_self_timeout)
                if not self.service.has_unfinished_tasks():
                    self.service._working = False
                self.service._stopping_self = False

            def resume(self):
                self._event.set()

        if not self._stopping_self:
            self._stopping_self = True
            logger.debug('任务池自停')
            self._self_stop_thread = _StopSelfThread(self)
            self._self_stop_thread.start()

    def __get_ready_tasks(self):
        task_items = list(self._tasks.values())
        for task in task_items:
            if task.ready and not task.status:
                yield task

    def has_unfinished_tasks(self):
        for task_id, task in self._tasks.items():
            if task.status != FINISHED:
                return True
        self.stop_self()
        return False


class TaskListener:
    """
    任务监听器
    """

    def on_start(self, task, *args, **kwargs):
        pass

    def on_status_changed(self, task, status, *args, **kwargs):
        pass

    def on_paused(self, task, *args, **kwargs):
        pass

    def on_terminated(self, task, *args, **kwargs):
        pass

    def on_canceled(self, task, *args, **kwargs):
        pass

    def on_resumed(self, task, *args, **kwargs):
        pass

    def on_sub_finished(self, task, sub, *args, **kwargs):
        pass

    def on_finished(self, task, *args, **kwargs):
        pass


class TaskError(BaseError):
    """
    任务异常
    """


class TaskTerminatedError(TaskError):
    """

    """


class TaskNotReadyError(TaskError):
    """

    """


class TaskNotFoundError(TaskError):
    """

    """


task_service = __TaskService()
