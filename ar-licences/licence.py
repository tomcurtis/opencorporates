# -*- coding: utf-8 -*-

import sys
import json

names_used = []

while True:
  line = sys.stdin.readline()
  if not line:
    break
  raw_record = json.loads(line)

  #make a licence
  licence_record = {
    "source_url": raw_record['source_url'],
    "company_name": raw_record['name'],
    "licence_jurisdiction": "Argentina",
    "category": "Financial",
    "regulator": "Banco Central de la República Argentina",
    "jurisdiction_classification": raw_record['type_of_institution'],
    "sample_date": raw_record['sample_date']
  }

  if (raw_record['type_of_institution'] == "Representative of foreign financial institution not licensed in Argentina"):
    licence_record["company_jurisdiction"] = raw_record['country']
  else:  
    licence_record["company_jurisdiction"] = "Argentina"

  #output the result -- avoid duplicates
  if (raw_record['name'] not in names_used):
    print json.dumps(licence_record)
    names_used.append(raw_record['name'])