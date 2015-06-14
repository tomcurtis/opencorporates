import sys
import json

while True:
  line = sys.stdin.readline()
  if not line:
    break
  raw_record = json.loads(line)

  #ignore unwanted categories
  if (raw_record['category'] not in ["Illegal operator", "Capital market operator with incomplete registration"]):
    
    #make a licence
    licence_record = {
      "source_url": raw_record['source_url'],
      "company_name": raw_record['name'],
      "company_jurisdiction": "Nigeria",
      "licence_jurisdiction": "Nigeria",
      "category": "Financial",
      "regulator": "Securities and Exchange Commission, Nigeria",
      "jurisdiction_classification": raw_record['category'],
      "sample_date": raw_record['sample_date']
    }

    #output the result
    print json.dumps(licence_record)