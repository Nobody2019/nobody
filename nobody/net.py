# coding=utf-8
"""
@Author: Liang Chao
@Email: nobody_team@outlook.com
@File: net.py
@Created: 2020/10/23 19:19
@Desc:
"""
import os
import shutil
import socket
import tempfile

import requests


def get_free_port():
    """
    获取空闲端口

    :return:
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('localhost', 0))
    try:
        return s.getsockname()[1]
    finally:
        s.close()


def get_host_ip():
    """
    获取本机IP
    """
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.connect(('8.8.8.8', 80))
        return s.getsockname()[0]


def download(url, filename=None, timeout=None, use_cache=True, headers=None):
    if not filename:
        filename = os.path.join(tempfile.gettempdir(), os.path.basename(url))
    file_dir = os.path.dirname(filename)
    if not os.path.isdir(file_dir):
        os.makedirs(file_dir)
    if os.path.exists(filename) and os.path.getsize(filename) > 0 and use_cache:
        return filename
    res = requests.get(url, stream=True, headers=headers, timeout=timeout)
    res.raise_for_status()
    file_size = int(res.headers.get("Content-Length"))
    with open(filename + '.part', 'wb') as f:
        chunk_length = 16 * 1024
        i = 0
        while 1:
            # percent = round(chunk_length * i * 100 / file_size, 2)
            # logger.info('Downloading from {} --- {}%'.format(url, min(100.0, percent)))
            buf = res.raw.read(chunk_length)
            if not buf:
                break
            f.write(buf)
            i += 1
    res.close()
    shutil.move(filename + '.part', filename)
    # logger.info('Finished!')
    return filename
