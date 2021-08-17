import json
import os
import numpy as np


class parse_map_to_json(object):
    def __init__(self,filename):
        self.map_file = self.mapToJson(filename)

    def mapToJson(self, filename):
        filenameList = []
        map_config = []
        map_dict = {}
        path = os.path.realpath('.') + '/conf/'  #这里要改
        if filename:
            filenameList=[filename]
        else:
            filenames = os.listdir(path)
            for item in filenames:
                file = os.path.splitext(item)
                filename, type = file
                if type == '.map':
                    # if type == '.txt':
                    filenameList.append(item)
                    break

        if len(filenameList) > 0:
            for i in filenameList:
                with open(path + i, 'r') as f:  #这里要改
                    read = f.readlines()
                    start_index = 0
                    end_index = len(read)
                    try: #直接在这里
                        start_index = list.index(read, 'GLOBAL SYMBOLS: SORTED ALPHABETICALLY BY Name \n') + 4
                        end_index = list.index(read, 'GLOBAL SYMBOLS: SORTED BY Symbol Address \n') - 3
                    except Exception as e:
                        print('未找到匹配的地址信息,解析过程可能稍慢，请耐心等待。')
                    read = read[start_index:end_index]
                    if start_index > 0:  # 匹配到开始结束位时，直接读取整个列表添加到数组中
                        for t in read:
                            t = t.strip('\n')
                            t = t.split(' ')
                            if t[0][-4:] not in map_dict.keys():
                                map_dict[t[0][-4:]] = t[-1]
                                map_config.append({'value': t[0][-4:], 'desc': t[-1]})
                    else:  # 未匹配到开始结束位时，就把列表循环。一般不会出现这种情况
                        for t in read:
                            t = t.strip('\n')
        return map_config, map_dict