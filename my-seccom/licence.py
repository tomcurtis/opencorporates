# -*- coding: utf-8 -*-

import sys
import json
import time

#have to turn dates into yyyy-mm-dd format
def parse_date(date_string):
  struct_time = time.strptime(date_string, "%d %b %Y")
  correct_date_format = time.strftime("%Y-%m-%d", struct_time)
  return correct_date_format

while True:
  line = sys.stdin.readline()
  if not line:
    break
  raw_record = json.loads(line)

  #only take details from the main page, not the list of licences. each licence can appear as its own page (e.g. LicenceID=33456 and LicenceID=17835)
  licence_record = {
    "source_url": raw_record['source_url'],
    "company_name": raw_record['name'],
    "company_jurisdiction": "Malaysia",
    "licence_jurisdiction": "Malaysia",
    "licence_number": raw_record['licence_number'],
    "category": "Financial",
    "regulator": "Securities Commission, Malaysia",
    "sample_date": raw_record['sample_date'],
    "confidence": "MEDIUM",
    "end_date": parse_date(raw_record['anniversary_date'])
  }

  if ('regulated_activities' in raw_record):
    licence_record['jurisdiction_classification'] = " / ".join(raw_record['regulated_activities']) #optional field and can be list of strings

  #output the result
  print json.dumps(licence_record)