# -*- coding: utf-8 -*-

import sys
import json

while True:
  line = sys.stdin.readline()
  if not line:
    break
  raw_record = json.loads(line)

  #make a licence
  licence_record = {
    "source_url": raw_record['source_url'],
    "company_name": raw_record['name'],
    "licence_jurisdiction": "Serbia",
    "category": "Financial",
    "regulator": "National Bank of Serbia",
    "jurisdiction_classification": raw_record['category'],
    "sample_date": raw_record['sample_date'],
    "confidence": "MEDIUM"
  }
  if ('country' in raw_record):
    licence_record["company_jurisdiction"] = raw_record['country']
  else:
    licence_record["company_jurisdiction"] = "Serbia"
  if ('status' in raw_record):
    licence_record["status"] = raw_record["status"]

  #output the result
  print json.dumps(licence_record)