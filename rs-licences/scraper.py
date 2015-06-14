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

#return a list of entity codes to be reviewed
def parse_entity_list(parsed_page):
	#identify where the table of entities begins based on finding the right heading cell	
	header_cells = parsed_page.find_all(attrs={'class': 'tableheader'}) + parsed_page.find_all(attrs={'class': 'regheader'})
	key_header = None
	for header in header_cells:
		if (header.string.strip() == "Name"):
			key_header = header
			break
	if (key_header == None):
		return [] #error encountered - no entities found
	else:
		entity_table = key_header.parent.parent

	#now go through the rows and get the code from the url
	code_list = [] #output
	tr_list = entity_table.find_all("tr")
	for tr in tr_list[1:]:
		td_list = tr.find_all("td")
		link = td_list[0].a['href']
		code = link[link.find("?cod=") + 5:]
		if (code not in code_list):
			code_list.append(code)
	return code_list

#Lists of entities to be processed
entity_lists = [
	{'url': "http://www.nbs.rs/static/nbs_site/gen/english/50/banks/50b1_en.htm", 'category': "Bank", 'basehref': "http://www.nbs.rs/static/nbs_site/gen/english/50/banks/"},
	{'url': "http://www.nbs.rs/static/nbs_site/gen/english/60/60b1_en.htm", 'category': "Insurance company", 'basehref': "http://www.nbs.rs/static/nbs_site/gen/english/60/"},
	{'url': "http://www.nbs.rs/static/nbs_site/gen/english/50/penfunds/VPFCompanies_eng.htm", 'category': "Voluntary pension funds management company", 'basehref': "http://www.nbs.rs/static/nbs_site/gen/english/50/penfunds/"},
	{'url': "http://www.nbs.rs/static/nbs_site/gen/english/50/leasing/SpisakLizing_eng.htm", 'category': 'Lessor', 'basehref': "http://www.nbs.rs/static/nbs_site/gen/english/50/leasing/"},
	{'url': "http://www.nbs.rs/static/nbs_site/gen/english/50/50b3_en.htm", 'category': "Bank authorised for performing international operations", 'basehref': None},
	{'url': "http://www.nbs.rs/internet/english/50/50_2/index.html", 'category': "Representative office of foreign bank in Serbia", 'basehref': None},
	{'url': "http://www.nbs.rs/static/nbs_site/gen/english/60/60b3_en.htm", 'category': "Insurance brokerage company, insurance agency company or agency or business unit for the provision of other insurance services", 'basehref': None},
	{'url': "http://www.nbs.rs/static/nbs_site/gen/english/60/preduzetnici.htm", 'category': "Insurance agent licensed to engage in insurance agency activities", 'basehref': None},
	{'url': "http://www.nbs.rs/static/nbs_site/gen/english/60/60b4_en.htm", 'category': "Agency or outlet whose operating licence has been revoked", 'basehref': None},
	{'url': "http://www.nbs.rs/static/nbs_site/gen/english/60/tagencije.htm", 'category': "Legal entity in charge of insurance agency and brokerage pursuant to special law", 'basehref': None}
]

#translation
countries = {
	'MOSKVA': "Russia",
	'PODGORICA': "Montenegro",
	'SOUTH DAKOTA': "South Dakota",
	'FRANKFURT/MAIN': "Germany",
	'SKOPJE': "Republic of Macedonia"
}

#get going
sample_date = str(date.today())
turbotlib.log("Starting run on " + sample_date) # Optional debug logging

#Step 1: load page for each category to identify who needs looking at
for entity_list in entity_lists:
	#monitor progress
	list_count = entity_lists.index(entity_list) + 1
	turbotlib.log("Starting category " + str(list_count) + "/" + str(len(entity_lists)))

	#load page
	list_page = get_doc(entity_list['url'])
	list_table = list_page.table
	
	#first off, if this category doesn't have links on its front page, there's nothing more to do
	if (entity_list['basehref'] == None):
		#deal with one weird template first
		if (entity_list['category'] == "Legal entity in charge of insurance agency and brokerage pursuant to special law"):
			#make list of rows with headings then work out where info is in relation to that
			tr_list = list_table.find_all("tr")
			header_rows = []
			for tr in tr_list:
				th_list = tr.find_all("th")
				if (len(th_list) > 0):
					header_rows.append(tr_list.index(tr))
			for header in header_rows:
				added_info = False
				output = {
					'sample_date': sample_date,
					'source_url': entity_list['url'],
					'source': "National Bank of Serbia",
					'category': entity_list['category']
				}

				#get name from header
				tr = tr_list[header]
				name = tr.th.text.strip().replace("\n", "").replace("\t", "")
				name = name[name.find(".") + 4:]
				if (len(name) > 0):
					output['name'] = name
					added_info = True

				#address is two rows below header, first cell.
				first_row = tr_list[header + 2].find_all("td")
				address = first_row[0].text.strip()
				if (len(address) > 0):
					output['address'] = address
					added_info = True
				
				#phone number is one cell over
				phone = first_row[1].text.strip()
				if (len(phone) > 0):
					output['phone'] = phone
					added_info = True

				#operations and fax number two rows below that
				second_row = tr_list[header + 4].find_all("td")
				operations = second_row[0].text.strip()
				if (len(operations) > 0):
					output["Types of insurance operations"] = operations
					added_info = True
				
				#fax is one cell over
				fax = second_row[1].text.strip()
				if (len(fax) > 0):
					output['fax'] = fax
					added_info = True

				if (added_info):
					print(json.dumps(output))
				
		else: #other categories are easier
			if (entity_list['category'] == "Representative office of foreign bank in Serbia"):
				entity_table = list_page.find(attrs={'class': 'confTable'})

			else:
				entity_table = list_table
			
			#once you have the right table, the work is much the same for each category
			output = {}
			for tr in entity_table.find_all("tr"):
				#check if it's a header - if so, new entity
				th_list = tr.find_all("th")
				td_list = tr.find_all("td")
				if (len(th_list) > 0):
					#first off print the existing entry if you added anything to it
					if ((len(output) > 5) and ('name' in output)):
						if (output['category'] == "Agency or outlet whose operating licence has been revoked"):
							output['status'] = "Revoked"
						print(json.dumps(output))

					#now start on the new one
					output = {
						'sample_date': sample_date,
						'source_url': entity_list['url'],
						'source': "National Bank of Serbia",
						'category': entity_list['category']
					}

					th_string = th_list[0].text.strip().replace("\n", "",).replace("\t", "")
					name_start = th_string.find(".  ")
					name = th_string[name_start + 5:].strip()
					if (len(name) > 0):
						output['name'] = name

					#deal with countries for international entities using a lookup
					if (entity_list['category'] == "Representative office of foreign bank in Serbia"):
						if ("," in name):
							country_name = name[name.find(",") + 2:]
						else:
							country_name_split = name.split()
							country_name = country_name_split[-1]
						output['country'] = countries[country_name]
				
				#add normal details to the current entity
				elif (len(td_list) == 2):
					label = td_list[0].text.strip().replace(":", "")
					value = td_list[1].text.strip()
					if ((len(value) > 0) and (value != "-")):
						if (label == "Web site"):
							output['url'] = "http://" + value
						else:
							output[label] = value
							if ("licence expired" in value):
								output['status'] = "Expired"

			#once done with last row, don't forget to print if we added info
			if ((len(output) > 5) and ('name' in output)):
				if (output['category'] == "Agency or outlet whose operating licence has been revoked"):
					output['status'] = "Revoked"
				print(json.dumps(output))

	#otherwise, step 2: load the details page and scrape that
	else:
		links_list = list_table.find_all("a")
		for link in links_list:
			detail_url = entity_list['basehref'] + link['href']
			detail_page = get_doc(detail_url)

			#make object to represent what we found
			added_info = False
			output = {
				'sample_date': sample_date,
				'source': "National Bank of Serbia",
				'category': entity_list['category'],
				'source_url': detail_url
			}

			#how to parse will depend on the category
			if (entity_list['category'] == "Bank"):
				table_list = detail_page.find_all("table")
				
				#name + other first details
				name = detail_page.h2.text.strip()
				if (len(name) > 0):
					output['name'] = name
					added_info = True
				address = detail_page.h2.next_sibling.strip().replace("\n", "").replace("  ", "").replace("\t", "")
				if (len(address) > 0):
					output['address'] = address
					added_info = True
				#org structure in first link
				org_structure_link = "http://www.nbs.rs/static/nbs_site/gen/" + table_list[0].a['href'].replace("../", "")
				if (len(org_structure_link) > len("http://www.nbs.rs/static/nbs_site/gen/")):
					output['organisational_structure_url'] = org_structure_link
					added_info = True

				#remaining core details from first table
				tr_list = table_list[1].find_all("tr")
				for tr in tr_list:
					td_list = tr.find_all("th") + tr.find_all("td")
					if (len(td_list) == 2):
						label = td_list[0].text.strip().replace(":", "")
						value = td_list[1].text.strip()

						#deal with special cases
						if (label == "www"):
							href = td_list[1].a['href']
							output['url'] = href
							added_info = True

						elif ((len(value) > 0) and (value != "-")):
							output[label] = value
							added_info = True

					#balance sheet and income statement
					elif (len(td_list) == 1):
						accounts_url = "http://www.nbs.rs/static/nbs_site/gen/" + td_list[0].a['href'].replace("../", "")
						if (len(accounts_url) > len("http://www.nbs.rs/static/nbs_site/gen/")):
							output['accounts_url'] = accounts_url
							added_info = True

				#shareholders come next
				shareholders = []
				tr_list = table_list[2].find_all("tr")
				for tr in tr_list[1:]:
					td_list = tr.find_all("td")
					if (len(td_list) == 2):
						shareholder_name = td_list[0].text.strip()
						voting_rights = td_list[1].text.strip()
						if (len(shareholder_name) > 0):
							shareholder = {
								'name': shareholder_name,
								'voting_rights': voting_rights
							}
							shareholders.append(shareholder)
				if (len(shareholders) > 0):
					output['shareholders'] = shareholders
					added_info = True

				#followed by directors in different format from before
				directors = []
				tr_list = table_list[3].find_all("tr")
				headings = ["Management Board", "Executive Board"]
				for tr in tr_list[1:]:
					td_count = 0
					td_list = tr.find_all("td")
					special_role = ""
					for td in td_list:
						value = td.text.strip()
						if ("," in value):
							role_start = value.find(",")
							special_role = value[role_start + 1:].strip()
							value = value[:role_start]
						role = headings[td_count]

						#actually store the result
						if ((role != None) and (len(value) > 0)):
							director = {
								'member_of': role,
								'name': value
							}
							if (len(special_role) > 0):
								director['role'] = special_role

							directors.append(director)

						td_count += 1
					if (len(directors) > 0):
						output['directors'] = directors
						added_info = True

			if (entity_list['category'] == "Insurance company"):
				#core details are in the first table
				table_list = detail_page.find_all("table")
				core_table = table_list[0]
				tr_list = core_table.find_all("tr")
				
				#weird rows at the top
				name = tr_list[0].th.text.strip()
				if (len(name) > 0):
					output['name'] = name
					added_info = True
				insurance_types = tr_list[1].td.text.strip()[31:]
				if (len(insurance_types) > 0):
					output['Types of insurance operations'] = insurance_types
					added_info = True

				#all remainder rows are label:value
				for tr in tr_list[2:]:
					td_list = tr.find_all("th") + tr.find_all("td")
					label = td_list[0].text.strip().replace(":", "")
					value = td_list[1].text.strip()

					#deal with special cases
					if (label == "WWW"):
						href = td_list[1].a['href']
						output['url'] = href
						added_info = True

					elif (len(value) > 0):
						output[label] = value
						added_info = True

				#second table is shareholding
				tr_list = table_list[1].find_all("tr")
				shareholders = []
				for tr in tr_list[1:]:
					td_list = tr.find_all("td")
					shareholder_name = td_list[0].text.strip()
					shareholding = td_list[1].text.strip()
					#ignore total line - it just duplicates what was already there
					if ((shareholder_name != "Share capital") and (len(shareholder_name) > 0)):
							shareholder = {
								'name': shareholder_name,
								'shareholding': shareholding
							}
							shareholders.append(shareholder)
				if (len(shareholders) > 0):
					output['shareholders'] = shareholders
					added_info = True

			if (entity_list['category'] == "Voluntary pension funds management company"):
				#core details
				name = detail_page.h2.text.strip()
				if (len(name) > 0):
					output['name'] = name
					added_info = True
				address = detail_page.h2.next_sibling.strip().replace("\n", "").replace("  ", "").replace("\t", "")
				if (len(address) > 0):
					output['address'] = address
					added_info = True
			
				#get remaining details. First table is overall layout. Second is label:value pairs. Remainder is to be added as a list
				tables_list = detail_page.find_all("table")
				tr_list = tables_list[1].find_all("tr")
				for tr in tr_list:
					td_list = tr.find_all("th") + tr.find_all("td")
					if (len(td_list) == 2):
						label = td_list[0].text.strip().replace(":", "")
						value = td_list[1].text.strip()
						
						#deal with special cases
						if (label == "WWW"):
							href = td_list[1].a['href']
							output['url'] = href
							added_info = True

						elif (label == "Appendices"):
							opinions = [] #make a list of these links
							for a in td_list[1].find_all("a"):
								href = "http://www.nbs.rs/static/nbs_site/gen/" + a['href'].replace("../", "")
								text = a.text.strip()
								opinion = {'date': text, 'url': href}
								opinions.append(opinion)
							if (len(opinions) > 0):
								output["Auditor's opinion and balance sheets"] = opinions
								added_info = True

						elif ((len(value) > 0) and (value != "-")):
							output[label] = value
							added_info = True

					#only lists of funds
					if (len(td_list) == 1):
						funds_link = entity_list['basehref'] + "vpfids/" + td_list[0].a['href']
						output['List of funds'] = funds_link

				#governing bodies is next
				governors = []
				current_role = None
				tr_list = tables_list[2].find_all("tr")
				for tr in tr_list[1:]:
					#this is the sign of a role rather than a name
					text = tr.td.text.strip()
					if (":" in text):
						current_role = text
					else:
						if ((current_role != None) and (len(text) > 0)):
							governor = {'role': current_role, 'name': text}
							governors.append(governor)
				if (len(governors) > 0):
					output['govenors'] = governors
					added_info = True

				#and then shareholders
				shareholders = []
				tr_list = tables_list[3].find_all("tr")
				for tr in tr_list[1:]:
					td_list = tr.find_all("td")
					shareholder = td_list[0].text.strip()
					shareholding = td_list[1].text.strip()
					if ((len(shareholder) > 0) and (len(shareholding) > 0)):
						shareholder = {'name': shareholder, 'shareholding': shareholding}
						shareholders.append(shareholder)
				if (len(shareholders) > 0):
					output['shareholders'] = shareholders
					added_info = True
				

			if (entity_list['category'] == "Lessor"):
				#core details
				name = detail_page.h2.text.strip()
				if (len(name) > 0):
					output['name'] = name
					added_info = True
				address_part_one = detail_page.h2.next_sibling.strip() #first line
				address_part_two = detail_page.h2.next_sibling.next_sibling.next_sibling.strip() #second line, after <br>
				address = (address_part_one + ", " + address_part_two).replace("\n", "").replace("  ", "").replace("\t", "")
				if (len(address) > 0):
					output['address'] = address
					added_info = True

				#main details (as for vfps)
				tables_list = detail_page.find_all("table")
				tr_list = tables_list[1].find_all("tr")
				for tr in tr_list:
					td_list = tr.find_all("th") + tr.find_all("td")
					if (len(td_list) == 2):
						label = td_list[0].text.strip().replace(":", "")
						value = td_list[1].text.strip()
						
						#deal with special cases
						if (label == "WWW"):
							href = td_list[1].a['href']
							output['url'] = href
							added_info = True

						elif ((len(value) > 0) and (value != "-")):
							output[label] = value
							added_info = True

				#foundation - i think this is like shareholding
				foundation = []
				tr_list = tables_list[2].find_all("tr")
				for tr in tr_list[1:]:
					td_list = tr.find_all("td")
					foundation_name = td_list[0].text.strip()
					holding = td_list[1].text.strip()
					if ((len(foundation_name) > 0) and (len(holding) > 0)):
						holder = {'name': foundation_name, 'holding': holding}
						foundation.append(holder)
				if (len(foundation) > 0):
					output['foundation'] = foundation
					added_info = True

				#followed by directors in different format from before
				directors = []
				tr_list = tables_list[3].find_all("tr")
				headings = ["Management Board", "Executive Board"]
				for tr in tr_list[1:]:
					td_count = 0
					td_list = tr.find_all("td")
					special_role = ""
					for td in td_list:
						value = td.text.strip()
						if ("," in value):
							role_start = value.find(",")
							special_role = value[role_start + 1:].strip()
							value = value[:role_start]
						role = headings[td_count]

						#actually store the result
						if ((role != None) and (len(value) > 0)):
							director = {
								'member_of': role,
								'name': value
							}
							if (len(special_role) > 0):
								director['role'] = special_role

							directors.append(director)

						td_count += 1
					if (len(directors) > 0):
						output['directors'] = directors
						added_info = True


			#that's our lot so return a result
			if (added_info):
				print(json.dumps(output))

turbotlib.log("Finished run")