# coding=utf-8
"""
@Author: Liang Chao
@Email: nobody_team@outlook.com
@File: time.py
@Created: 2020/10/23 19:21
@Desc: 改写自 https://github.com/dbader/schedule
原Schedule必须对一个可执行对象封装，这里不关心执行什么，只提供时间上的计划
"""
from datetime import datetime, timedelta


# region Schedule

class Schedule:
    """
    Schedule support, providing the next run time, no care of what to run.
    """

    def __init__(self):
        self.interval = None  # pause interval * unit between runs
        # self.latest = None  # upper limit to the interval
        self.unit = None  # time units, e.g. 'minutes', 'hours', ...
        self.at_time = None  # optional time at which this job runs
        self.period = None  # timedelta between runs, only valid for
        self.start_day = None
        self._relative = None  # 计算下次时间的相对值

    def __lt__(self, other):
        return self.next_run < other.next_run

    def __repr__(self):
        def format_time(t):
            return t.strftime('%Y-%m-%d %H:%M:%S') if t else '[never]'

        if self.at_time is not None:
            return 'Every %s %s at %s' % (
                self.interval,
                self.unit[:-1] if self.interval == 1 else self.unit,
                self.at_time)
        else:
            fmt = (
                    'Every %(interval)s ' +
                    ('to %(latest)s ' if self.latest is not None else '') +
                    '%(unit)s'
            )

            return fmt % dict(
                interval=self.interval,
                latest=self.latest,
                unit=(self.unit[:-1] if self.interval == 1 else self.unit)
            )

    @property
    def seconds(self):
        self.unit = 'seconds'
        return self

    @property
    def minutes(self):
        self.unit = 'minutes'
        return self

    @property
    def hours(self):
        self.unit = 'hours'
        return self

    @property
    def days(self):
        self.unit = 'days'
        return self

    @property
    def weeks(self):
        self.unit = 'weeks'
        return self

    @property
    def monday(self):
        self.start_day = 'monday'
        return self.weeks

    @property
    def tuesday(self):
        self.start_day = 'tuesday'
        return self.weeks

    @property
    def wednesday(self):
        self.start_day = 'wednesday'
        return self.weeks

    @property
    def thursday(self):
        self.start_day = 'thursday'
        return self.weeks

    @property
    def friday(self):
        self.start_day = 'friday'
        return self.weeks

    @property
    def saturday(self):
        self.start_day = 'saturday'
        return self.weeks

    @property
    def sunday(self):
        self.start_day = 'sunday'
        return self.weeks

    def every(self, interval=1):
        self.interval = interval
        return self

    def at(self, year=None, month=None, day=None, hour=None, minute=None, second=None):
        self.at_time = dict(year=year, month=month, day=day, hour=hour, minute=minute, second=second, microsecond=0)
        return self

    def begin_at(self, *args, **kwargs):
        if args and isinstance(args[0], datetime):
            self._relative = args[0]

        return self

    def to(self, latest):
        self.latest = latest
        return self

    @property
    def next_run(self):
        """
        Compute the instant when this job should run next.

        """
        if self.unit and self.interval:
            self.period = timedelta(**{self.unit: self.interval})
            if not self._relative:
                self._relative = datetime.now()
            next_run = self._relative + self.period
            if self.start_day is not None:
                if self.unit != 'weeks':
                    raise ScheduleValueError('`unit` should be \'weeks\'')
                weekdays = (
                    'monday',
                    'tuesday',
                    'wednesday',
                    'thursday',
                    'friday',
                    'saturday',
                    'sunday'
                )
                if self.start_day not in weekdays:
                    raise ScheduleValueError('Invalid start day')
                weekday = weekdays.index(self.start_day)
                days_ahead = weekday - next_run.weekday()
                if days_ahead <= 0:  # Target day already happened this week
                    days_ahead += 7
                next_run += timedelta(days_ahead) - self.period
        else:
            next_run = datetime.now()
        if self.at_time is not None:
            kwargs = {k: v for k, v in self.at_time.items() if v is not None}
            next_run = next_run.replace(**kwargs)

        return next_run

    def get_during(self, start, end):
        """
        获取起止日期范围内的日程时间

        :param start:
        :param end:
        :return:
        """

    def __next__(self):
        next_run = self.next_run
        self._relative = next_run
        return next_run


class ScheduleError(Exception):
    """Base schedule exception"""


class ScheduleValueError(ScheduleError):
    """"""


def every(interval):
    return Schedule().every(interval)


def at_time(*args, **kwargs):
    if args and isinstance(args[0], datetime):
        return Schedule().at(args[0])
    else:
        return Schedule().at(datetime(*args, **kwargs))

# endregion
