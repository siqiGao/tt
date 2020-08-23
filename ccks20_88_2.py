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


import ccksNeo
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

mention2entity_dic = pickle.load(open('mention2entity_dic_2020.pkl', 'rb'))


def simi(sentence1, sentence2):
    predict = lf.predict(sentence1, sentence2)
    # print('similarity：', {predict[0][1]})
    return predict[0][1]


# 指称识别
def segmentsentence(sentence):
    segmentor = Segmentor()
    postagger = Postagger()
    parser = Parser()
    recognizer = NamedEntityRecognizer()

    segmentor.load("./ltpdata/ltp_data_v3.4.0/cws.model")
    postagger.load("./ltpdata/ltp_data_v3.4.0/pos.model")
    # parser.load("./ltpdata/ltp_data_v3.4.0/parser.model")
    recognizer.load("./ltpdata/ltp_data_v3.4.0/ner.model")
    #############
    word_list = segmentor.segment(sentence)
    postags_list = postagger.postag(word_list)
    nertags = recognizer.recognize(word_list, postags_list)
    ############
    for word, ntag in zip(word_list, nertags):
        if ntag == 'Nh':
            entity_list.append(word)
    print(" ".join(word_list))
    print(' '.join(nertags))
    ############
    segmentor.release()
    postagger.release()
    # parser.release()
    recognizer.release()
    return word_list


def entityRecognize(word_list, question):
    entity_list = []
    for word in word_list:
        entity = ""
        finalentity = ""
        for temp_entity in word_list[word_list.index(word):]:
            entity = entity + temp_entity
            all_entity = [entity]
            if len(entity) > 1:
                # print(entity)
                # print(1)
                if entity in mention2entity_dic:  # 如果它有对应的实体
                    for alias in mention2entity_dic[entity]:
                        all_entity.append(alias)
                for en in all_entity:
                    same_name_entity_list = ccksNeo.get_entity_list_by_name(en)
                    extra_name = ccksNeo.get_entity_info_by_name(en)
                    for name in extra_name:
                        if name[0][-1] == '名' or name[0][-1] == '称':
                            if len(name[1]) > 1:
                                if name[0] != '英文名' and name[0] != '英文名称' and name[0] != '外文名' and name[0] != '外文名称':
                                    entity_list.append(name[1])
                    if len(same_name_entity_list) >= 1:
                        entity_list.append(en)
    # print(list(set(entity_list)))
    for entity1 in entity_list:  # 如果短的指称被长的指称包含，检测短指称的一度关系名
        temp = question
        for i in entity1:
            if i in question:
                temp = temp.replace(i, "")
        # temp_list = sentence.replace(entity1, "")
        # segmentor1 = Segmentor()
        # segmentor1.load("./ltpdata/ltp_data_v3.4.0/cws.model")
        # temp_list = segmentor1.segment(temp)
        # segmentor1.release()
        for entity2 in entity_list:
            if entity1 != entity2 and entity1 in entity2:
                # print(2)
                same_name_entity_list = ccksNeo.get_entity_list_by_name(entity1)
                flag = 0
                for entitydict in same_name_entity_list:
                    # print(entitydict, "用id查")
                    # print(3)
                    relations = ccksNeo.get_related_entities_by_id(entitydict['id'])
                    # print(relations)
                    for relation in relations:  # 除掉实体的剩余句子
                        score = serviceWord2vec.get_similarity(list(jieba.cut(temp)), list(jieba.cut(relation['name'])))
                        if score > 0.2:
                            flag = 1
                if flag == 0 and entity1 in entity_list:
                    # print(entity_list)
                    # print(entity1)
                    entity_list.remove(entity1)

    print("entity_list", entity_list)
    # time.sleep(10)

    return entity_list


# 实体链接
def entityLink(entity_list, question):  # (通过实体名找到数据库中的各实体并通过评分策略找到中心实体)
    scores = []
    allentity_info = []
    for name in entity_list:
        simple_name = name
        if '_(' in name:
            simple_name = name[:name.find('_(')]
        elif '_（' in name:
            simple_name = name[:name.find('_（')]
        # print(4)

        name_simi_score = serviceWord2vec.get_similarity(list(jieba.cut(question)), list(jieba.cut(simple_name)))
        entity_total = ccksNeo.get_entity_list_by_name(name)  # 指称的所有实体
        # print(entity_total)
        in_question_word = 0
        temp = question
        for j in simple_name:
            if j in question:
                temp = temp.replace(j, "")
                in_question_word = in_question_word + 1

        temp = question
        for i in simple_name:
            if i in question:
                temp = temp.replace(i, "")
        # print("temp", temp)
        temp0 = temp
        # temp = question.replace(name, "")  # 去掉指称的剩余句子

        # print(temp)   #剩余句子分词

        for entity in entity_total:
            relation_list = []
            entity_Id = entity['id']
            # print(5)
            relations = ccksNeo.get_related_entities_by_id(entity['id'])
            # print(relations)
            max_relation_score = 0
            relation_in_question = 0
            for relation in relations:  # 不同的关系，可能有类别相同的关系
                relation_list.append(relation['name'])
                score = serviceWord2vec.get_similarity(list(jieba.cut(temp0)),
                                                       list(jieba.cut(relation['name'])))  # 只要实体关系和句子沾边
                if score > max_relation_score:
                    max_relation_score = score
                if relation['name'] in temp0:
                    relation_in_question = 1
            link_relation_num = len(relation_list)
            # relation_list_type = set(relation_list)
            # link_relation_type_num = len(relation_list_type)

            # print(question)
            if "《" + simple_name + "》" in question or "\"" + simple_name + "\"" in question or "“" + simple_name + "”" in question:
                be_included = 1
            else:
                be_included = 0
            relative_position = question.find(simple_name) / len(question)
            have_quesition_word = 0
            # question_word_num = 0
            min_distance = 100
            for question_word in question_words:
                if question_word in question:
                    have_quesition_word = 1
                    # question_word_num = question_word_num+1
                    if min_distance > abs(question.find(question_word) - question.find(simple_name)):
                        min_distance = abs(question.find(question_word) - question.find(simple_name))
            have_alpha_or_digit = 0
            pattern1 = re.compile('[0-9]+')
            pattern2 = re.compile('[a-z]+')
            pattern3 = re.compile('[A-Z]+')
            match1 = pattern1.findall(simple_name)
            match2 = pattern2.findall(simple_name)
            match3 = pattern3.findall(simple_name)
            if match1 or match2 or match3:
                have_alpha_or_digit = 1
            entity_length = len(simple_name)

            if simple_name in question:
                name_in_question = 1
            else:
                name_in_question = 0

            levenshtein_score = Levenshtein.distance(simple_name, question)
            '''
            if name == c_name:
                is_correct_name =1
            else:
                is_correct_name =0


            if entity['keyId'] == c_keyid:
                is_correct_entity = 1
            else:
                is_correct_entity = 0

            print(q_id, entity_keyId, one_relation, link_relation_num, link_relation_type_num, be_included, relative_position, have_quesition_word, min_distance,
                  have_alpha_or_digit, entity_length, is_correct_entity)

            sentence = q_id+'  '+entity_keyId+'  '+str(one_relation)+'  '+str(link_relation_num)+'  '+str(link_relation_type_num)+'  '+str(be_included)+'  '+str(relative_position)+'  '+str(have_quesition_word)+'  '+str(min_distance)+'  '+str(have_alpha_or_digit)+'  '+str(entity_length)+'  '+str(is_correct_entity)+'\n'
            p = open("../NLPCC_KBQA/nlpcc-iccpol-2016.kbqa.training-data_processtry2.txt", 'a', encoding="utf-8")
            p.writelines(sentence)
            p.close()
            '''
            entity_info = [name, entity_Id, name_simi_score, in_question_word, max_relation_score,
                           relation_in_question,
                           link_relation_num, be_included, relative_position, have_quesition_word, min_distance,
                           have_alpha_or_digit, entity_length, name_in_question, levenshtein_score]

            allentity_info.append(entity_info)

    print(allentity_info)
    # time.sleep(10)

    return allentity_info
    '''
        frequency = len(entity_total)  #实体频率
        allentity = allentity + entity_total

    relation = []
    for entitydict in entity_total:
        relations = ccksNeo.get_related_entities_by_id(entitydict['neoId'])
        print(relations)
        for relationname in relations:
            relation.append(relationname['name'])
    set(relation)
    relationfrequency = len(relation)
    print(frequency, relationfrequency)
    score = frequency + relationfrequency
    scores.append(score)
'''


def entity_sort(entity_info):  # 返回得分最大的两个实体id。[name, entity_Id, one_relation, link_relation_num,
    # link_relation_type_num, be_included, relative_position, have_quesition_word, min_distance,have_alpha_or_digit, entity_length]
    result = []
    print("entity_info", entity_info)
    if len(entity_info) == 1:  # 返回name和keyid
        result = entity_info[:2]
        return result
    else:
        result = []
        flag = 0
        entity_scores = LambdaRank.lambdarank(entity_info, flag)
        print(entity_scores)
        temp_score = list(set(entity_scores))
        a = sorted(temp_score, key=lambda x: x * 1000 if x < 0 else x, reverse=True)
        print(a)
        if len(a) >= 5:
            m = 5
        else:
            m = len(a)
        for j in range(0, m):
            res = [idx for idx, i in enumerate(entity_scores) if i == a[j]]
            for i in res:
                # print(i)
                temp = []
                temp = entity_info[i][:2]
                result.append(temp)
        print(result)
        # time.sleep(10)
        return result
        '''
        print(a)
        res = [idx for idx, i in enumerate(entity_scores) if i == a[0]]
        print(res)
        for i in res:
            print(i)
            temp = []
            temp = entity_info[i][:2]
            result.append(temp)

        res = [idx for idx, i in enumerate(entity_scores) if i == a[1]]
        for j in res:
            print(j)
            temp = []
            temp = entity_info[j][:2]
            result.append(temp)
        return result
        '''


##########################################
def get_realtion_info(relation_candidate, question):  # [name, relation, target_entity, target_entity_keyid]
    # temp_relations = ccksNeo.get_entity_info_by_keyid(entity_keyid)  #该实体的信息
    # 实体名，路径，目标实体
    # print(temp_relations)
    relation_info = []
    for candidate in relation_candidate:
        if '/' in candidate[0]:
            true_entity = candidate[0].split('/')[0]
            temp_name = true_entity
            if '_(' in true_entity:
                temp_name = true_entity[:true_entity.find('_(')]
            elif '_（' in true_entity:
                temp_name = true_entity[:true_entity.find('_（')]
            entity_name = temp_name + '的' + candidate[0].split('/')[1]
        else:
            entity_name = candidate[0]

        temp = question
        for i in candidate[0]:  # 除去实体的剩余句子
            if i in question:
                temp = temp.replace(i, '')

        temp0 = temp
        in_question_word = 0
        for i in candidate[1]:  # 除去关系名的剩余句子
            if i in temp0:
                in_question_word = in_question_word + 1
                temp0 = temp0.replace(i, '')

        if candidate[1] in temp:
            relation_in_question = 1
        else:
            relation_in_question = 0
        aa = []
        bb = []

        temp_sentence = entity_name + '的' + candidate[1]

        for j in temp_sentence:  # 关系是否在句子中
            aa.append(j)
        for m in question:
            bb.append(m)
        word_jaccard = jaccard_distance(set(aa), set(bb))
        leve_score = Levenshtein.distance(question, entity_name + '的' + candidate[1])  # 关系是否在句子中
        # for key, value in temp_relations.items():  #路径名，目标实体

        '''
        guanxideci = jieba.cut(candidate[0])
        for word in guanxideci:
            if word in model and word in temp:
                temp.remove(word)
        '''
        '''
        segmentor2 = Segmentor()
        segmentor2.load("./ltpdata/ltp_data_v3.4.0/cws.model")
        temp2 = list(segmentor2.segment(candidate[1]))
        segmentor2.release()
        '''
        ##################jaccard
        # temp2 = list(jieba.cut(candidate[1]))
        # set1 = set(temp)
        # set2 = set(temp2)

        # print(temp, temp2)

        bert = simi(question, entity_name + '的' + candidate[1])
        # print(question, entity_name + '的' + candidate[1], w2v)

        words_jaccard = jaccard_distance(set(list(jieba.cut(question))), set(list(jieba.cut(temp_sentence))))
        edit = difflib.SequenceMatcher(None, question, temp_sentence).ratio()

        '''

        if key == c_relation_name:
            is_correct = 1
        else:
            is_correct = 0
        '''
        #
        # if w2v > 0.2:
        if candidate[2] != candidate[0]:  # 防止出现扰乱关系和实体成环现象
            relation_info.append(
                [candidate[0], candidate[1], candidate[2], candidate[3], candidate[4], in_question_word,
                 relation_in_question, bert])
        # 实体，路径名，目标实体，jaccard距离，编辑距离，向量相似度
    print(relation_info)
    # time.sleep(10)

    return relation_info
    '''
    print(id,  entity_keyid, key, jaccard, edit, w2v, is_correct)
    sentence = str(id) + "  " + str(entity_keyid) + "  " +str(key)+ "  "+ str(jaccard)+ "  " +str(edit)+"  " +str(w2v)+"  " +str(is_correct)+'\n'
    w = open("../NLPCC_KBQA/nlpcc-iccpol-2016.kbqa.training-data_process_entity_info.txt", 'a', encoding="utf-8")
    w.writelines(sentence)
    w.close()
    '''


#################################################
def relation_sort(relation_info):  # [entity_name, relation, target_entity, target_entity_keyid, jaccard, edit, w2v]
    # print(relation_info)
    if len(relation_info) == 1:
        return relation_info
    else:
        temp = []
        flag = 1
        relation_scores = LambdaRank.lambdarank(relation_info, flag)
        # print(relation_scores)
        temp_score = list(set(relation_scores))
        # entity_scores.sort()
        a = sorted(temp_score, key=lambda x: x * 1000 if x < 0 else x, reverse=True)
        # print(a)

        result10 = []
        result1 = []
        res = [idx for idx, i in enumerate(relation_scores) if i == a[0]]
        for i in res:
            # print(i)
            temp = []
            temp = relation_info[i]
            result1.append(temp)
        if len(a) >= 10:
            m = 10
        else:
            m = len(a)
        for j in range(0, m):
            res = [idx for idx, i in enumerate(relation_scores) if i == a[j]]
            for i in res:
                # print(i)
                temp = []
                temp = relation_info[i]
                result10.append(temp)
        '''
        res = [idx for idx, i in enumerate(relation_scores) if i == a[1]]
        for j in res:
            # print(i)
            temp = []
            temp = relation_info[j]
            result.append(temp)
        '''
        print(result1)
        ##time.sleep(10)
        return result1, result10


######################三种问题模板
def template(using_entity, question):  # 使用实体id，传进来的是[name , keyid]
    # print(using_entity)
    # template1
    query_candidates = []
    relations1 = []
    relations2 = []
    relations3 = []
    result1 = []
    result2 = []
    result3 = []
    for e in using_entity:
        # print(6)
        temp_relations = ccksNeo.get_entity_info_by_id(e[1])  # 该实体的所有relation信息
        # print("temp_relations:", temp_relations)  # [relation, target_entity, target_entity_id]
        for i in temp_relations:
            triple = [e[0], i[0], i[1], i[2], i[3]]
            relations1.append(triple)  # 所有实体的信息三元组[name, relation, target_entity ,target_entity_keyid]
    # print("realtion1", relations1)

    # remain_sentence = question.replace(relations1[0][0], "")
    relation_info = get_realtion_info(relations1, question)
    # print("relationinfo", relation_info)
    if len(relation_info) != 0:
        result1, result10 = relation_sort(relation_info)
        # time.sleep(6)
    else:
        # print(1111)
        result1 = relations1
    result_candidates = result1
    print(result1)

    # template2
    # for result_candidate in result_candidates:
    onehopid = {}
    if result10:
        # print(result10)
        for relation in result10:
            owl_relations2 = ccksNeo.get_entity_info_by_id(relation[3])
            for i in owl_relations2:
                triple = [relation[0] + '/' + relation[1] + '/' + relation[2], i[0], i[1], i[2], i[3]]  # 对第二跳来说实体是关系名
                # onehopid[relation[1]] = relation[2]
                relations2.append(triple)  # 二度子图所有实体的信息三元组[name, relation, target_entity ,target_entity_keyid]
        # print(relations2)
        relation_info = get_realtion_info(relations2, question)
        try:
            result2, result2_10 = relation_sort(relation_info)
            # time.sleep(6)
        except:
            result2 = relations2
        # return result1, result2

    ###########################template3
    if result2_10:
        # print(4444)
        max_score = 0
        for i in range(len(result2_10)):
            temp = ""
            simiword = 0
            temp_queston = question
            entity = result2_10[i][0].split('/')[0]
            relation1 = result2_10[i][0].split('/')[1]
            onehopentity = result2_10[i][0].split('/')[2]

            temp = entity + onehopentity
            if entity == result2_10[i][2]:
                continue

            for j in temp:
                if j in temp_queston:
                    temp_queston = temp_queston.replace(j, "")
            # print(temp)
            # score = serviceWord2vec.get_similarity(list(jieba.cut(temp_queston)), list(jieba.cut(temp)))
            # time.sleep(5)
            if result2_10[i][2] in temp_queston:
                temp_score = 0
                temp1 = relation1 + result2_10[i][1] + result2_10[i][2]
                temp_queston2 = question
                for m in entity:
                    if m in temp_queston2:
                        temp_queston2 = temp_queston2.replace(m, "")
                for k in temp1:
                    if k in temp_queston2:
                        temp_score = temp_score + 1
                if temp_score > max_score:
                    result3 = []
                    max_score = temp_score
                    result3.append(
                        [entity, relation1 + '*', onehopentity, 0, ['Instance'], result2_10[i][1], result2_10[i][2]])
                elif temp_score == max_score:
                    result3.append(
                        [entity, relation1 + '*', onehopentity, 0, ['Instance'], result2_10[i][1], result2_10[i][2]])
        # print(result3)
        # time.sleep(10)
    ##########################

    if result3 != []:
        print(6767)
        return result3
    else:
        print(565)
        print(result1, result2)
        # time.sleep(6)
        result4 = choose_type(result1, result2, question)
        return result4
    '''
    return result1, result2, result3
    '''


def choose_type(result1, result2, question):
    type_score1 = 0
    type_score2 = 0
    temp = question
    if result1:
        for j in result1[0][0]:
            if j in temp:
                temp = temp.replace(j, '', 1)
        for i in result1[0][1]:
            if i in temp:
                temp = temp.replace(i, '', 1)
                type_score1 = type_score1 + 1
    temp = question
    if result2:
        entity = result2[0][0].split('/')[0]
        relation1 = result2[0][0].split('/')[1]
        two_hop_relation = relation1 + result2[0][1]
        # print(two_hop_relation)
        for j in entity:
            if j in temp:
                temp = temp.replace(j, '', 1)
        for i in two_hop_relation:
            if i in temp:
                # print(i)
                temp = temp.replace(i, '', 1)
                type_score2 = type_score2 + 1
    # print(type_score1, type_score2)
    # time.sleep(10)
    if (type_score1 + 1 < type_score2 and result2[0][-1] >= 0.2) or (
            type_score1 < type_score2 and result2[0][-1] >= 0.6):
        result4 = result2
    else:
        result4 = result1
    # print(result4)
    return result4


def answer(line):
    index1 = line.find('|||')
    index2 = line[index1 + 4:].find('|||')
    question_id = line[:index1]
    question = line[index1 + 3:-1]
    # print(question_id, question )
    # sentence = question
    ###########################################
    word_list = []
    # question = "诗人李白葬在了何地？"
    entity_list = []  # 筛选出来的指称
    # allentity = []  # 实体
    entity_info = []
    using_entity = []
    # sentence = question
    # word_list = segmentsentence(sentence)
    # word_list = list(word_list)  # 分词后的原始指称
    word_list = list(jieba.cut(question))
    # word_list = list(set(word_list))
    # print(word_list)
    normal_list = entityRecognize(word_list, question)  # 这里召回的是指称
    # print(entity_list)
    ###########################################
    bert_list = bert_ner(question)

    entity_list = normal_list + bert_list
    entity_list = list(set(entity_list))
    # print(entity_list)
    if "是什么" in entity_list:
        entity_list.remove("是什么")
    temp = entity_list[:]
    for i in temp:
        if i in question_words:
            entity_list.remove(i)

    temp_mention = entity_list[:]
    for mention in temp_mention:
        if mention in mention2entity_dic:  # 如果它有对应的实体
            for entity in mention2entity_dic[mention]:
                entity_list.append(entity)
    entity_list = list(set(entity_list))
    print(entity_list)
    entity_info = entityLink(entity_list, question)  # 提取实体用于排序的信息
    using_entity = entity_sort(entity_info)[:5]  # 实体排序的结果（top2），得到name和id
    # print(using_entity)
    # time.sleep(6)
    shiti = ""
    result1 = []
    result2 = []
    result3 = []
    result4 = []
    for j in using_entity:
        shiti += str(j[0]) + '|' + str(j[1]) + '||'
    try:
        result4 = template(using_entity, question)
        # print(result4)
        # time.sleep(6)
    except:
        # print("error")
        # time.sleep(6)
        neirong = question_id + '|||' + question + '|||' + shiti + '|||哈哈哈哈|哈哈哈哈|哈哈哈哈|||||' + '\n'
    else:
        # result4 = choose_type(result1, result2)
        daan1 = ""
        daan2 = ""
        daan3 = ""
        daan4 = ""
        '''
        if result1:
            for result in result1:
                daan1 = daan1 + str(result[0]) + '|' + str(result[1]) + '|' + str(result[2]) + '||'
        else:
            daan1 = '哈哈哈哈|哈哈哈哈|哈哈哈哈||'

        if result2:
            for result in result2:
                daan2 = daan2 + str(result[0]) + '|' + str(result[1]) + '|' + str(result[2]) + '||'
        else:
            daan2 = '哈哈哈哈|哈哈哈哈|哈哈哈哈||'

        if result3:
            for result in result3:
                daan3 = daan3 + str(result[0]) + '|' + str(result[1]) + '|' + str(result[2]) + '||'
        else:
            daan3 = '哈哈哈哈|哈哈哈哈|哈哈哈哈||'
        '''
        if result4:
            for result in result4:
                if result[4][0] == 'Instance':
                    daan4 = daan4 + str(result[0]) + '|' + str(result[1]) + '|' + '<' + str(result[2]) + '>' + '||'
                elif result[4][0] == 'Discription':
                    daan4 = daan4 + str(result[0]) + '|' + str(result[1]) + '|' + '"' + str(result[2]) + '"' + '||'
        else:
            daan4 = '哈哈哈哈|哈哈哈哈|哈哈哈哈||'

        neirong = question_id + '|||' + question + '|||' + shiti + '|||' + daan4 + '|||' + '\n'
        # print(neirong)
    q = open("answer_88_2.txt", 'a', encoding="utf-8")
    q.writelines(neirong)


question_words = ["谁", "何", "哪", "什么", "哪儿", "哪里", "几时", "几", "多少",
                  "怎", "怎么", "怎的", "怎样", "怎么样", "怎么着", "如何", "为什么",
                  "吗", "呢", "吧", "啊", '是什么', '在哪里', '哪里', '什么', '提出的', '有什么', '国家', '哪个', '所在',
                  '培养出', '为什么', '什么时候', '人', '你知道', '都包括', '是谁', '告诉我', '又叫做', '有', '是']
p = open("question.txt", 'r+', encoding="utf-8")
for line in p:
    answer(line)

