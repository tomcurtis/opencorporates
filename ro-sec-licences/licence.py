# -*- coding: utf-8 -*-

import sys
import json

#these record how to treat each category of item
all_domestic_categories = [
  "SSIF", #Investment Firms in Romania
  "INCR", #Credit Institutions
  "CIPJ", #Investment Advisers legal persons
  "SAIR", #Investment Management Companies in Romania
  "FDIR", #Open-end Investment Funds in Romania
  "SINR", #Investment Companies in Romania
  "FIIRS", #Closed-end investment funds in Romania supervised by FSA
  "SIIRS", #Closed-end investment companies in Romania supervised by FSA
  "DEPR", #Depositaries in Romania
  "OPRO", #Market Operators in Romania
  "OSRO", #System Operators in Romania
  "ASPJ", #Special Administrators legal persons
  "LIPJ", #Liquidators legal persons
  "EVPJ", #Evaluators/Independent experts legal persons - specialisation: Evaluation of undertakings
  "EIPJ", #Evaluators/Independent experts legal persons - specialisation: Real estate
  "ICPJ", #Qualified Investors legal persons
  "CCCC", #Clearing Houses/Central Counterparties
  "DPCN"  #Central Depositary
]

overseas_in_romania_categories = [
  "FISM", #The equivalent of Investment Firms, authorised by Competent Authorities in Member States
  "INCM", #The equivalent of Credit Institutions, authorised by Competent Authorities in Member States
  "ICSM", #Credit institutions of Member States pursuing activity in Romania directly
  "SAIM", #Investment Management Companies in Member States
  "FDIN", #Open-end Investment Funds in non-Member States
  "FDNA", #Open-end Investment Funds in other Member States not harmonised with European directives
  "SISN", #Investment Companies in non-Member States
  "SISA", #Investment Companies in other Member States harmonised with European directives
  "SISM", #Investment Companies in other Member States not harmonised with European directives
  "AFIASMD", #Alternative investment fund managers in other Member States pursuing activity in Romania directly
  "FIAM", #Alternative Investment Funds in other Member States
  "SIAM", #Alternative Investment Companies in other Member States
  "OPSM", #Market operators of Member States /entities assimilated thereto
  "OSSM", #System operators of Member States /entities assimilated thereto
]

romanian_branch_of_overseas_categories = [
  "SFIM", #Branches of Investment firms in Member States
  "SFIN", #Branches of Investment firms in non-Member States
  "SICN", #Branches of credit institutions in non-Member States
  "SICM", #Branches of credit institutions in Member States
  "SSAM", #Branches of investment management companies in Member States
  "AFIASMS", #Branches of Alternative investment fund managers in other Member States pursuing activity in Romania through branches
]

#not included as these relate to individuals, not companies or where there was no data
ignored_categories = [
  "ASIF", #Financial Investment Services Agents
  "ADEL", #Tied Agents
  "AOIS", #Agents representing the interests of holders of mortgage bonds/securitised financial instruments
  "ADIS", #Distribution agents of investment management companies (SAI)
  "TRAD", #Traders
  "CIPF", #Investment Advisers natural persons
  "SSAN", #Branches of investment management companies in non-Member States
  "FDIN", #Open-end Investment Funds in non-Member States
  "FIIRN", #Closed-end investment funds in Romania not supervised by FSA
  "SIIRN", #Closed-end investment companies in Romania not supervised by FSA
  "FIAN", #Alternative Investment Funds in non-Member States
  "SIAN", #Alternative Investment Companies in non-Member States
  "SICD", #Branches of credit institutions of other Member States licensed by NSC as Depositaries
  "OPSN", #Market operators of non-Member States /entities assimilated thereto
  "OSSN", #System operators of non-Member States /entities assimilated thereto
  "RCCI", #Representatives of the internal control compartment
  "RCCO", #Representatives of the compliance department
  "ASPF", #Special Administrators natural persons
  "LIPF", #Liquidators natural persons
  "EVPF", #Evaluators/Independent experts natural persons - specialisation: Evaluation of undertakings
  "EIPF", #Evaluators/Independent experts natural persons - specialisation: Real estate
  "ICPF", #Qualified Investors natural persons
  "OINR", #Independent Operators (SSIF) in Romania
  "OISM", #Independent Operators (INCR) in Member States
  "AGRT", #Rating Agencies
  "VISS", #Securitisation companies
  "VIFS", #Securitisation funds
  "SAVI", #Special purpose vehicle management companies
  "AITR", #IT System Auditors natural persons in Romania
  "AITS"  #IT System Auditors natural persons in Member States
]

#translate name to English, or town to country
countries = {
  'MAREA BRITANIE': "United Kingdom",
  'CEHIA': "Czech Republic",
  'GRECIA': "Greece",
  'OLANDA': "Netherlands",
  'BULGARIA': "Bulgaria",
  'GERMANIA': "Germany",
  'CIPRU': "Cyprus",
  'NORVEGIA': "Norway",
  'IRLANDA': "Ireland",
  'DANEMARCA': "Denmark",
  'SLOVACIA': "Slovakia",
  'FINLANDA': "Finland",
  'FRANTA': "France",
  'POLONIA': "Poland",
  'GIBRALTAR': "Gibraltar",
  'LUXEMBURG': "Luxembourg",
  'AUSTRIA': "Austria",
  'ITALIA': "Italy",
  'MALTA': "Malta",
  'ESTONIA': "Estonia",
  'BELGIA': "Belgium",
  'SPANIA': "Spain",
  'LETONIA': "Latvia",
  'UNGARIA': "Hungary",
  'SUEDIA': "Sweden",
  'LIECHTENSTEIN': "Liechtenstein",
  'LONDRA': "United Kingdom",
  'VIENA': "Austria",
  'FRANKFURT AM MAIN': "Germany"
}

while True:
  line = sys.stdin.readline()
  if not line:
    break
  raw_record = json.loads(line)
  category = raw_record['category']['symbol']

  #Wholly domestic - everything is Romanian
  if (category in all_domestic_categories):
    record = {
      'source_url': raw_record['source_url'],
      'company_name': raw_record['company_name'],
      'sample_date': raw_record['sample_date'],
      'company_jurisdiction': 'Romania',
      'licence_jurisdiction': 'Romania',
      'licence_number': raw_record['Registry no.'],
      'confidence': 'MEDIUM',
      'regulator': 'Financial Supervisory Authority, Romania',
      'category': 'Financial',
      'jurisdiction_classification': raw_record['category']['name']
    }
    print(json.dumps(record))

  #Foreigners over here
  if (category in overseas_in_romania_categories):
    #will translate countries later
    country = None
    if 'Country' in raw_record:
      country = raw_record['Country']
    elif 'Home member state' in raw_record:
      country = raw_record['Home member state']
    elif 'Town/county' in raw_record:
      country = raw_record['Town/county'] #if there's not too many of these, we can also translate back to country

    if (country != None):
      country = countries[country]
      #sometimes it's not stated, so override only when you can
      regulator = "Unknown"
      if ('Competent authority' in raw_record):
        regulator = raw_record['Competent authority']

      record = {
        'source_url': raw_record['source_url'],
        'company_name': raw_record['company_name'],
        'sample_date': raw_record['sample_date'],
        'company_jurisdiction': country,
        'licence_jurisdiction': "Romania",
        'licence_number': raw_record['Registry no.'],
        'confidence': 'MEDIUM',
        'regulator': regulator,
        'category': 'Financial',
        'jurisdiction_classification': raw_record['category']['name']
      }
      print(json.dumps(record))

  #Branches in Romania of foreign companies - Romanian entity but regulated overseas
  if (category in romanian_branch_of_overseas_categories):
    #sometimes it's not stated, so override only when you can
    regulator = "Unknown"
    if ('Competent authority' in raw_record):
      regulator = raw_record['Competent authority']

    record = {
      'source_url': raw_record['source_url'],
      'company_name': raw_record['company_name'],
      'sample_date': raw_record['sample_date'],
      'company_jurisdiction': 'Romania',
      'licence_jurisdiction': 'Romania',
      'licence_number': raw_record['Registry no.'],
      'confidence': 'MEDIUM',
      'regulator': regulator,
      'category': 'Financial',
      'jurisdiction_classification': raw_record['category']['name']
    }
    print(json.dumps(record))