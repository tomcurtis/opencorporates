import sys
import json

while True:
  line = sys.stdin.readline()
  if not line:
    break
  raw_record = json.loads(line)

  #skip insurance agents as these are individuals, not companies
  if (raw_record['category'] == "Insurance agent"):
    continue

  #make a licence
  licence_record = {
    "source_url": raw_record['source_url'],
    "company_name": raw_record['name'],
    "company_jurisdiction": "Nigeria",
    "licence_jurisdiction": "Nigeria",
    "category": "Financial",
    "regulator": "National Insurance Commission, Nigeria",
    "jurisdiction_classification": raw_record['category'],
    "sample_date": raw_record['sample_date']
  }

  #output the result
  print json.dumps(licence_record)