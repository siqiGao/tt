from py2neo import Graph

def execute(statement):
    graph1 = Graph("http://10.1.1.5:7474/browser/", username="neo4j", password="123456")
    #statement1 = "match (n:Instance) where n.name= \""+"龙卷风"+"\" return n"
    print(statement)
    print(2)
    result = []
    try:
        print(3)
        list1 = graph1.run(statement).data()
        print(4)
    except Exception as m:
        print(m)
        return []
    else:
        if list1:
            for element in list1:  # 子（实体）
                sub_result = {}
                sub_row = []
                for key, values in element.items():  # 返回来的结果类型如id，type，n等
                    if isinstance(values, dict):
                        sub_sub_result = {}
                        for i, j in values.items():
                            sub_sub_result[i] = j
                        sub_row.append(sub_sub_result)
                    else:
                        sub_row.append(values)
                sub_result['row'] = sub_row
                result.append(sub_result)
            #print(result)
        else:
            print("kong")
        return result


def get_id_by_name(name):
    graph1 = Graph("http://10.1.1.5:7474/browser/", username="neo4j", password="123456")
    statement = "match (n:Instance)-[r]->(m) where n.name = \"" + name + "\" return id(n)"
    # statement = "match (n:Instance) where n.name= \""+"红楼梦"+"\" return n"
    list1 = graph1.run(statement).data()
    print(list1[0]['id(n)'])
    return list1[0]['id(n)']

def get_entity_info_by_neoid(neoid):
    graph1 = Graph("http://10.1.1.5:7474/browser/", username="neo4j", password="123456")
    statement = "match (n:Instance)-[r]->(m) where id(n) = " + str(neoid) + " return r.value, m.name, id(m)"
    # statement = "match (n:Instance) where n.name= \""+"红楼梦"+"\" return n"
    list1 = graph1.run(statement).data()
    #print(list1)
    result = []
    for i in list1:
        sub_list = []
        for key, value in i.items():
            sub_list.append(value)
        result.append(sub_list)
    print(result)
    return result


def get_entity_list_by_name(name):#######
    entity_list = []
    # 再通过全名检索
    statement = "match (n:Instance) where n.name =\"" + str(name) + "\" return id(n), n"
    result = execute(statement)
    print(result)
    if len(result)!= 0:
        for data in result:
            entity = data['row'][1]
            entity['id'] = data['row'][0]
            entity['label'] = 'None' if 'label' not in entity else entity['label']
            entity_list.append(entity)
        print(entity_list)

    return entity_list

def get_related_entities_by_id(id):####
    statement = "match (n:Instance)-[r]->(m) where id(n) = " + str(id) + " return r.value,m.name,id(m)"
    related_entities = []
    print(statement)
    result = execute(statement)
    print(result)
    if len(result)!= 0 :
        for data in result:
            related_entities.append({'name': data['row'][0], 'target_name': data['row'][1], 'target_Id': data['row'][2]})
        print(related_entities)
    return related_entities

# def get_entity_info_by_id(id):########
#     statement = "match (n:Instance)-[r]->(m:Instance) where id(n)=" + str(id) + " return r.value,m.name,id(m)"
#     result = execute(statement)
#     entity = []
#     if len(result) != 0:
#         for i in result:
#             entity.append(i["row"])
#     print(entity)
#     return entity

def get_entity_info_by_id(id):########
    statement = "match (n:Instance)-[r]->(m) where id(n)=" + str(id) + " return r.value,m.name,id(m),labels(m)"
    result = execute(statement)
    entity = []
    if len(result) != 0:
        for i in result:
            entity.append(i["row"])
    print(entity)
    return entity

def get_entity_info_by_name(name):########
    statement = "match (n:Instance)-[r]->(m) where n.name=\"" + str(name) + "\" return r.value,m.name,id(m)"
    result = execute(statement)
    entity = []
    if len(result) != 0:
        for i in result:
            entity.append(i["row"])
    print(entity)
    return entity
'''
def get_relation_by_id(id):
    statement = "match (n:Instance)-[r]->(m:Instance) where n.id=\""+ id +"\" return r.value,m.name,m.id"
    result = execute(statement)
    print(result)
    temp = []
    for i in result:
        temp.append(i['row'])
    print(temp)
    return temp
'''

