# coding=utf-8
"""
@Author: Liang Chao
@Email: nobody_team@outlook.com
@File: image.py
@Created: 2020/10/23 10:43
@Desc:
"""
import math

import cv2
from skimage.metrics import structural_similarity as compare_similarity


def calc_similarity(src, target):
    if isinstance(src, str):
        src = cv2.imread(src)
    if isinstance(target, str):
        target = cv2.imread(target)
    src_h, src_w, _ = src.shape
    target_h, target_w, _ = target.shape
    if src_h != target_h or src_w != target_w:
        w, h = min(src_w, target_w), min(src_h, target_h)

        def resize(img, img_h, img_w):
            _h = abs(img_h - h) / 2
            _w = abs(img_w - w) / 2
            return img[math.floor(_h): img_h - math.ceil(_h), math.floor(_w):img_w - math.ceil(_w)]

        src = resize(src, src_h, src_w)
        target = resize(target, target_h, target_w)
    try:
        src = cv2.cvtColor(src, cv2.COLOR_BGR2GRAY)
        target = cv2.cvtColor(target, cv2.COLOR_BGR2GRAY)
        return compare_similarity(src, target)
    except:
        return 0
