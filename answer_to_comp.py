import ccksNeo

q = open("answer20_723.txt", 'r', encoding="utf-8")
p = open("answer_to_comp.txt", 'a', encoding="utf-8")

for line in q:
    sentence = ""
    yitiao = []
    yitiaodaan = []

    index2 = line.find('|||||')
    try:
        yitiao = line.split("|||||")[1]
    except:
        print(1)

    try:
        yitiaodaan = yitiao.split("||")
    except:
        print(3)

    an21 = []
    if yitiaodaan:
        for i in yitiaodaan:
            if i != ' ':
                try:
                    an21.append(i.split("|")[2])
                except:
                    print(1)
    comp = list(set(an21))
    for mm in comp:
        info = ccksNeo.get_entity_info_by_name(mm)
        if info != []:
            sentence = sentence + '\t' + '<' + mm + '>'
        else:
            sentence = sentence + '\t' + '“' + mm + '”'
    print(comp)
    p.writelines(sentence + '\n')
