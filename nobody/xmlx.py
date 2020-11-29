# coding=utf-8
"""
@Author: Liang Chao
@Email: nobody_team@outlook.com
@File: xmlx.py
@Created: 2020/11/17 17:30
@Desc: 扩展lxml
"""
import re

from lxml import etree

from nobody.builtin import Dict, Str


class Xml(Str):
    @property
    def etree(self):
        # xml 不能包含encoding='utf-8'，lxml不支持
        return etree.fromstring(re.sub(r"(encoding='.+')", '', self))

    def sub(self, xpath):
        """获取xpath指向的节点内容"""
        nodes = self.etree.xpath(xpath)
        if nodes:
            return etree.tostring(nodes[0], method='html')

    def one(self, xpath):
        """查找满足的第一个节点"""
        nodes = self.etree.xpath(xpath)
        if nodes:
            return _Node(**nodes[0].attrib)

    def all(self, xpath):
        """查找所有满足条件的节点"""
        return [_Node(**item.attrib) for item in self.etree.xpath(xpath)]


class _Node(Dict):
    """"""
