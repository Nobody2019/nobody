# coding=utf-8
"""
@Author: Liang Chao
@Email: nobody_team@outlook.com
@File: gitlab.py
@Created: 2020/8/4 17:15
@Desc:
"""
import re
from urllib.parse import urlencode

import requests
from requests import HTTPError

# Actions
from tsrunner.utils.log import logger
from tsrunner.utils.o import get

_LIST = 0
_GET = 1
_ADD = 2
_EDIT = 3
_DELETE = 4


class _API:
    url = ''
    actions = []
    required_params = []

    def __init__(self, parent: '_API', **kwargs):
        self._id = None
        self._base_url = parent._base_url + self.url if parent else None
        self._headers = parent._headers if parent else {}
        self._url_args = parent._url_args if parent else {}
        self._url_args.update(**kwargs)
        self._requests_kwargs = parent._requests_kwargs if parent else {}
        self._convert_dates_enabled = True
        self._session = parent._session if parent else {}
        self._parent = parent
        self._branch = get(parent, '_branch', 'master')

    def _get(self, api_url, addl_keys=None, data=None, _headers=False):
        return self._request('get', api_url, addl_keys, data, _headers=_headers)

    def _post(self, api_url, addl_keys=None, data=None):
        return self._request('post', api_url, addl_keys, data)

    def _put(self, api_url, addl_keys=None, data=None):
        return self._request('put', api_url, addl_keys, data)

    def _delete(self, api_url, addl_keys=None, data=None):
        return self._request('delete', api_url, addl_keys, data)

    def _request(self, request_fn, api_url, addl_keys, data, _headers=False):
        url = self._get_url(api_url, self._url_args)
        # print "%s %s, data=%s" % (request_fn.__name__.upper(), url, str(data))
        self._session = self._session or requests.Session()
        if request_fn in ['get', 'head'] and data:
            url = url + '?' + urlencode(data, doseq=True)
            data = None
        url = url[:-1] if url.endswith('?') else url
        if not isinstance(self, GitLab):
            url = url + ('&' if '?' in url else '?') + 'ref=' + self._branch
        logger.debug(url)
        resp = self._session.request(method=request_fn, url=url, headers=self._headers, data=data,
                                     **self._requests_kwargs)
        resp.raise_for_status()
        return resp.json()

    def _get_url(self, api_url, addl_keys=None):
        keys = self._get_keys(addl_keys)
        # Handle annoying case of CurrentUser (wherein we have more keys
        # than we need) by stripping away excess keys...
        api_url = self._base_url + api_url
        num_url_keys = len(re.findall(r':[^/]+', api_url))
        keys = keys[-num_url_keys:]
        for key in keys:
            api_url = api_url.replace(':' + key, str(addl_keys[key]))
        return api_url

    def _get_keys(self, addl_keys=None):
        ret = [*addl_keys] if addl_keys else []
        api = self
        while api and api._id:
            ret.append(api._id)
            api = api._parent
        ret.reverse()  # Need to modify this later so no reversed()
        return ret


class GitLab(_API):
    def __init__(self, host, token=None, convert_dates=True, ssl_verify=True, ssl_cert=None):
        super().__init__(parent=None)
        self._base_url = f"{host.rstrip('/')}/api/v3"
        self._requests_kwargs = dict(verify=ssl_verify, cert=ssl_cert)
        self._headers = {'PRIVATE-TOKEN': token}
        self._convert_dates_enabled = convert_dates

    def login(self, username, password):
        data = {'password': password}
        if '@' in username:
            data['email'] = username
        else:
            data['login'] = username
        try:
            ret = self._post('/session', data=data)
        except HTTPError:
            return False
        headers = {'PRIVATE-TOKEN': ret['private_token']}
        self._headers = headers
        return True

    def projects(self, page=1, per_page=10):
        """
        获取所有项目

        :return:
        """
        return self._get('/projects', data=dict(page=page, per_page=per_page))

    def project(self, id):
        return _Project(parent=self, id=id)


class _Project(_API):
    url = '/projects/:id'

    def __init__(self, parent, id):
        super().__init__(parent, id=id)

    def branch(self, name):
        """
        分支

        :param name:
        :return:
        """
        self._branch = name
        return self

    def files(self, path=None):
        if path:
            path = path.replace('/', '%2F').replace('.', '%2E')
        url = f'/repository/tree{"" if not path else "?path=" + path}'
        return [_File(parent=self, **item) for item in self._get(url)]


class _Team(_API):
    def __init__(self, parent, name):
        super().__init__(parent)
        self.name = name


class Group(_API):
    url = '/groups/:id'
    actions = [_LIST, _GET, _ADD, _DELETE]
    required_params = [
        'name',
        'path',
    ]


class _User(_API):
    url = '/user'

    def __init__(self, parent):
        super().__init__(parent)


class _File(_API):
    # url = '/repository/tree'

    def __init__(self, parent, path=None, **kwargs):
        super().__init__(parent)
        self._info = kwargs  # 文件信息
        if parent and isinstance(parent, _File):
            self.parent = parent.parent
            self.path = '/'.join([parent.path, path]) if path else parent.path
        else:
            self.parent = parent
            self.path = path

    @property
    def info(self):
        """
        文件信息

        :return:
        """
        return self._info

    @property
    def is_folder(self):
        """
        是否文件夹

        :return:
        """
        return self._info.get('type') == 'tree'

    @property
    def is_file(self):
        return self._info.get('type') == 'blob'

    def delete(self):
        pass

    def create(self):
        self._post(self.path)

    def update(self):
        pass

    def get_info(self):
        return self._get('/repository/files/' + self.path)

    def list_all(self):
        """
        列出目录下所有文件

        :return:
        """
        if self.is_folder:
            return [_File(parent=self, **item) for item in self._get('/repository/tree?path=' + self.path)]
        return []

    def __repr__(self):
        return f'File (name={self._info.get("name")}, is_folder={self.is_folder})'


class SSHKey(_API):
    url = '/keys/:id'


class _Member(_API):
    url = '/members/:user_id'
    actions = [_LIST, _GET, _ADD, _DELETE]
    required_params = [
        'title',
        'key',
    ]


gl = GitLab('https://192.168.67.107:18600/', ssl_verify=False)
b = gl.login('liangchao0510', 'ThunderSoft@88')
files = gl.project(390).files(path='sony_project')
for f in files:
    if f.is_file:
        info = f.get_info()
        pass
s = gl.project(390).files('sony_project')
pass
