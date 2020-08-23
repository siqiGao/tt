import sys  
import os

c = os.getcwd()
sys.path.append(c+'/bert/bertNER')
sys.path.append(c+'/bert/bertNER/bert')
sys.path.append(c+'/bert/berNER/chinese_L-12_H-768_A-12')  

import try_predict
def bert_ner(line):
    entity = try_predict.ner(line)
    print(entity)
    return entity

bert_ner("被誉为童话王国的是哪个国家？")
