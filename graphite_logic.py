#!/usr/bin/python3
# coding=utf-8
"""
----------------------------------------------------------------------
Send and recieve data from from graphite/carbon database
https://graphite.readthedocs.io/en/latest/render_api.html
----------------------------------------------------------------------
"""
#----------------------------------------------------------------------


import sys
import time 
import requests
# local serial wrapper class
#sys.path.append('../common')
import simplejson as json



r = requests.get('http://pidp.local:8013/render?target=baro.metric&from=-90s&format=json')

#print(r.json())  # this will give your the JSON file with the data

foo = r.json()

print(foo)

bar = foo[0]

print(bar['target'])
#print(bar['datapoints'])

for dp in bar['datapoints']:
    print("val: {}  time: {}".format(dp[0],dp[1]))
    print("stale: {} seconds".format(time.time() - dp[1]))

