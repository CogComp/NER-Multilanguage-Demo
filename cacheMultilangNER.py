import json 
from datetime import datetime

class CacheNER:

    def __init__(self):
        self.lang = ["aka"]


    def load(self, name):
        '''
        name: "cogcomp", "bert"
        '''
        try:
            with open('./cache/cache_' + name + '.json') as file_obj:
                cache = json.load(file_obj)
            print("Successfully load cache from cache_" + name + ".json.")
        except:
            cache = {}
            for lang in self.lang: 
                cache[lang] = {}
            print("Cannot find cache_" + name + ".json and an empty new nested dictionary for cache is created.")
        
        return cache 


    def read(self, name, cache_dic, lang, hash_value):

        res_json = cache_dic[lang][hash_value]['res_json']
        
        if 'count' not in cache_dic[lang][hash_value].keys():
            cache_dic[lang][hash_value]['count'] = 1
        else:
            cache_dic[lang][hash_value]['count'] += 1

        print("--------------The annotations is loaded from cache_" + name + "--------------")


        return res_json, cache_dic


    def add(self, name, cache_dic, lang, text, hash_value, res_json):

        cache_dic[lang][hash_value] = {}
        cache_dic[lang][hash_value]['text'] = text
        cache_dic[lang][hash_value]['res_json'] = res_json
        cache_dic[lang][hash_value]['count'] = 1

        print("--------------The annotations is not included in cache_" + name + "--------------")

        return cache_dic


    def count(self, cache_dic):
        '''
        This function is used to count the number of sentence in a cache
        '''  
        num = sum([len(cache_dic[key]) for key in cache_dic.keys()])

        return num


    def write(self, name, cache_dic):

        json_dic = json.dumps(cache_dic, indent=4)
        with open('cache/cache_' + name + '_'+ datetime.now().strftime('%Y-%m-%d-%H-%M-%S') + '.json', 'w') as json_file:
            json_file.write(json_dic) 