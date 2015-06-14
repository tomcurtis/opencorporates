# -*- coding: utf-8 -*-

import json
import sys
import datetime

#need to check some of the dates in case excel brought them back as numbers
def is_number(s):
  try:
    float(s)
    return True
  except ValueError:
    return False

while True:
  line = sys.stdin.readline()
  if not line:
    break
  raw_record = json.loads(line)

  #most fields are the same for all licences
  licence_record = {
    "source_url": raw_record['source_url'],
    "company_jurisdiction": "Kazakhstan",
    "licence_jurisdiction": "Kazakhstan",
    "category": "Financial",
    "regulator": "National Bank of Kazakhstan",
    "sample_date": raw_record['sample_date'],
    "confidence": "HIGH",
    "jurisdiction_classification": [raw_record['category']]
  }

  #cope with upper/lower case
  if ('name' in raw_record):
    licence_record['company_name'] = raw_record['name']
  if ('Name' in raw_record):
    licence_record['company_name'] = raw_record['Name']

  #skip the ones with no name or which were just notes
  if ('company_name' not in licence_record):
    continue
  if (licence_record['company_name'][0] == "*"):
    continue

  #use detail of each category to get the classifications - sources one, two and three
  if ((raw_record['category'] == "Banking operation") or (raw_record['category'] == "Insurance activity")):
    #categories approved are marked with a plus sign
    for k,v in raw_record.items():
      if (v == "+"):
        licence_record['jurisdiction_classification'].append(k)
    #mm/dd/yyyy format it seems (have an 08/14/2008 example)
    if ('Date of Granting License' in raw_record):
      date_string = raw_record['Date of Granting License']
      if (is_number(date_string)):
        date_number = float(date_string)
        new_date = datetime.date(1900, 1, 1) + datetime.timedelta(date_number)
        licence_record['start_date'] = new_date.isoformat()
      else: #date format already
        date_parts = date_string.split("/")
        licence_record['start_date'] = date_parts[2] + "-" + date_parts[0].zfill(2) + "-" + date_parts[1].zfill(2) #yyyy-mm-dd
    if ("Licences" in raw_record):
      licence_record['jurisdiction_classification'].append(raw_record['Licences'])
    if ('Number of License' in raw_record):
      licence_record['licence_number'] = raw_record['Number of License']
    if ("License: Reg.\u2116, Date of Granting" in raw_record):
      licence_record['licence_number'] = raw_record['License: Reg.\u2116, Date of Granting']

  #fourth type 
  if (raw_record['category'] == "Microfinancial organisation"):
    if ('Inclusion date in register' in raw_record):
      date_string = raw_record['Inclusion date in register']
      if (is_number(date_string)):
        date_number = float(date_string)
        new_date = datetime.date(1900, 1, 1) + datetime.timedelta(date_number)
        licence_record['start_date'] = new_date.isoformat()
      else: #have mm.dd.yyyy format (seen 02.19.2014 example)
        date_parts = date_string.split(".")
        licence_record['start_date'] = date_parts[2] + "-" + date_parts[0].zfill(2) + "-" + date_parts[1].zfill(2)
    if ('\u2116 in register ofthe territorial branches of NBK' in raw_record):
      licence_record['licence_number'] = raw_record['\u2116 in register ofthe territorial branches of NBK']

  #type five
  if (raw_record['category'] == "Securities market activity"):
    licence_types = ['Brokers -Dealers  (I category)', 'Brokers \u2013 Dealers (II category)', 'IPM', 'IMPAO', 'RFCA Participants', 'Transfer-Agents', 'The Stock Exchange', '\u0421learing activities to transactions in financial instruments in the securities market', 'Organizations, Engaged in Certain Types of Banking Operations']
    for licence_type in licence_types:
      if (licence_type in raw_record):
        licence_record['jurisdiction_classification'].append(licence_type)

  #type six
  if (raw_record['category'] == 'Attraction of pension contributions and making pension payments'):
    licence_types = ['License: Number of Reg., Date of Granting - Securities Market - Investment Management of Pension Assets', 'License: Number of Reg., Date of Granting - APF', 'License: Number of Reg., Date of Granting - Securities Market - Brokers \u2013 Dealers (II category)']
    for licence_type in licence_types:
      if (licence_type in raw_record):
        type_string = licence_type.split(" - ")[-1]
        licence_record['jurisdiction_classification'].append(type_string)

  #type seven
  if (raw_record['category'] == "Credit bureau activity"):
    if ('Number of License' in raw_record):
      licence_record['licence_number'] = raw_record['Number of License']

  #output the result
  print json.dumps(licence_record)