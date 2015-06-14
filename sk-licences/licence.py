import sys
import json

while True:
  line = sys.stdin.readline()
  if not line:
    break
  raw_record = json.loads(line)

  #some fields change depending on the source page
  licence_jurisdiction = ""
  company_jurisdiction = ""
  regulator = ""
  licence_number = ""
  start_date = ""
  end_date = ""

  all_slovak_sources = [
  "http://www.nbs.sk/en/financial-market-supervision/banking-sector-supervision/List-of-credit-institutions/commercial-and-savings-banks",
  "http://www.nbs.sk/en/financial-market-supervision/banking-sector-supervision/List-of-credit-institutions/branch-offices-of-foreign-banks/banks",
  "http://www.nbs.sk/en/financial-market-supervision/banking-sector-supervision/List-of-credit-institutions/branch-offices-of-foreign-banks/credit-cooperatives",
  "http://www.nbs.sk/en/financial-market-supervision/banking-sector-supervision/List-of-credit-institutions/representative-offices-of-foreign-banks-in-the-slovak-republic",
  "http://www.nbs.sk/en/financial-market-supervision/banking-sector-supervision/List-of-credit-institutions/representative-offices-of-slovak-banks-abroad",
  "http://www.nbs.sk/en/financial-market-supervision/securities-market-supervision/collective-investment/list-of-supervised-entities/list-of-foreign-management-company-operating-through-branch-under-article-75-aoci",
  "http://www.nbs.sk/en/financial-market-supervision/securities-market-supervision/collective-investment/list-of-supervised-entities/list-of-compulsory-administrators",
  "http://www.nbs.sk/en/financial-market-supervision/banking-sector-supervision/List-of-credit-institutions/branch-offices-of-slovak-banks-operating-abroad",
  "http://www.nbs.sk/en/financial-market-supervision/payment-institutions-supervision/list-of-payment-institutions/payment-institutions-with-its-registered-office-in-the-territory-of-the-slovak-republic",
  "http://www.nbs.sk/en/financial-market-supervision/payment-institutions-supervision/list-of-payment-institutions/branch-offices-of-slovak-payment-institutions-operating-abroad",
  "http://www.nbs.sk/en/financial-market-supervision/insurance-supervision/actuaries/list-of-actuaries",
  "http://www.nbs.sk/en/financial-market-supervision/pension-saving-supervision/old-age-pension-saving-system/list-of-pension-asset-management-companies",
  "http://www.nbs.sk/en/financial-market-supervision/pension-saving-supervision/supplementary-pension-saving-system/list-of-supplementary-pension-asset-management-companies",
  "http://www.nbs.sk/en/financial-market-supervision/securities-market-supervision/securities-issuers/stock-issuers/main-listed-market",
  "http://www.nbs.sk/en/financial-market-supervision/securities-market-supervision/securities-issuers/stock-issuers/parallel-listed-market",
  "http://www.nbs.sk/en/financial-market-supervision/securities-market-supervision/securities-issuers/stock-issuers/regulated-free-market",
  "http://www.nbs.sk/en/financial-market-supervision/securities-market-supervision/securities-issuers/bond-issuers/main-listed-market",
  "http://www.nbs.sk/en/financial-market-supervision/securities-market-supervision/securities-issuers/bond-issuers/parallel-listed-market",
  "http://www.nbs.sk/en/financial-market-supervision/securities-market-supervision/securities-issuers/bond-issuers/regulated-free",
  "http://www.nbs.sk/en/financial-market-supervision/securities-market-supervision/securities-issuers/bond-issues-under-art-114-paragraph-2-of-the-act-on-collective-investment",
  "http://www.nbs.sk/en/financial-market-supervision/securities-market-supervision/collective-investment/list-of-depositories1",
  "http://www.nbs.sk/en/financial-market-supervision/securities-market-supervision/investment-firms/list-of-supervised-entities/566",
  ]

  all_slovak_scopes = [
  "Commercial and Savings Banks in Slovakia",
  "Branch offices of Foreign Banks in Slovakia",
  "Domestic management companies and their mutual funds",
  "Branch offices of Foreign Credit Cooperatives in Slovakia",
  "Branch offices of Slovak Banks operating abroad",
  ]

  slovak_abroad_sources = [
  "http://www.nbs.sk/en/financial-market-supervision/banking-sector-supervision/List-of-credit-institutions/slovak-banks-providers-of-services-on-the-cross-border-basis-abroad",
  "http://www.nbs.sk/en/financial-market-supervision/insurance-supervision/list-of-insurance-companies/ic-with-head-office-in-sr/ic-with-head-office-in-sr-providing-activitie-in-another-member-state/through-its-branch-office",
  "http://www.nbs.sk/en/financial-market-supervision/securities-market-supervision/investment-firms/list-of-supervised-entities/ocp/iIF-without-branch",
  "http://www.nbs.sk/en/financial-market-supervision/securities-market-supervision/investment-firms/list-of-supervised-entities/ocp/investment-firms-providing-services-abroad-through-branch",
  ]

  revoked_sources = [
  "http://www.nbs.sk/en/financial-market-supervision/banking-sector-supervision/List-of-credit-institutions/banks-in-special-proceedings",
  "http://www.nbs.sk/en/financial-market-supervision/electronic-money-institutions-supervision/list-of-electronic-money-institutions/ceased-licence",
  "http://www.nbs.sk/en/financial-market-supervision/securities-market-supervision/collective-investment/list-of-supervised-entities/list-of-expired-licences",
  "http://www.nbs.sk/en/financial-market-supervision/payment-institutions-supervision/list-of-payment-institutions/ceased-licences",
  "http://www.nbs.sk/en/financial-market-supervision/insurance-supervision/list-of-insurance-companies/ic-with-head-office-in-sr/insurance-companies-that-quit-their-activity",
  "http://www.nbs.sk/en/financial-market-supervision/securities-market-supervision/investment-firms/list-of-supervised-entities/announcement-about-withdrawal-of-licence",
  ]

  non_licences = [
    "Stock issuers on the parallel listed market",
    "Stock issuers on the main listed market",
    "Stock issuers on the regulated free market",
    "Bond issuers under Article 210 paragraph 2 of the Act No 203/2011 Coll. on collective investment",
    "Bond issuers on the regulated free market",
    "Bond issuers on the main listed market",
    "Bond issuers on the parallel listed market"
  ]

  if ((raw_record['source_url'] in all_slovak_sources) or (raw_record['scope'] in all_slovak_scopes)):
    licence_jurisdiction = "Slovakia"
    company_jurisdiction = "Slovakia"
    regulator = "National Bank of Slovakia"
    if ('commenced_operation' in raw_record):
      start_date = raw_record['commenced_operation']
    elif ('date_of_registration' in raw_record):
      start_date = raw_record['date_of_registration']
    elif ('date_of_validity' in raw_record):
      start_date = raw_record['date_of_validity']
    elif ('licence_validity_date' in raw_record):
      start_date = raw_record['licence_validity_date']
    elif ('date_of_licence_issue' in raw_record):
      start_date = raw_record['date_of_licence_issue']
    elif ('licence_valid_from' in raw_record):
      start_date = raw_record['licence_valid_from']
    elif ('date_of_final_decision' in raw_record):
      start_date = raw_record['date_of_final_decision']
    if ('licence_number' in raw_record):
      licence_number = raw_record['licence_number']
    elif ('number_of_licence' in raw_record):
      licence_number = raw_record['number_of_licence']
    status = "Current"

  if (raw_record['source_url'] in slovak_abroad_sources):
    if ('country' in raw_record):
      licence_jurisdiction = raw_record['country']
    elif ('member_state_of_eu' in raw_record):
      licence_jurisdiction = raw_record['member_state_of_eu']
    company_jurisdiction = "Slovakia"
    if ('member_state,_in_which_the_insurance_company_intends_to_provide_activity' in raw_record):
      company_jurisdiction = raw_record['member_state,_in_which_the_insurance_company_intends_to_provide_activity']
    regulator = "National Bank of Slovakia"
    if ('supervisory_authority_of_eu_member_state' in raw_record):
      regulator = raw_record['supervisory_authority_of_eu_member_state']
    elif ('supervisory_authority' in raw_record):
      regulator = raw_record['supervisory_authority']
    if ('date_of_registration' in raw_record):
      start_date = raw_record['date_of_registration']
    elif ("date_of_notification's_delivery_to_the_member_state" in raw_record):
      start_date = raw_record["date_of_notification's_delivery_to_the_member_state"]
    status = "Current"

  if (raw_record['source_url'] in revoked_sources):
    licence_jurisdiction = "Slovakia"
    company_jurisdiction = "Slovakia"
    regulator = "National Bank of Slovakia"
    status = "Revoked"
    if ('commenced_operation' in raw_record):
      start_date = raw_record['commenced_operation']
    elif ('licence_validity_date' in raw_record):
      start_date = raw_record['licence_validity_date']
    if ('termination_of_the_licence' in raw_record):
      end_date = raw_record['termination_of_the_licence']
    elif("bank's_licence_revoked" in raw_record):
      end_date = raw_record["bank's_licence_revoked"]
    elif('expiry_date' in raw_record):
      end_date = raw_record['expiry_date']
    elif('licence_ceased' in raw_record):
      end_date = raw_record['licence_ceased']
    elif('effective_as_of' in raw_record):
      end_date = raw_record['effective_as_of']
    if ('licence_number' in raw_record):
      licence_number = raw_record['licence_number']

  #skip any empties
  if ((len(licence_jurisdiction) == 0) or (len(company_jurisdiction) == 0)):
    continue

  #skip certain types of primary data which doesn't relate to licences
  if (raw_record['scope'] in non_licences):
    continue

  #make a licence
  licence_record = {
    "source_url": raw_record['source_url'],
    "company_name": raw_record['name'],
    "company_jurisdiction": str(company_jurisdiction),
    "licence_jurisdiction": str(licence_jurisdiction),
    "category": "Financial",
    "regulator": str(regulator),
    "jurisdiction_classification": raw_record['scope'],
    "sample_date": raw_record['sample_date'],
  }

  #add optional fields if appropriate
  if (len(str(licence_number)) > 0):
    licence_record['licence_number'] = str(licence_number)
  if (len(str(start_date)) > 0):
    licence_record['start_date'] = str(start_date)
  if (len(str(end_date)) > 0):
    licence_record['end_date'] = str(end_date)

  #output the result
  print json.dumps(licence_record)