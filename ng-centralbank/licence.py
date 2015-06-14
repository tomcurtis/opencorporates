# -*- coding: utf-8 -*-

import sys
import json

while True:
  line = sys.stdin.readline()
  if not line:
    break
  raw_record = json.loads(line)

  if ('type_of_institution' in raw_record):
    
    #make a licence
    licence_record = {
      "source_url": raw_record['source_url'],
      "company_name": raw_record['name'],
      "company_jurisdiction": "Nigeria",
      "licence_jurisdiction": "Nigeria",
      "category": "Financial",
      "regulator": "Central Bank of Nigeria",
      "jurisdiction_classification": raw_record['type_of_institution'],
      "sample_date": raw_record['sample_date']
    }

    #output the result
    print json.dumps(licence_record)