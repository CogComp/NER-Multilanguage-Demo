import cherrypy
import os
import json
import requests
import tabular

import hashlib
import cacheMultilangNER
from datetime import datetime
import sys 

################################ Cache Loading ################################
# Instantiate Cache Class
cache = cacheMultilangNER.CacheNER()
        
cache_cogcomp = cache.load("cogcomp")
cache_bert = cache.load("bert")

################################ Service Path ################################
BASE_HTML_PATH = "./html"
BASE_MULTILANG_NER_HTTP = 'http://dickens.seas.upenn.edu:4033/ner'
# BASE_MULTILANG_EDL_HTTP = 'http://macniece.seas.upenn.edu:4032/edl'

# BASE_COGCOMP_HTTP = "http://macniece.seas.upenn.edu:4001/annotate"

def getBasicNER(lang,text):
    res_json = getMULTILANG_NER_BERT(lang,text)
    tokens = []
    endPositions = []
    if "tokens" in res_json:
        tokens = res_json["tokens"]
    if "sentences" in res_json:
        sentences = res_json["sentences"]
        if "sentenceEndPositions" in sentences:
            endPositions = sentences["sentenceEndPositions"]
    # print(tokens)
    return tokens, endPositions, res_json

'''
def getBasicCCG(text):
    input = {"views":"TOKENS","text":text}
    res_out = requests.get(BASE_COGCOMP_HTTP, params = input)
    # print(res_out.text)
    res_json = json.loads(res_out.text)
    tokens = []
    endPositions = []
    if "tokens" in res_json:
        tokens = res_json["tokens"]
    if "sentences" in res_json:
        sentences = res_json["sentences"]
        if "sentenceEndPositions" in sentences:
            endPositions = sentences["sentenceEndPositions"]
    # print(tokens)
    return tokens, endPositions
'''

def getBasics(annView):
    #input = {"views":"TOKENS","text":text}
    #res_out = requests.get(BASE_COGCOMP_HTTP, params = input)
    #res_json = json.loads(res_out.text)
    res_json = annView
    tokens = []
    endPositions = []
    if "tokens" in res_json:
        tokens = res_json["tokens"]
    if "sentences" in res_json:
        sentences = res_json["sentences"]
        if "sentenceEndPositions" in sentences:
            endPositions = sentences["sentenceEndPositions"]
    # print(tokens)
    return tokens, endPositions

def initView(myTabularView,lang,text):
    myTabularView.setText(text)
    # t,s = getBasicCCG(text)
    t,s,res_json = getBasicNER(lang,text)
    myTabularView.setTokens( t )
    myTabularView.setSentenceEnds( s )
    return res_json

'''
    NER EXAMPLE: 
    # curl -d '{"lang" : "rus", "model" : "bert", "text" : "В прошлом году я жил в Шампейне, штат Иллинойс. Тогда моей лучшей подругой была Дейзи Джонсон."}' -H "Content-Type: application/json" -X POST http://cogcomp.org/dc4033/ner/
'''

def getMULTILANG_NER_BERT(lang,text):
    global cache_bert

    hash_value = hashlib.sha1(text.encode()).hexdigest()

    if cache.count(cache_bert) > 200:
        cache.write('bert', cache_bert)
        cache_bert = cache.load('bert')

    if hash_value in cache_bert[lang].keys():
        res_json, cache_bert = cache.read('bert', cache_bert, lang, hash_value)

    else:
        input = {"lang":lang,"model":"bert","text":text}
        res_out = requests.get(BASE_MULTILANG_NER_HTTP, params = input)
        #print('==========')
        #print(res_out.text)
        #print('----------')
        try:
            res_json = json.loads(res_out.text)
        except:
            res_json = {"tokens":[]}
        #print('==========')
        #print(res_json)
        #print('----------')
        cache_bert = cache.add('bert', cache_bert, lang, text, hash_value, res_json)

    return res_json

def getMULTILANG_NER_COGCOMP(lang,text):
    global cache_cogcomp

    hash_value = hashlib.sha1(text.encode()).hexdigest()

    if cache.count(cache_cogcomp) > 200:
        cache.write('cogcomp', cache_cogcomp)
        cache_cogcomp = cache.load('cogcomp')

    
    if hash_value in cache_cogcomp[lang].keys():
        res_json, cache_cogcomp = cache.read('cogcomp', cache_cogcomp, lang, hash_value)

    else:
        input = {"lang":lang,"model":"cogcomp","text":text}
        res_out = requests.get(BASE_MULTILANG_NER_HTTP, params = input)
        #print('==========')
        #print(res_out.text)
        #print('----------')
        try:
            # print(res_out.json())
            res_json = json.loads(res_out.text)
        except:
            res_json = {"text_tokens":[]}
        #print('==========')
        #print(res_json)
        #print('----------')
        cache_cogcomp = cache.add('cogcomp', cache_cogcomp, lang, text, hash_value, res_json)
    return res_json

def processNER(myTabularView,lang,text):
    # print('>>>>>>>>>>>>>>>> processNER')
    annjson = initView(myTabularView, lang, text)
    # annjson = getMULTILANG_NER(lang,text)
    if "tokens" in annjson:
        myTabularView.setText(text)
        t,s = getBasics(annjson)
        myTabularView.setTokens( t ) # reset tokens in foreign language
        # myTabularView.setSentenceEnds( s )
        tokens = annjson["tokens"]
        if len(tokens) != len(myTabularView.getTokens()): return
        myTabularView.addSpanLabelView(annjson,"NER_CONLL","NER-Neural")
    try:
        annjson2 = getMULTILANG_NER_COGCOMP(lang,text)
        if "text_annotation" in annjson2:
            annjson2 = annjson2["text_annotation"]
            if "tokens" in annjson2:
                #print(annjson2)
                #print("-----------")
                tokens = annjson2["tokens"]
                if len(tokens) != len(myTabularView.getTokens()): return
                myTabularView.addSpanLabelView(annjson2,"NER_CONLL","NER-CogComp")
    except Exception as e:
        print("An exception occurred when runnin CogComp NER")
        print(e)
    return annjson,tokens

def doProcess(myTabularView, lang=None, text=None, anns=None):
    # print(">>>>>> PROCESS")
    myTabularView.reset()
    # initView(myTabularView, text) # DOES THE SENTENCE SPLITTER WORK FOR NON-ENGLISH TEXT?
    # for ann in anns:
    ann = "NER"
    nerjson = {}
    tokens = []
    # if True or ann in ["NER","EDL"]: 
    nerjson,tokens = processNER(myTabularView, lang, text)
    print("TOKENS",tokens)
    h = myTabularView.HTML()
    return h

def doProcessInnerNeural(lang=None, text=None, anns=None):
    av = getMULTILANG_NER_BERT(lang,text)
    tokens = av["tokens"]
    startAnns = tokens.copy()
    finalAnns = tokens.copy()
    for i in range(len(startAnns)):
        startAnns[i] = ""
    for i in range(len(finalAnns)):
        finalAnns[i] = ""
    if "views" in av:
        views = av["views"]
        for view in views:
            if view["viewName"] == "NER_CONLL":
                consts = view["viewData"][0]["constituents"]
                for const in consts:
                    start = const["start"]
                    end = const["end"]
                    startAnns[start] += '<span class="w3-border NER-Neural-'+const["label"]+'">' + '&nbsp;<b>[' + const["label"] + ']</b>&nbsp;'
                    finalAnns[end-1] += '&nbsp;</span>&nbsp;'
    h = ""
    h += '<div class="w3-panel w3-border w3-border-amber"><br>&nbsp;'
    for i in range(len(tokens)):
        h += startAnns[i] + tokens[i] + finalAnns[i] + " "
    h += '<br>&nbsp;'
    h += '</div><br>&nbsp;'
    return h

def doProcessInnerCogComp(lang=None, text=None, anns=None):
    av = getMULTILANG_NER_COGCOMP(lang,text)
    tokens = av["text_tokens"]
    startAnns = tokens.copy()
    finalAnns = tokens.copy()
    for i in range(len(startAnns)):
        startAnns[i] = ""
    for i in range(len(finalAnns)):
        finalAnns[i] = ""
    if "text_annotation" in av:
        if "views" in av["text_annotation"]:
            views = av["text_annotation"]["views"]
            for view in views:
                if view["viewName"] == "NER_CONLL":
                    consts = view["viewData"][0]["constituents"]
                    for const in consts:
                        start = const["start"]
                        end = const["end"]
                        startAnns[start] += '<span class="w3-border NER-Neural-'+const["label"]+'">' + '&nbsp;<b>[' + const["label"] + ']</b>&nbsp;'
                        finalAnns[end-1] += '&nbsp;</span>&nbsp;'
    h = ""
    h += '<div class="w3-panel w3-border w3-border-amber"><br>&nbsp;'
    for i in range(len(tokens)):
        h += startAnns[i] + tokens[i] + finalAnns[i] + " "
    h += '<br>&nbsp;'
    h += '</div><br>&nbsp;'
    return h

class MyWebService(object):

    _myTabularView = None
    
    @cherrypy.expose
    def index(self):
        return open(BASE_HTML_PATH+'/index.php')

    def html(self):
        pass

    @cherrypy.expose
    @cherrypy.tools.json_out()
    @cherrypy.tools.json_in()
    def info(self, **params):
        return {"status":"online"}

    @cherrypy.expose
    def halt(self, **params):
        cherrypy.engine.exit()

    @cherrypy.expose
    @cherrypy.tools.json_out()
    @cherrypy.tools.json_in()
    def view(self, text=None, lang=None, anns=None):
        input = { "lang" : None , "text" : None , "anns" : [] }
        try:
            data = cherrypy.request.json
        except:
            data = cherrypy.request.params
        if "lang" in data: input["lang"] = data["lang"]
        if "text" in data: input["text"] = data["text"]
        if "anns" in data: input["anns"] = data["anns"]
        # print(">>>>>>>>>", data["text"])
        
        html = ""
        if "NEURAL" in data["anns"]:
            html += '<div class="subtitle">Neural</div>'#<br>'
            html += doProcessInnerNeural(data["lang"] , data["text"] , data["anns"])
        if "COGCOMP" in data["anns"]:
            html += '<div class="subtitle">CogComp</div>'#<br>'
            html += doProcessInnerCogComp(data["lang"] , data["text"] , data["anns"])
        
        #self._myTabularView = tabular.TabularView()
        #html = doProcess(self._myTabularView, data["lang"] , data["text"] , data["anns"])
                
        result = {"input": input, "html": html}
        return result

################################ sys parameters ###############################
serviceHost = sys.argv[1]
servicePort = int(sys.argv[2])

if __name__ == '__main__':
    print ("")
    print ("Starting 'Multilang' rest service...")
    config = {'server.socket_host': '0.0.0.0'}
    cherrypy.config.update(config)
    config = {
      'global' : {
            #'server.socket_host' : 'dickens.seas.upenn.edu',
            'server.socket_host' : serviceHost,
            #'server.socket_port' : 4032,
            'server.socket_port' : servicePort,
            'cors.expose.on': True
      },
      '/': {
            'tools.sessions.on': True,
            'tools.staticdir.root': os.path.abspath(os.getcwd())

      },
      '/static': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': BASE_HTML_PATH
      },
      '/html' : {
        'tools.staticdir.on'    : True,
        'tools.staticdir.dir'   : BASE_HTML_PATH,
        'tools.staticdir.index' : 'index.html',
        'tools.gzip.on'         : True
      },
    }
    cherrypy.config.update(config)
    cherrypy.quickstart(MyWebService(), '/', config)

    cache.write('cogcomp', cache_cogcomp)
    cache.write('bert', cache_bert)

