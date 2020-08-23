#!/usr/bin/env python
# -*- coding: utf-8 -*-

import config
import jieba

print ("Loading model:word2vec ......")
model = config.w2v_model


# 获取两个单词列表的相似度
def get_similarity(seg_list, word_list):

    ws1 = []
    ws2 = []
    point = 0

    for word in seg_list:
        if word in model:
            ws1.append(word)
    for word in word_list:
        if word in model:
            ws2.append(word)
    if len(ws1) > 0 and len(ws2) > 0:
        point = model.n_similarity(ws1, ws2)
    print(ws1, ws2, point)
    return point


