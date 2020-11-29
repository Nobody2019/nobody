# coding=utf-8
"""
@Author: Liang Chao
@Email: nobody_team@outlook.com
@File: builtin_ext.py
@Created: 2020/10/29 9:35
@Desc:
"""
import fnmatch
import json
import os
import re
import shutil
import sys
from datetime import datetime
from typing import Union
from uuid import UUID

from lxml import etree


def cvt_bool(value):
    if isinstance(value, bool):
        return value
    return True if value.lower() == 'true' else False


class Int(int):
    """"""

    def __init__(self, *args, **kwargs):
        super().__init__()


class Str(str):
    def __new__(cls, o, *args, **kwargs):  # 重写 __new__ 否则无法正常重写 __init__
        return super().__new__(cls, o)

    def ints(self):
        _list = re.compile(r'\d+').findall(self)
        return [int(n) for n in _list]

    def uncamel(self):
        """
        变量名风格转换：驼峰 --> 下划线
        """
        s1 = re.sub('([A-Z][a-z]+)(?=[A-Z]]?)', r'\1_', self)
        return s1.lower()

    def camel(self):
        """
        变量名风格转换：下划线 --> 驼峰
        """
        s1 = ''.join([s.title() if s else '_' for s in self.split('_')])
        return s1

    def startswith_any(self, prefixes: Union[list, tuple]):
        for prefix in prefixes:
            if self.startswith(prefix):
                return True
        return False

    def endswith_any(self, suffixes: Union[list, tuple]):
        for suffix in suffixes:
            if self.endswith(suffix):
                return True
        return False

    def sep(self, n=1):
        """
        生成器，用于将字符串按照指定数量分组

        list(sep('123456', 8)) >> ['123456']

        list(sep('13465782345', 4)) >> ['1346', '5782', '345']

        :param n:
        :return:
        """
        length = len(self)
        for i in range(0, length, n):
            if i > 0:
                yield self[i - n: i]
        yield self[length - (length % n or 4):]

    def path(self, relpath):
        return Path.abspath(relpath, self)

    def is_ip_address(self):
        m = re.match(r'.*(?:(?:\d+)\.){3}\d+(?::\d+)?.*', self)
        return m is not None


class Version(str):
    pattern = re.compile(r'^(?P<major>\d+)\.'
                         r'(?P<minor>\d+)\.'
                         r'(?P<patch>\d+)$')

    def __init__(self, o):
        if o is None:
            raise VersionError('Require version str value!')
        super().__init__()
        self.parts = {}

    def apply_pattern(self, pattern=None):
        pattern = re.compile(pattern) if isinstance(pattern, str) else pattern
        pattern = pattern or self.pattern
        self.parts = pattern.search(self).groupdict({})
        return self

    def __getattr__(self, item):
        return self.parts.get(item)

    def __int__(self):
        return int(''.join(re.compile(r'\d+').findall(self)))

    def __gt__(self, other):
        return int(self) > int(other)

    def __lt__(self, other):
        return int(self) < int(other)


class VersionError(Exception):
    """

    """


class Path(str):
    @property
    def basename(self):
        return os.path.basename(self)

    @property
    def size(self):
        return os.path.getsize(self)

    @property
    def create_time(self):
        return datetime.fromtimestamp(os.path.getctime(self))

    @property
    def mod_time(self):
        return datetime.fromtimestamp(os.path.getmtime(self))

    @property
    def last_access_time(self):
        return datetime.fromtimestamp(os.path.getatime(self))

    @property
    def isfile(self):
        return os.path.isfile(self)

    @property
    def isdir(self):
        return os.path.isdir(self)

    @property
    def ismount(self):
        """是否盘符"""
        return os.path.ismount(self)

    @property
    def parent(self):
        return self.__class__(os.path.dirname(self)) if not self.ismount else None

    @property
    def exists(self):
        return os.path.exists(self)

    @property
    def nodes(self):
        """将路径拆分成节点列表"""
        return re.split(r'[\\/]', self)

    def info(self, related: str = None):
        info = dict(name=self.basename,
                    path=self,
                    size=self.size,
                    create_time=self.create_time,
                    mod_time=self.mod_time,
                    last_access_time=self.last_access_time)
        if self.isfile:
            info['size'] = self.size
            info['type'] = 'file'
        else:
            info['type'] = 'dir'
        if related:
            related = related.strip(os.sep)
            info['relative_path'] = self.replace(related, '')
        return info

    def search(self, pattern):
        if not pattern:
            raise PathError('Pattern for searching is required!')
        for item in self.list():
            if item.isfile and fnmatch.fnmatch(item.basename, pattern):
                yield item
            if item.isdir:
                for f in item.search(pattern):
                    yield f

    def list(self, pattern=None):
        for item in os.listdir(self):
            if pattern is None or (pattern and fnmatch.fnmatch(item, pattern)):
                yield Path(os.path.join(self, item))

    def files(self, pattern=None):
        for item in self.list(pattern):
            if item.isfile:
                yield item

    def dirs(self, pattern=None):
        for item in self.list(pattern):
            if item.isdir:
                yield item

    def upstream_search(self, pattern):
        if not pattern:
            raise PathError('Pattern for searching is required!')
        if self.isfile:
            for f in self.parent.upstream_search(pattern):
                yield f
        else:
            for f in self.list(pattern):
                yield f
            if self.parent:
                for f in self.parent.upstream_search(pattern):
                    yield f

    def open(self):
        if self.isfile:
            return open(self)
        else:
            raise PathError('Can not open a dir!')

    def copy(self, dest):
        if self.isfile:
            shutil.copy(self, dest)
        else:
            shutil.copytree(self, dest)

    def move(self, dest, overwrite=False):
        """

        :param dest:
        :param overwrite:
        :return:
        """
        _dest = Path(dest)
        if _dest.isfile and _dest.basename != self.basename:
            dest = os.path.dirname(dest)
        try:
            shutil.move(self, dest)
            return True
        except shutil.Error as e:
            if 'already exists' in str(e) and overwrite:
                os.remove(os.path.join(dest, self.basename))
                return self.move(dest)
            return False

    def delete(self):
        if not self.exists:
            return
        if self.isfile:
            os.remove(self)
        else:
            os.removedirs(self)

    def rename(self, new):
        """
        Rename a file or a directory.

        :param new: new name
        :return:
        """
        shutil.move(self, os.path.join(self.parent, new))

    @staticmethod
    def abspath(rel_path: str, base_dir=None):
        if os.path.isabs(rel_path):
            return rel_path
        if not base_dir:
            try:
                raise Exception
            except Exception:
                frame_str = str(sys.exc_info()[2].tb_frame.f_back)
                base_dir = os.path.normpath(re.findall(r'(?<=file \')(.+)(?=\', line)', frame_str)[0])
        if os.path.isfile(base_dir):
            base_dir = os.path.dirname(base_dir)
        cur_dir_parts = base_dir.split(os.sep)
        parts = re.split(r'[\\/]', rel_path)
        for part in parts:
            if part == '':
                parts = parts[1:]
            elif part == '..':
                cur_dir_parts = cur_dir_parts[:-1]
                parts = parts[1:]
            elif part == '.':
                parts = parts[1:]
            else:
                cur_dir_parts.extend([part])
        return Path(os.sep.join(cur_dir_parts))

    def join(self, *paths):
        result = None
        for path in paths:
            result = result / path if result else path
        return result

    def __truediv__(self, other):
        return self.__class__(os.path.join(self, other))


class PathError(Exception):
    """

    """


class Dict(dict):
    def __setattr__(self, key, value):
        self[key] = value

    def __getattr__(self, item):
        return self.get(item)

    @staticmethod
    def load_xml(file):
        tree = etree.parse(file)
        root = tree.getroot()
        result = Dict(**root.attrib)

        def convert_ele(ele, d):
            for sub in ele:
                tag = sub.tag.lower()
                count = len(ele.xpath(f'//{sub.tag}'))
                sd = Dict(**sub.attrib)
                _list = []
                if count > 1:
                    _list.append(sd)
                    setattr(d, tag + '_list', sd)
                else:
                    setattr(d, tag, sd)
                convert_ele(sub, sd)

        convert_ele(root, result)
        return result

    def to_query_str(self):
        """
        将字典转换为查询字符串

        :return:
        """
        return '&'.join([k + '=' + str(v) for k, v in self.items()])

    @staticmethod
    def from_query_str(query_str):
        query_str = query_str + '&'
        p = re.compile(r'[^=&]+=[^=]+(?=&)')
        _list = p.findall(query_str)
        d = Dict()
        for item in _list:
            _arr = item.split('=', maxsplit=1)
            d[_arr[0]] = _arr[1]
        return d


class List(list):
    def remove(self, *args):
        for arg in args:
            if arg in self:
                super().remove(arg)
        return self

    def prepend(self, *args, dup=True):
        """在列表头部添加元素"""
        for arg in args:
            if arg in self and not dup:
                continue
            self.insert(0, arg)
        return self

    def append(self, *args, dup=True):
        for arg in args:
            if arg in self and not dup:
                continue
            super().append(arg)
        return self

    def extend(self, *args, dup=True):
        return self.append(*args, dup=dup)


class Json:
    """
    Json数据包装器，可以用来处理 dict 或 list，包装之后可以像类实例对象一样访问属性
    """

    def __init__(self, data):
        self.__data = data

    @property
    def data(self):
        return self.__data

    def items(self):
        if isinstance(self.__data, dict):
            return self.__data.items()
        else:
            return self.__data

    def from_xml(self, file):
        """从XML文件中读取"""

    def from_json(self, file):
        """从json文件中读取"""
        self.__data = json.load(open(file, 'r', encoding='utf-8'))

    def __getattr__(self, name):
        return self.__getitem__(name)

    def __getitem__(self, item):
        if isinstance(item, int) and isinstance(self.__data, list):
            return Json(self.__data[item])
        elif isinstance(item, (str, tuple)) and isinstance(self.__data, dict):
            v = self.__data.get(item)
            if isinstance(v, (dict, list)):
                return Json(v)
            else:
                return v
        return None

    def __str__(self):
        return str(self.__data)


class Py(Path):
    def __init__(self, o):
        if not o or not isinstance(o, str):
            raise TypeError('Only allow str with value!')
        if not self.exists:
            raise FileNotFoundError(o)
        super().__init__()
        self.__module = None

    @property
    def module(self):
        if not self.__module:
            self.load()
            self.__module = __import__(self.basename[:-3])
        return self.__module

    def load(self):
        _dir = self
        if self.isfile:
            _dir = self.parent
            sys.modules.pop(self.basename, None)
        else:
            sys.modules.pop(_dir, None)  # 移除以便加载最新版本
        if _dir in sys.path:
            sys.path.remove(_dir)
        if _dir not in sys.path:
            sys.path.insert(0, _dir)
        return self

    def unload(self):
        _dir = self.parent if self.isfile else self
        sys.path.remove(_dir)

    def list_module(self):
        for name in dir(self.module):
            value = getattr(self.module, name)
            yield self.module, name, value

    def __getattr__(self, item):
        self.load()
        module = __import__(os.path.basename(self)[:-3])
        if item not in dir(module):
            raise AttributeError(item)
        return getattr(module, item)

    def load_pytest(self):
        setup_class, setup, tests, teardown, teardown_class = None, None, [], None, None
        for m, name, value in self.list_module():
            if name.startswith('_'):
                continue
            if name == 'setup':
                setup = value
            elif name == 'cleanup':
                teardown = value
            elif name.startswith('test_'):
                tests.append(m)
            elif name == 'setup_class':
                setup_class = value
        return setup_class, setup, tests, teardown, teardown_class


def serialize(o, private=False, protected=False):
    if isinstance(o, (str, int, float, bool)):
        return o
    elif isinstance(o, (datetime, UUID)):
        return str(o)
    elif isinstance(o, list):
        return [serialize(item, private, protected) for item in o]
    d = dict(cls=o.__class__)
    for name in dir(o):
        value = getattr(o, name)
        if callable(value):
            continue
        if name.startswith('__') and name.endswith('__'):
            continue
        is_private = name.startswith(f'_{o.__class__.__name__}')
        if not private and is_private:
            continue
        if not protected and name.startswith('_') and not is_private:
            continue
        d[name] = serialize(value, private, protected)
    return d


def deserialize(value):
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        cls = value.get('cls')
        instance = cls()
        value.pop('cls', None)
        for k, v in value.items():
            setattr(instance, k, deserialize(v))
        return instance


def get_target_py():
    try:
        raise Exception
    except Exception:
        exec_info = sys.exc_info()
        f_back = sys.exc_info()[2].tb_frame.f_back.f_back
        lineno = f_back.f_lineno
        method = f_back.f_code.co_name
        filename = f_back.f_code.co_filename.replace('\\', '/')
        return filename, method if method != '<module>' else None, lineno


# region 装饰器：typecheck

class TypeCheck:
    def __init__(self, arg, arg_type):
        self.arg = arg
        self.arg_type = arg_type

    def __get__(self, instance, cls):
        if instance is None:
            return self
        return instance.__dict__[self.arg]

    def __set__(self, instance, value):
        if isinstance(value, self.arg_type):
            instance.__dict__[self.arg] = value
        else:
            raise TypeError('{} should be {}'.format(value, self.arg_type))


# 装饰器自身是一个函数
def typecheck(**kwargs):
    def dec(cls):
        def wraps(*args):
            for name, required_type in kwargs.items():
                setattr(cls, name, TypeCheck(name, required_type))
            return cls(*args)  # 这里是实例化新的Person类后返回实例对象，也就是p

        return wraps

    return dec

# endregion
