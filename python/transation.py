#!/usr/bin/env python
# coding=utf-8

import urllib.request
import urllib.parse
import json

content = input("请输入需要翻译的内容：")
#content = '我的未来不是梦'
url = "http://fanyi.youdao.com/translate?smartresult=dict&smartresult=rule&smartresult=uqc&sessionFrom=http://www.youdao.com/"
data = {}
data['type'] = 'AUTO'
data['i'] = content
data['doctype'] = 'json'
data['xmlVersion'] = 'fanyi.web'
data['ue'] = 'UTF-8'
data['typoResult'] = 'true'
data = urllib.parse.urlencode(data).encode('utf-8')

response = urllib.request.urlopen(url,data)
html = response.read().decode('utf-8')
target = json.loads(html)

print('翻译结果:%s' %(target['translateResult'][0][0]['tgt']))
