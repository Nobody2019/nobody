# nobody

## otest

otest 用于面向对象的单元测试，状态驱动测试，自动跟踪状态以便灵活清理环境，用于取代传统的setup 和 teardown模式

```python
from nobody.otest import TestStatus, require_status, test


class BaseStatus(TestStatus):
    def _set_value(self, value, *args, **kwargs):
        result = kwargs.get('result')
        result.logger.info(f'{self.__class__.__name__} {value}')


class Status1(BaseStatus):
    """"""


class Status2(BaseStatus):
    """"""
    default = 'a'


class Test1:
    @require_status(Status1)
    @require_status(Status2, 'b')
    def test(self, result, *args, **kwargs):
        result.logger.info('Test1.test')


test(Test1())

```

输出：
```log
[2020-11-30 01:37:22 otest:164] [DEBUG] 开始测试：Test1, test
[2020-11-30 01:37:22 otest:170] [DEBUG] 执行测试：Test1, test
[2020-11-30 01:37:22 otest:182] [DEBUG] 设置状态：Status1 -> None
[2020-11-30 01:37:22 objects:18] [INFO] Status1 None
[2020-11-30 01:37:22 otest:182] [DEBUG] 设置状态：Status2 -> b
[2020-11-30 01:37:22 objects:18] [INFO] Status2 b
[2020-11-30 01:37:22 otest:102] [INFO] 执行测试逻辑：Test1, test
[2020-11-30 01:37:22 objects:34] [INFO] Test1.test
[2020-11-30 01:37:22 otest:63] [DEBUG] 恢复状态：Status2 -> a
[2020-11-30 01:37:22 objects:18] [INFO] Status2 a
[2020-11-30 01:37:22 otest:202] [DEBUG] 完成测试：Test1, test
```