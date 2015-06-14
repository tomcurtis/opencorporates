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
    "company_jurisdiction": "Nepal",
    "licence_jurisdiction": "Nepal",
    "category": "Financial",
    "regulator": "Insurance Regulatory Authority of Nepal",
    "jurisdiction_classification": raw_record['category'],
    "sample_date": raw_record['sample_date'],
    "confidence": "HIGH"
  }

  #output the result
  print json.dumps(licence_record)