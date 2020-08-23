# -*- coding: utf-8 -*-
import sys
import os

c = os.getcwd()
sys.path.append(c + '/bert')
sys.path.append(c + '/bert/bertNER')
sys.path.append(c + '/bert/bertNER/bert')
sys.path.append(c + '/bert/berNER/chinese_L-12_H-768_A-12')

import try_predict


def bert_ner(line):
    entity = try_predict.ner(line)
    print(entity)
    return entity


import ccksNeo_reverse
import jieba
import serviceWord2vec
import re
import time
import LambdaRankNNmaster.shishi20_87 as LambdaRank
# from pyltp import Segmentor, Postagger, Parser, NamedEntityRecognizer
from nltk.metrics.distance import jaccard_distance
import difflib
import config
import Levenshtein
import Attribute.similarity as si
import tensorflow as tf

lf = si.BertSim()
lf.set_mode(tf.estimator.ModeKeys.PREDICT)
model = config.w2v_model
import pickle




def simi(sentence1, sentence2):
    predict = lf.predict(sentence1, sentence2)
    # print('similarity：', {predict[0][1]})
    return predict[0][1]

def answer(line):
    index1 = line.find('|||')
    index2 = line[index1 + 4:].find('|||')
    question_id = line[:index1]
    question = line[index1 + 3: index1 + index2 + 4]


    bert_list = bert_ner(question)
    results = []
    if len(bert_list) == 1:
        discription = bert_list[0]
        results = ccksNeo_reverse.get_entity_by_discription(discription)
        temp_results = results[:]
        if results:
            for result in temp_results:
                print(result)
                relation = result[0]
                n_entity = result[1]
                simple_name = n_entity

                if '_(' in n_entity:
                    simple_name = n_entity[:n_entity.find('_(')]
                elif '_（' in n_entity:
                    simple_name = n_entity[:n_entity.find('_（')]

                print(simple_name, discription)
                if simple_name == discription:
                    results.remove(result)
            for result in results:
                relation = result[0]
                simi_score = simi(question, relation + '是' + discription)
                result.append(simi_score)
        print(results)
        daan4 = ""
        if results:
            for result in results:

                daan4 = daan4 + str(discription) + '|' + str(result[0]) + '|' + '<' + str(result[1]) + '>' + '||'

        else:
            daan4 = '哈哈哈哈|哈哈哈哈|哈哈哈哈||'

        neirong = question_id + '|||' + question + '|||' + discription + '|||' + daan4 + '|||' + '\n'
        # print(neirong)
        q = open("answer_8_16.txt", 'a', encoding="utf-8")
        q.writelines(neirong)



p = open("train_reverse.txt", 'r+', encoding="utf-8")
for line in p:
    answer(line)
