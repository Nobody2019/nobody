# coding=utf-8
"""
@Author: Liang Chao
@Email: nobody_team@outlook.com
@File: md.py
@Created: 2020/10/27 17:36
@Desc: Markdown文件支持
"""


class MDWriter:
    """
    用于写md文件
    """

    def __init__(self):
        pass

    def table(self):
        class _Table:
            def __enter__(self):
                pass

            def __aenter__(self):
                pass

            def write_head(self, *args):
                pass

            def write_line(self, *args):
                pass
        return _Table()

    def title(self, title, level=3):
        pass

    def write_text(self, text):
        pass

    def line(self):
        pass

    def ref(self, content):
        pass

    def list(self, content):
        pass

    def image(self, name, uri):
        pass

    def link(self, text, link):
        pass

    def convert_pdf(self):
        pass

    def convert_html(self):
        pass
