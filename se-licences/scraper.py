# -*- coding: utf-8 -*-

import json
import datetime
from datetime import date
import turbotlib
from bs4 import BeautifulSoup
import bs4
import requests

#FUNCTIONS
#retrieve a document at a given URL as parsed html tree
def get_doc(source_url):
	response = requests.get(source_url)
	html = response.content
	doc = BeautifulSoup(html)
	return doc

#add the value to the object. If there's already a value, then make a list
def add_field(data, label, value):
	if (label in data):
		#check we're not duplicating anything
		if (data[label] != value):
			#if there's already a list, add this to it
			if (isinstance(data[label], list)):
				data[label].append(value)
			#otherwise, have to start a list with the existing value and the new one
			else:
				data[label] = [data[label], value]
	else:
		data[label] = value

#if given a tag. find the next ul and extract names/links
def extract_list(tag):
	results = [] #container
	list_ul = tag.find_next("ul")
	for item in list_ul:
		if (isinstance(item, bs4.Tag)): #get the ones that are actually an li
			try:
				#extract details from link
				item_idx_start = item.a['href'].find("?idx=")
				if (item_idx_start != -1):
					item_idx = item.a['href'][idx_start + 5:].strip()
				item_name = item.a.string.strip()
				
				#make an object and add to the list
				result = {
					'name': item_name,
					'idx': item_idx
				}
				results.append(result)
			except:
				continue
	return results



#get going
sample_date = str(date.today())
turbotlib.log("Starting run on " + sample_date) # Optional debug logging

#Base URLs we will want to use
category_url = "http://www.fi.se/Folder-EN/Startpage/Register/Company-register/Company-register-Company-per-category/?typ='" #need to finish with category and "'"
company_url = "http://www.fi.se/Folder-EN/Startpage/Register/Company-register/Company-register-Details/?idx=" #need to finish with idx number
company_se_url = "http://www.fi.se/Register/Foretagsregistret/Foretagsregistret-Detaljerad-information/?idx=" #need to finish with idx number
overseas_permissions_url = "http://www.fi.se/Register/Foretagsregistret/Foretagsregistret-Gransoverskridande-handel/?idx=" #need to finish with idx number

#keep track of progress
count = 1

#These are the categories of instituion - use these to populate category urls and find the relevant entries
categories = [
	"BANK++", #Banking companies (limited liability company)
	"FILB++", #Foreign branches of Swedish chartered banks
	"MBANK+", #Members-bank
	"SPAR++", #Savings banks
	"UTLBGH", #Foreign bank cross-border business
	"UTLFIL", #Foreign bank branch
	"BET+++", #Payment institution
	"BETREG", #Registered payment firm
	"FILBET", #Foreign branches of a Swedish payment institution
	"OMB+++", #Agent for a payment institution or a registered payment firm
	"OMBUTL", #Foreign agents of Swedish payment institution
	"UTLBEG", #Foreign payment instituion, cross-border
	"UTLBET", #Foreign payment institution
	"UTLBFI", #Foreign branches of payment institution
	"UTLOMB", #Foreign agents of payment institution
	"AUKTMP", #Authorised marketplace
	"BGC+++", #Clearinghouses
	"BORS++", #Securities exchanges
	"MTF+++", #MTF/Operation of Multilateral Trading Facilities
	"REGMND", #Regulated Market
	"VPC+++", #Central securities depositories
	"AIFFOR", #AIF Managers Authorisation
	"AIFREG", #AIF Managers Registration
	"APFOND", #AP Fund
	"FILFO+", #Swedish management companies, branch
	"FOND++", #UCITS I management companies
	"FONDBO", #UCITS III management companies
	"NATION", #National fund
	"SPECFO", #Special fund
	"SYNTFO", #Synthetic mutual fund
	"VPFO++", #UCITS III (mutual funds)
	"VPFOND", #UCITS I (mutual funds)
	"UTF1:6", #Foreign UCITS III management company 1:6
	"UTF1:7", #Foreign UCITS III 1:7
	"UTF1:8", #Foreign non-UCITS management company outside EES 1:8
	"UTF1:9", #Foreign non-UCITS 1:9
	"UTFFIL", #Foreign management company (branch)
	"UTLAIF", #Foreign AIF Managers
	"UTDELF", #Foreign subfund
	"RIKSCA", #Nationwide, non-life captive
	"RIKSLI", #Nationwide, life insurance
	"RIKSSK", #Nationwide, non-life insurance
	"RIKSUL", #Nationwide, unit-linked
	"UNDE++", #Friendly societies
	"UNDEB+", #Friendly societies, restricted supervision
	"KREA++", #Agricultural insurance
	"MLOK++", #Small local insurance company
	"SLOK++", #Medium-size local insurance company
	"UTLFAL", #Foreign insurance company, agency, life
	"UTLFAS", #Foreign insurance company, agency, non-life
	"UTLFFL", #Foreign insurance company branch office, life
	"UTLFFS", #Foreign insurance company branch office, non-life
	"UTLFGL", #Foreign insurance company, cross-border business, life
	"UTLFGS", #Foreign insurance company, cross-border business, non-life
	"UTLFO+", #Association of Underwriters
	"FORSFA", #Insurance mediation
	"FORSFB", #Insurance mediation employees
	"UTLGFB", #Foreign insurance mediation, cross-border business
	"LANHYP", #Landshypotek
	"SKEHYP", #Skeppshypotek
	"STAHYP", #Stadshypotek
	"FILKM+", #Foreign branches of Swedish loan companies
	"KMB+++", #Credit-market company
	"KMF+++", #Credit-market association
	"UTLKGH", #Foreign credit-market company, cross-border business
	"UTLKMF", #Foreign credit-market company, branch office
	"EINST+", #Swedish e-money institution
	"REGUTG", #Swedish registered e-money issuer
	"FILVP+", #Investment firm, foreign branch
	"VARD++", #Investment firms
	"MIFFIL", #Investment firm in EES with branch
	"UTLVGH", #Investment firm in EES with cross-border business
	"UTLVOM", #Investment firm in EES with Swedish tied agent
	"AUKTFI", #Previously licensed financial institution
	"FIINST", #Financial institutions (Only registered not under supervision)
	"INLAN+", #Deposit company (Only registered not under supervision)
	"INLFI+", #Deposit companies with certain financial activity (Only registered not under supervision)
	"STIFT+", #Pension fund
	"UTFMAN", #Foreign management company
	"VPFIL+", #Foreign securities company with Swedish branch office
]

# for category in categories:
for category in categories:
	category_page_url = category_url + category + "'"
	try:
		category_page = get_doc(category_page_url).table
		
		#No table = no results found
		if (category_page == None):
			continue

		#Got some results - first, extract the category title
		category_name_string = category_page.find_next('tr').find_next('tr').td.string
		category_name = category_name_string[:category_name_string.find(":")].strip()
		
		#secondly, compile a list of entities to look for
		category_page_links = category_page.find_all('a')
		category_link_idx = [] #container for id numbers we'll look for
		for link in category_page_links:
			idx_start = link['href'].find('?idx=')
			if (idx_start == -1): #check if this isn't the sort of link we want
				continue
			#we found it, so harvest the link for the next step
			idx_number = link['href'][idx_start + 5:].strip()
			category_link_idx.append(idx_number)

		#now go through the individual pages one-by-one
		for idx in category_link_idx:
			#extract key details from the english version first
			english_url = company_url + idx
			try:
				english_page = get_doc(english_url)
				company_name = english_page.h1.string.strip()
				got_results = False #monitor if we have anything worth returning

				#create an object to output
				output = {
					'sample_date': sample_date,
					'source_url': english_url,
					'name': company_name,
					'source_authority': "Finansinspektionen",
					'idx': idx
				}

				#find the table of details we want
				table_list = english_page.find_all('table')
				for table in table_list:
					h3_table = False
					span_table = False
					if ("class" not in table.attrs):
						continue
					if ("institut-table" in table['class']):
						#look for employees
						h3_list = table.find_all("h3")
						if (len(h3_list) > 0):
							for h3 in h3_list:
								#looking for table of permissions - employees are in both English and Swedish versions
								if (h3.string == u"EMPLOYEES"):
									h3_table = True
									employees = extract_list(h3)

									if (len(employees) > 0):
										add_field(output, "employees", employees)
										got_results = True

								#insurance intermediaries, get them too
								if (h3.string == "INSURANCE INTERMEDIARIES"):
									h3_table = True
									insurance_intermediaries = extract_list(h3)

									if (len(insurance_intermediaries) > 0):
										add_field(output, "insurance_intermediaries", insurance_intermediaries)
										got_results = True

						#look for lists that come before ul of names with links
						span_list = table.find_all("span")
						if (len(span_list) > 0):
							#fund companies
							if (span_list[0].string == "FUND COMPANIES"):
								span_table = True
								fund_companies = extract_list(span_list[0])

								if (len(fund_companies) > 0):
									add_field(output, "fund_companies", fund_companies)
									got_results = True

							#foreign subfunds
							if (span_list[0].string == "FOREIGN SUBFUNDS/FUND COMPANIES"):
								span_table = True
								foreign_subfunds_or_fund_companies = extract_list(span_list[0])

								if (len(foreign_subfunds_or_fund_companies) > 0):
									add_field(output, "foreign_subfunds_or_fund_companies", foreign_subfunds_or_fund_companies)
									got_results = True

							#foreign fund companies
							if (span_list[0].string == "FOREIGN FUND COMPANIES/ ASSET-MANAGEMENT COMPANIES "):
								span_table = True
								foreign_fund_companies_or_asset_management_companies = extract_list(span_list[0])

								if (len(foreign_fund_companies_or_asset_management_companies) > 0):
									add_field(output, "foreign_fund_companies_or_asset_management_companies", foreign_fund_companies_or_asset_management_companies)
									got_results = True

						#now deal with normal table otherwise
						if ((not h3_table) and (not span_table)):
							tr_list = table.find_all('tr')
							for tr in tr_list:
								#looking for the part which is key-value pairs
								td_list = tr.find_all('td')
								if (len(td_list) == 2):
									try:
										label = td_list[0].string.strip().lower().replace(" ", "_") #convert to field name format
										value = td_list[1].contents #need to deal with addreseses which cover multiple lines
									
										#easy ones are fine
										if (len(value) == 1):
											value_string = value[0].strip()

										#complex ones like addresses need handling
										if (len(value) > 1):
											value_string = ""
											for part in value:
												part_word = " ".join(unicode(part).split())
												if ((part_word != "<br/>") and (len(part_word) > 0)):
													value_string = value_string + ", " + part_word
											value_string = value_string[2:].strip()

										#only add on results if we have something to say for them
										if ((len(label) > 0) and (len(value_string) > 0)):
											add_field(output, label, value_string) #append results to the object we're creating
											got_results = True
											
									except:
										continue

					#look for list of funds - special format of table
					if ("trade-list" in table['class']):
						funds = []
						tr_list = table.find_all("tr")
						for tr in tr_list:
							td_list = tr.find_all("td")
							#extract the header row -> tells you fund type
							if ((len(td_list) == 1) and ('header' in td_list[0]['class'])):
								fund_type = td_list[0].string.strip()
							if (len(td_list) == 2):
								#skip the very header row - just name and fi_number (and not always present)
								if ((len(td_list[0].contents) == 1) and (len(td_list[1].contents) == 1)):
									continue
								else:
									try:
										#extract name, idx and fi number
										fund_name_link = td_list[0].contents[1]
										fund_idx_start = fund_name_link['href'].find("?idx=")
										if (fund_idx_start != -1):
											fund_idx = fund_name_link['href'][idx_start + 5:].strip()
										fund_name = fund_name_link.string.strip()
										fund_fi = td_list[1].contents[0]
										
										#make an object, add it to the list
										fund = {
											'name': fund_name,
											'idx': fund_idx,
											'fi_identification_number': fund_fi,
											'type': fund_type
										}
										funds.append(fund)
									except:
										continue

						#add our list to our overall entity record
						if (len(funds) > 0):
							add_field(output, 'funds', funds)
							got_results = True
			except:
				continue

			#now look for further details on Swedish version of the register
			svenska_url = company_se_url + idx
			try:
				svenska_page = get_doc(svenska_url)
				svenska_table_list = svenska_page.find_all("table")
				for table in svenska_table_list:
					if ("class" not in table.attrs):
						continue
					if ("institut-table" in table['class']):
						h3_list = table.find_all("h3")
						if (len(h3_list) > 0):
							for h3 in h3_list:
								#looking for table of permissions - employees are in both English and Swedish versions
								if (h3.string == u"TILLSTÅND"):
									permissions = [] #container
									list_ul = h3.find_next("ul")
									for item in list_ul:
										if (isinstance(item, bs4.Tag)): #get the ones that are actually an li
											try:
												item_string = item.string.strip()
												permission_date = item_string[:10].strip()
												permission_svenska = item_string[11:].strip()
												if ((len(permission_date) > 0) and (len(permission_svenska) > 0)):
													result = {
														'date': permission_date,
														'permission': permission_svenska,
														'country': "Sverige"
													}
													permissions.append(result)
											except:
												continue

									if (len(permissions) > 0):
										add_field(output, "permissions", permissions)
										got_results = True
										if ('source_url_svenska' not in output):
											add_field(output, 'source_url_svenska', svenska_url)

								#for registered (but not necessarily supervised)
								if (h3.string == "REGISTRERAT"):
									registrations = []
									list_ul = h3.find_next("ul")
									for item in list_ul:
										if (isinstance(item, bs4.Tag)): #get the ones that are actually an li
											try:
												item_string = item.string.strip()
												registration_date = item_string[:10].strip()
												registration_svenska = item_string[11:].strip()
												if ((len(registration_date) > 0) and (len(registration_svenska) > 0)):
													result = {
														'date': registration_date,
														'registration': registration_svenska,
														'country': "Sverige"
													}
													registrations.append(result)
											except:
												continue

									if (len(registrations) > 0):
										add_field(output, "registrations", registrations)
										got_results = True
										if ('source_url_svenska' not in output):
											add_field(output, 'source_url_svenska', svenska_url)
						

				#check if we need to look for overseas permissions
				svenska_a_list = svenska_page.find_all("a")
				for item in svenska_a_list:
					if (item.string == u'Se gränsöverskridande handel'):
						svenska_overseas_url = overseas_permissions_url + idx
						try:
							svenska_overseas_page = get_doc(svenska_overseas_url)
							table_list = svenska_overseas_page.find_all("table")
							for table in table_list:
								#look for list of permissions - special format of table
								if ("trade-list" in table['class']):
									overseas_permissions = []
									tr_list = table.find_all("tr")
									for tr in tr_list:
										td_list = tr.find_all("td")
										#extract the header row -> tells you fund type
										if ((len(td_list) == 1) and ('header' in td_list[0]['class'])):
											country_svenska = td_list[0].string.strip().title()

										if (len(td_list) == 2):
											#skip the very header row - just name and fi_number (and not always present)
											if ('textNormal' in tr['class']):
												try:
													#extract date and permission
													permission_date = td_list[0].string.strip()
													permission_svenska = td_list[1].string.strip()

													#make object and add to the list
													if ((len(permission_date) > 0) and (len(permission_svenska) > 0)):
														permission = {
															'date': permission_date,
															'permission': permission_svenska,
															'country': country_svenska
														}
														overseas_permissions.append(permission)
												except:
													continue

									#add our list to our overall entity record
									if (len(overseas_permissions) > 0):
										#add to existing permissions if we have it
										if ('permissions' in output):
											output['permissions'] += overseas_permissions

										else: #otherwise add from scratch
											add_field(output, 'permissions', overseas_permissions)
										got_results = True
						
						except:
							continue

				#if we found anything, output the results
				if (got_results):
					print(json.dumps(output))
					turbotlib.log(str(count) + " " + category + " " + company_name)
					count += 1

			except:
				continue

	except:
		continue