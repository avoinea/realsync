""" Update proxy list
"""
from pprint import pformat
import csv

PROXIES = {}
reader = csv.reader(open('proxy.csv', 'r'))
for index, row in enumerate(reader):
    if index == 0:
        continue

    typo = row[6].lower()
    if not 'http' in typo:
        continue

    anon = row[7].lower()
    if 'high' not in anon:
        continue

    ip = row[1]
    port = row[2]
    PROXIES["%s:%s" % (ip, port)] = typo

with open('proxy.py', 'w') as out:
    out.write(u"PROXIES = " + pformat(PROXIES))
