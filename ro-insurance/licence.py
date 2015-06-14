# -*- coding: utf-8 -*-

import sys
import json

while True:
  line = sys.stdin.readline()
  if not line:
    break
  raw_record = json.loads(line)

  #These are always the same
  record = {
    'source_url': raw_record['source_url'],
    'company_name': raw_record['name'],
    'sample_date': raw_record['sample_date'],
    'company_jurisdiction': raw_record['Country'],
    'licence_jurisdiction': 'Romania',
    'confidence': 'MEDIUM',
    'category': 'Financial',
    'jurisdiction_classification': raw_record['category'],
  }

  if (raw_record['category'] == "Insurance undertakings and intermediaries from EEA"):
    record['licence_number'] = raw_record['Registration no.']
  else:
    if ('Authorization no.' in raw_record):
      record['licence_number'] = raw_record['Authorization no.']
      record['start_date'] = raw_record['Authorization date']

  if ('Regulator' in raw_record):
    record['regulator'] = raw_record['Regulator']['Denumire']
  else:
    record['regulator'] = 'Financial Supervisory Authority, Romania'
  
  if ('Sole reg. no' in raw_record):
    record['licence_number'] = raw_record['Sole reg. no']
  
  if (raw_record['category'][:9] == "Section B"):
    record['status'] = "Revoked"
  else:
    record['status'] = "Current"

  #end date
  if ("Strike off date" in raw_record):
    record['end_date'] = raw_record["Strike off date"]

  print(json.dumps(record))