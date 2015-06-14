# -*- coding: utf-8 -*-

#SECTION ONE: OVERALL SET UP AND CONSTANTS

import json
import datetime
from datetime import date
import turbotlib
from bs4 import BeautifulSoup
import bs4
import requests
import urllib

#links to the relevant detail pages we need:
urls = {
	"financial_institution_list": "http://www.bcra.gov.ar/sisfin/sf020101_i.asp?bco=AAA00&tipo=1",
	"financial_institution_main_page": "http://www.bcra.gov.ar/sisfin/sf010100_i.asp?bco=",
	"financial_service_customer_assistance_manager": "http://www.bcra.gov.ar/sisfin/sf010108_i.asp?entidad=",
	"head_management": "http://www.bcra.gov.ar/sisfin/sf010101_i.asp?bco=",
	"shareholders": "http://www.bcra.gov.ar/sisfin/sf010102_i.asp?bco=",
	"auditors": "http://www.bcra.gov.ar/sisfin/sf010103_i.asp?bco=",
	"financial_statements": "http://www.bcra.gov.ar/sisfin/sf010104_i.asp?bco=",
	"debtors_status": "http://www.bcra.gov.ar/sisfin/sf010105_i.asp?bco=",
	"indicators": "http://www.bcra.gov.ar/sisfin/sf010107_i.asp?bco=",
	"structural_information": "http://www.bcra.gov.ar/sisfin/sf020139_i.asp?Tit=4&bco=",
	"branches_and_atms": "http://www.bcra.gov.ar/sisfin/sf020130_i.asp?Tit=5&bco=",
	"quarterly_information": "http://www.bcra.gov.ar/sisfin/sf040000.asp?bco=",
	"exchange_institutions": "http://www.bcra.gov.ar/sisfin/sf010200_i.asp",
	"institutions_in_receivership": "http://www.bcra.gov.ar/sisfin/sf010300_i.asp",
	"representatives_of_foreign_institutions": "http://www.bcra.gov.ar/sisfin/sf020110_i.asp",
	"financial_trusts": "http://www.bcra.gov.ar/sisfin/sf010400_i.asp"
}

#lists of institutions of each type
institution_urls = [
	{'type_of_institution': "Public bank", 'url': "http://www.bcra.gov.ar/sisfin/sf020101_i.asp?bco=AAA10&tipo=2"},
	{'type_of_institution': "Private bank", 'url': "http://www.bcra.gov.ar/sisfin/sf020101_i.asp?bco=AAA20&tipo=3"},
	{'type_of_institution': "Financial institution", 'url': "http://www.bcra.gov.ar/sisfin/sf020101_i.asp?bco=AAA30&tipo=5"},
	{'type_of_institution': "Credit union", 'url': "http://www.bcra.gov.ar/sisfin/sf020101_i.asp?bco=AAA40&tipo=6"}
]

#There are further details available as PDFs, but which are not currently scraped
# http://www.bcra.gov.ar/pdfs/sisfin/Proveedores_no_financieros.pdf - non financial credit providers
# http://www.bcra.gov.ar/pdfs/sisfin/Emisora_tarjetas.pdf - non-financial companies issuing credit and/or purchase cards
# http://www.bcra.gov.ar/pdfs/marco/SGR.pdf - reciprocal guarantee companies
# http://www.bcra.gov.ar/pdfs/sisfin/Fondos.pdf - guarantee funds of public nature
# http://www.bcra.gov.ar/pdfs/sisfin/DIRECCIONES_EX_ENT.PDF - former institutions

#needed for translating financial statements - it uses a key
audit_opinions = {
	"1": "FAVORABLE WITH NO EXCEPTIONS",
	"2": "FAVORABLE WITH EXCEPTIONS REGARDING EXHIBITION",
	"3": "FAVORABLE WITH EXCEPTIONS REGARDING VALUATION",
	"4": "FAVORABLE WITH INDEFINITE EXCEPTIONS REGARDING SCOPE LIMITATIONS",
	"5": "FAVORABLE WITH INDEFINITE EXCEPTIONS REGARDING UNCERTAINTY OVER FUTURE EVENTS",
	"6": "UNFAVORABLE OPINION",
	"7": "REFRAINED OPINION",
	"8": "NO OBSERVATIONS",
	"9": "WITH OBSERVATIONS FOR SPECIFIC CONCEPTS",
	"10": "WITH OBSERVATIONS FOR INDEFINITE CONCEPTS"
}

colour_hierarchy = {
	"#004488": 0, #dark blue is highest-level
	"#00A080": 1, #green
	"#D85A71": 2, #red
	"#000000": 3  #black
}

exchange_institution_types = [
	{'type': 'Exchange company', 'value': 'casas'},
	{'type': 'Exchange agency', 'value': 'agencias'},
	{'type': 'Exchange broker', 'value': 'corredores'}
]

#FUNCTIONS
#retrieve a document at a given URL as parsed html tree
def get_doc(source_url, extra_parameters={}):
	post_value = {"Pagina": "1"} #need to override post values on certain pages to avoid automatic redirection
	post_value.update(extra_parameters)
	response = requests.post(source_url, post_value)
	html = response.content
	doc = BeautifulSoup(html)
	return doc

#get going
sample_date = unicode(date.today())
turbotlib.log("Starting run on " + sample_date) # Optional debug logging

#****

#SECTION TWO: FINANCIAL INSTITUTIONS - COLLATE LIST OF ENTITIES AND THEN PROCESS DETAILS OF EACH ENTITY
turbotlib.log("")
turbotlib.log("**** FINANCIAL INSTITUTIONS ****")
turbotlib.log("")

#scrape list of financial institutions to look at
financial_institutions = [] #list to store the ones we find
for list_url in institution_urls:
	turbotlib.log("Loading list of " + list_url['type_of_institution'] + "s")
	# try:
	financial_institution_list_page = get_doc(list_url['url'])
	financial_institution_list = financial_institution_list_page.find("table", attrs={"class": "Tabla_Borde"})
	tr_list = financial_institution_list.find_all("tr")
	#id numbers for entitties are in the first column of the main table on the page
	for tr in tr_list[1:]:
		td_list = tr.find_all("td")
		entity_id = td_list[0].text.strip()
		entity_name = (td_list[1].text.strip()).decode('iso-8859-1').encode("utf-8")
		if ((len(entity_id) > 0) and (len(entity_name) > 0)):
			entity = {
				'id': entity_id,
				'name': entity_name,
				'type_of_institution': list_url['type_of_institution']
			}
			financial_institutions.append(entity)
	# except:
	turbotlib.log("Unable to load list of " + list_url['type_of_institution'] + "s")

turbotlib.log("")

#go through list of financial institutions and extract details
for entity in financial_institutions:
	#monitor progress
	entity_count = financial_institutions.index(entity) + 1
	turbotlib.log(("Parsing entity " + str(entity['id']) + ": " + entity['name'] + " (" + str(entity_count) + u"/" + str(len(financial_institutions)) + ")").encode("utf-8"))
	turbotlib.log("    Loading main page")
	
	try:
		#load main page - get the details from the main table. Hope is that the same info is always in the same row/cell
		main_page = get_doc(urls["financial_institution_main_page"] + entity['id'])
		details_table = main_page.find("table", id="table1")
		details_labels = details_table.find_all("span")
		
		#create object to hang results from
		output = {
			'name': entity['name'],
			'id': entity['id'],
			'source_url': urls['financial_institution_main_page'] + entity['id'],
			'sample_date': sample_date,
			'source': "Banco Central de la República Argentina",
			'type_of_institution': entity['type_of_institution']
		}

		#find the relevant label, and the text will be next to it -- add it to our output object
		for span in details_labels:
			span_text = span.text.strip()
			if (span_text == "Bank No.:"):
				output['bank_number'] = span.next_sibling.strip()
			elif (span_text == "CUIT:"):
				output['cuit'] = span.next_sibling.strip()
			elif (span_text == "Balance Sheet Closing Month:"):
				output['balance_sheet_closing_month'] = span.next_sibling.strip()
			elif (span_text == "Address:"):
				output['address'] = span.next_sibling.strip().replace("\t", "").replace("\n","").replace("  ", "")
			elif (span_text == "Telephone:"):
				output['telephone'] = span.next_sibling.strip()
			elif (span_text == "Fax:"):
				output['fax'] = span.next_sibling.strip()
			elif (span_text == "Internet Site:"):
				output['url'] = span.next_sibling['href']
			elif (span_text == "Email:"):
				output['email'] = span.find_next("a").text.strip()
			elif (span_text == "Member:"):
				output['member_of'] = span.next_sibling.strip()
			elif (span_text == "Institutional Group:"):
				output['institutional_group'] = span.next_sibling.strip()
			elif (span_text != "Financial service customer assistance manager"):
				turbotlib.log("**** New type of label: " + span_text)

		#try to find logo image
		img_list = main_page.find_all("img")
		for img in img_list:
			if ("/logosbancos/" in img['src']):
				#need to convert to absolute reference instead of relative
				file_name_start = img['src'].rfind("/") + 1
				file_name = img['src'][file_name_start:]
				img_src = "http://www.bcra.gov.ar/images/logosbancos/" + file_name 
				output['logo'] = img_src

		#now get further details from the other pages on the site
		#FIRST: Financial service customer asssistant manager
		turbotlib.log("    Loading financial service customer assistant manager page")
		try:
			customer_service_page = get_doc(urls['financial_service_customer_assistance_manager'] + entity['id'])
			customer_service_table = customer_service_page.find("table", attrs={"class": "Tabla_Borde"})

			if (customer_service_table != None):
				#extract all relevant rows from table into a list
				customer_service_managers = []
				tr_list = customer_service_table.find_all("tr")
				if (len(tr_list) > 0):
					for tr in tr_list[1:]:
						td_list = tr.find_all("td")
						manager = {
							'name': td_list[0].text.strip(),
							'email': td_list[1].a.text.strip(),
							'address': td_list[2].text.strip(),
							'telephone': td_list[3].text.strip()
						}

						if (len(manager['name']) > 0):
							customer_service_managers.append(manager)

				#if we have any results, append them to our main output object
				if (len(customer_service_managers) > 0):
					output['financial_service_customer_assistance_managers'] = customer_service_managers
		except:
			turbotlib.log("    Unable to load financial service customer assistant manager page")

		#SECOND: head management
		turbotlib.log("    Loading head management page")
		try:
			head_management_page = get_doc(urls['head_management'] + entity['id'])
			directors_table = head_management_page.find("table", attrs={"class": "Tabla_Borde"})

			if (directors_table != None):
				#extract details into a list
				head_management = []
				tr_list = directors_table.find_all("tr")
				for tr in tr_list[1:]:
					td_list = tr.find_all("td")
					director = {
						'name': td_list[1].text.strip(),
						'position': td_list[0].text.strip()
					}
					if (len(director['name']) > 0):
						head_management.append(director)
				
				#if we have any results, append them to our main output object
				if (len(head_management) > 0):
					output['head_management'] = head_management
		except:
			turbotlib.log("    Unable to load head management page")

		#THIRD: shareholders
		turbotlib.log("    Loading shareholders page")
		try:
			shareholders_page = get_doc(urls['shareholders'] + entity['id'])
			shareholders_table = shareholders_page.find("table", attrs={"class": "Tabla_Borde"})

			if (shareholders_table != None):
				#extract details into a list
				shareholders = []
				tr_list = shareholders_table.find_all("tr")
				for tr in tr_list[1:]:
					td_list = tr.find_all("td")
					shareholder = {
						'name': td_list[0].text.strip(),
						'capital': td_list[1].text.strip(),
						'voting_shares': td_list[2].text.strip()
					}

					if (len(shareholder['name']) > 0):
						shareholders.append(shareholder)

				if (len(shareholders) > 0):
					output['shareholders'] = shareholders
		except:
			turbotlib.log("    Unable to load shareholders page")

		#FOURTH: auditors
		turbotlib.log("    Loading auditors page")
		try:
			auditors_page = get_doc(urls['auditors'] + entity['id'])
			audit_tables = auditors_page.find_all("table", attrs={"class": "Tabla_Borde"})

			#several tables - need to work out which is which and then process appropriately
			for audit_table in audit_tables:
				tr_list = audit_table.find_all("tr")
				table_header = tr_list[0].td.text.strip()

				if (table_header == "EXTERNAL AUDIT"):
					td_list = tr_list[2].find_all("td")
					external_auditor = {
						'name': td_list[0].text.strip(),
						'start_date': td_list[1].text.strip(),
						'company': td_list[2].text.strip()
					}

					if (len(external_auditor['name']) > 0):
						output['external_auditor'] = external_auditor

				elif (table_header == "INTERNAL AUDIT"):
					internal_auditor = tr_list[1].text.strip()
					if (len(internal_auditor) > 0):
						output['internal_auditor'] = internal_auditor

				elif (table_header == "RESPONSIBLE PARTNER"):
					responsible_partner = tr_list[1].text.strip()
					if (len(responsible_partner) > 0):
						output['responsible_partner'] = responsible_partner
					
				elif (table_header == "COMITE OF AUDIT"):
					audit_committee = []
					for tr in tr_list[2:]:
						td_list = tr.find_all("td")
						member = {
							'name': td_list[1].text.strip(),
							'position': td_list[0].text.strip()
						}
						if (len(member['name']) > 0):
							audit_committee.append(member)
					
					if (len(audit_committee) > 0):
						output['audit_committee'] = audit_committee
		except:
			turbotlib.log("    Unable to load auditors page")

		#FIFTH: financial statements
		turbotlib.log("    Loading financial statements page")
		try:
			fin_stats_page = get_doc(urls['financial_statements'] + entity['id'])
			fin_stats_table = fin_stats_page.find("table", attrs={"class": "Tabla_Borde"})

			if (fin_stats_table != None):
				#extract relevant information
				financial_statements = [] #will store a list of statements. each statement is made up of a number of rows setting out a) the value, b) the caption, c) the caption it rolls up into
				tr_list = fin_stats_table.find_all("tr")

				#now go through each column and create a financial statement for each
				dates_td = tr_list[0].find_all("td")
				for td in dates_td[1:]:
					column = dates_td.index(td) #keep track of which column we're in
					financial_statement = {
						'date': td.text.strip(),
						'unit': "ARS thousands",
					}

					#translate the audit opinion into 
					opinion_list = tr_list[1].find_all("td")
					opinion_number = opinion_list[column].text.strip()
					if (len(opinion_number) > 0):
						opinion_number = opinion_number.replace("[", "").replace("]", "")
						opinion_numbers = opinion_number.split("-") #have seen cases with more than one opinion (e.g. [2-3])
						opinions = []
						for x in opinion_numbers:
							if (x <= 10):
								opinions.append(audit_opinions[x])
						audit_opinion = " / ".join(opinions)
						if (len(audit_opinion) > 0):
							financial_statement['audit_opinion'] = audit_opinion

					#use colours to determine hierarchy
					hierarchy = [
						{
							'parent': financial_statement,
							'colour': "#004488"
						}
					]
					last_line = None

					#now extract the detail and the numbers
					for tr in tr_list[2:]:
						td_list = tr.find_all("td")
						caption = td_list[0].text.strip()
						if (caption == "A S S E T S"):
							caption = "Assets"
						elif (caption == "L I A B I L I T I E S"):
							caption = "Liabilities"
						elif (caption == "E Q U I T Y"):
							caption = "Equity"
						elif (caption == "A C C U M U L A T E D   I N C O M E"):
							caption = "Accumulated Income"
						elif (caption == "M E M O R A N D U M   A C C O U N T S"):
							caption = "Memorandum Accounts"

						value = td_list[column].text.strip()
						line_item = {
							'caption': caption,
							'value': value,
						}
						colour = td_list[0].font.attrs['color']

						#use colours to determine hierarchy:
						last_level = hierarchy[-1]
						#case 1: we're moving at the same level as before - keep the same parent
						if (colour == last_level['colour']):
							parent = last_level['parent']
						else:
							#we have a change of colour. are we getting more or less depth?
							colour_level = colour_hierarchy[colour] #new level
							last_colour_level = colour_hierarchy[last_level['colour']]

							#case 2: we're moving to greater depth
							if (colour_level > last_colour_level):
								new_level = {
									'parent': last_line,
									'colour': colour
								}
								hierarchy.append(new_level)
								parent = last_line

							#case 3: we're moving to shallower depth
							else:
								while (last_colour_level > colour_level):
									hierarchy.pop()
									last_level = hierarchy[-1]
									last_colour_level = colour_hierarchy[last_level['colour']]
								parent = last_level['parent']

						#no point having line items with no values
						if ((len(value) > 0) or (caption == "Memorandum Accounts")):
							if ("components" in parent):
								parent['components'].append(line_item)
							else:
								parent['components'] = [line_item]

							if (value == ""):
								line_item.pop("value", None)

							last_line = line_item
					
					#check we've added any info to the financial statement before adding to list
					if (len(financial_statement) > 2):
						if (len(financial_statement['components']) == 1):
							#remove empty keys if there were no values given
							financial_statement.pop('components', None)
							financial_statement.pop('unit', None)
						financial_statements.append(financial_statement)

				#if we found anything, add it to the output
				if (len(financial_statements) > 0):
					output['financial_statements'] = financial_statements
		except:
			turbotlib.log("    Unable to load financial statements page")

		#SIXTH: debtors status
		turbotlib.log("    Loading debtors status page")
		try:
			debtors_page = get_doc(urls['debtors_status'] + entity['id'])
			debtors_table = debtors_page.find("table", attrs={"class": "Tabla_Borde"})

			#need to identify where the different divisions are, based on repeated date row
			tr_list = debtors_table.find_all("tr")
			portfolio_sections = []
			start_number = 1
			row_number = 0
			for tr in tr_list[1:]:
				row_number += 1
				#found the end row - work out the bits we have
				if (tr.td.attrs["class"][0] == "Celda_Borde_Titulo"):
					end_number = row_number - 1
					section = {
						'start': start_number,
						'end': end_number
					}
					portfolio_sections.append(section)
					start_number = row_number + 1
			#add on last bit when we get to the end too
			final_section = {
				'start': start_number,
				'end': row_number
			}
			portfolio_sections.append(final_section)

			#get the relevant dates, and then go through the columns one by one
			debtors_status = []
			dates = tr_list[0].find_all("td")
			for td in dates[1:]:
				column = dates.index(td)
				for section in portfolio_sections:
					status = {
						'date': td.text.strip(),
						'unit': "ARS thousands"
					}

					#get details about the header
					portfolio_row = tr_list[section['start']].find_all("td")
					status['portfolio'] = portfolio_row[0].text.strip()
					status['value'] = portfolio_row[column].text.strip()

					ratios = []
					#now get the relevant ratios relating to that portfolio from following rows
					for tr in tr_list[section['start'] + 1: section['end'] + 1]:
						td_list = tr.find_all("td")
						caption = td_list[0].text.strip()
						value = td_list[column].text.strip()
						
						if ((len(caption) > 0) and (len(value) > 0)):
							#ie. we have an absolute value - add it to the portfolio level
							if ("." in value):
								status[caption] = value
							else:
								#we have a percentage, so add a percentage sign and add it to a list of ratios
								ratio = {
									'ratio': caption,
									'value': value + "%"
								}
								if (len(caption) > 0):
									ratios.append(ratio)
						
						#check we have something before adding it
						if (len(ratios) > 0):
							status['ratios'] = ratios

					#check we've added something besides the date/name before storing the result
					if (len(status) > 2):
						debtors_status.append(status)
			
			#if there is data, add it to the main result object and continue to next page
			if (len(debtors_status) > 0):
				output['debtors_status'] = debtors_status
		except:
			turbotlib.log("    Unable to load debtors status page")

		#SEVENTH: indicators
		turbotlib.log("    Loading indicators page")
		try:
			indicators_page = get_doc(urls['indicators'] + entity['id'])
			indicators_tables = indicators_page.find_all("table", attrs={"class": "Tabla_Borde"})

			#have several tables. process each separately
			indicators = []
			for indicators_table in indicators_tables:
				tr_list = indicators_table.find_all("tr")
				headers_row = tr_list[0].find_all("td")
				
				#extract category from top-left cell
				category = headers_row[0].text.strip()
				category_start = category.find("- ") + 2
				category_end = category.find("(")
				category = category[category_start : category_end]

				#go through remaining rows
				for tr in tr_list[1:]:
					td_list = tr.find_all("td")
					caption = td_list[0].text.strip()
					for td in td_list[1:]:
						column = td_list.index(td)
						date = headers_row[column].text.strip()
						value = td.text.strip()

						#put it all together
						indicator = {
							'category': category,
							'caption': caption,
							'date': date,
							'value': value
						}

						if (len(value) > 0):
							indicators.append(indicator)

			#store results if we found any
			if (len(indicators) > 0):
				output['indicators'] = indicators
		except:
			turbotlib.log("    Unable to load indicators page")

		#EIGHTH: structural information
		turbotlib.log("    Loading structural information page")
		try:
			structural_page = get_doc(urls['structural_information'] + entity['id'])
			structural_tables = structural_page.find_all("table", attrs={"class": "Tabla_Borde"})
			location_counts = [] #will need to store results for either domestic or outside Argentina

			#work through tables one-by-one
			for structural_table in structural_tables:
				tr_list = structural_table.find_all("tr")
				if (len(tr_list) > 1):

					#identify which type of table it is from top-left cell
					table_top_left = tr_list[0].td.text.replace("\n", "").replace("\t", "").replace("  ", "").strip()
					
					#first table: accounts information, etc. doesn't look like there's any hierarchy to this, so add to top level object
					if (("INFORMATION" in table_top_left) or ("ADITIONAL" in table_top_left)):
						date_row = tr_list[0].find_all("td")
						#look at each row after the header/dates
						for tr in tr_list[1:]:
							#get the caption then go through each column
							td_list = tr.find_all("td")
							caption = td_list[0].text.strip()
							data_points = []
							for td in td_list[1:]:
								column = td_list.index(td)
								date = date_row[column].text.strip()
								value = td.text.strip()

								#extract info into an object, and then add to list
								if (len(value) > 0):
									data_point = {
										'date': date,
										'value': value
									}
									data_points.append(data_point)

							#if we have some data, add it to our object
							if (len(data_points) > 0):
								output[caption] = data_points

					#second kind of table - store as one object
					elif ((table_top_left == "PAYROLL THRU DIRECT DEPOSIT") or (table_top_left == "Payroll Thru Direct Deposit")):
						payroll_deposit = {}
						date_row = tr_list[0].find_all("td")
						#look at each row
						for tr in tr_list[1:]:
							#get caption then go through the dates
							td_list = tr.find_all("td")
							caption = td_list[0].text.strip()
							data_points = []
							for td in td_list[1:]:
								column = td_list.index(td)
								date = date_row[column].text.strip()
								value = td.text.strip()

								if (len(value) > 0):
									data_point = {
										'date': date,
										'value': value
									}
									data_points.append(data_point)
						
							#add to level above if we have a result
							if (len(data_points) > 0):
								payroll_deposit[caption] = data_points

						#add to output object if we have some data
						if (len(payroll_deposit) > 0):
							output['payroll_through_direct_deposit'] = payroll_deposit

					#details on branches
					elif ((table_top_left == "DOMESTIC") or (table_top_left == "Domestic")):
						for tr in tr_list[2:]: #have two header rows to ignore this time
							td_list = tr.find_all("td")
							location = td_list[0].text.strip()
							operating_branches = td_list[1].text.strip()
							authorised_branches = td_list[2].text.strip()
							requested_branches = td_list[3].text.strip()
							total_branches = td_list[4].text.strip()
							atms = td_list[5].text.strip()

							#only bother to store data if there was a number in the cell
							if (len(location) > 0):
								data_point = {
									'category': "Domestic",
									'location': location
								}
								branches = {}
								if (len(operating_branches) > 0):
									branches['operating'] = operating_branches
								if (len(authorised_branches) > 0):
									branches['authorised'] = authorised_branches
								if (len(requested_branches) > 0):
									branches['requested'] = requested_branches
								if (len(total_branches) > 0):
									branches['total'] = total_branches
								if (len(branches) > 0):
									data_point['branches'] = branches
								if (len(atms) > 0):
									data_point['atms'] = atms

								#store it if we have any results
								if (('branches' in data_point) or ('atms' in data_point)):
									location_counts.append(data_point)

					#other table seen - branches outside Argentina
					elif ((table_top_left == "OUTSIDE ARGENTINA") or (table_top_left == "Outside Argentina")):
						for tr in tr_list[1:]:
							td_list = tr.find_all("td")
							location = td_list[0].text.strip()
							if (len(location) > 0):
								total_branches = td_list[1].text.strip()
								representative_offices = td_list[2].text.strip()
								data_point = {
									'category': "Outside Argentina",
									'location': location
								}
								if (len(total_branches) > 0):
									#keep format consistent with domestic ones
									data_point['branches'] = {
										'total': total_branches
									}
								if (len(representative_offices) > 0):
									data_point['representative_offices'] = representative_offices

								#store the result if we had any information on it
								if (len(data_point) > 2):
									location_counts.append(data_point)

					#add domestic and international locations to table if we found any
					if (len(location_counts) > 0):
						output['location_counts'] = location_counts
		except:
			turbotlib.log("    Unable to load structural information page")

		#NINTH: branches and ATMs
		turbotlib.log("    Loading detailed branch information")
		try:
			branch_index_page = get_doc(urls['branches_and_atms'] + entity['id'])
			drop_down_list = branch_index_page.find_all("select")

			for drop_down in drop_down_list:
				label = drop_down.parent.parent.parent.parent.td.text.strip()
				option_list = drop_down.find_all("option")
				#ignore it if it only contains "select province" line
				if (len(option_list) > 1):
					data_points = []
					for option in option_list[1:]:
						location = option.text.strip()
						url = "http://www.bcra.gov.ar/sisfin/"  + option.attrs['value'].replace(" ", "")

						#now need to load the page and process the details therein - looks like the same info in each
						turbotlib.log("      Loading " + label + " in " + location)
						try:
							branch_page = get_doc(url)
							branch_table = branch_page.find("table", attrs={"class": "Tabla_Borde"})

							if (branch_table != None):
								tr_list = branch_table.find_all("tr")
								for x in xrange(2, len(tr_list), 2):
									#load pairs of rows
									td_one = tr_list[x].find_all("td")
									td_two = tr_list[x + 1].find_all("td")

									city = td_one[0].text.strip()
									address = td_two[0].text.strip()
									zip_code = td_two[1].text.strip()
									area_code = td_two[2].text.strip()
									fax = td_two[3].text.strip()
									atm = td_two[4].text.strip()

									#create an object - add info to it if we have it
									data_point = {}
									if (len(city) > 0):
										data_point['city'] = city
									if (len(address) > 0):
										data_point['address'] = address
									if (len(zip_code) > 0):
										data_point['zip'] = zip_code
									if (len(area_code) > 0):
										data_point['area_code'] = area_code
									if (len(fax) > 0):
										data_point['fax'] = fax
									if (atm == "SI"):
										data_point['atm'] = True
									if (atm == "NO"):
										data_point['atm'] = False

									#add to list if we have gathered any info
									if (len(data_point) > 0):
										data_point['location'] = location
										data_points.append(data_point)
						except:
							turbotlib.log("      Unable to load " + label + " in " + location)

					#add list to output object if we have any thing to sho
					if (len(data_points) > 0):
						output[label] = data_points
		except:
			turbotlib.log("    Unable to load detailed branch information")

		#TENTH: quarterly information
		turbotlib.log("    Loading quarterly information page")
		try:
			quarterly_info_page = get_doc(urls['quarterly_information'] + entity['id'])
			quarterly_info_table = quarterly_info_page.find("table", attrs={"class": "Tabla_Borde"})
			tr_list = quarterly_info_table.find_all("tr")

			#make a list of all the reports- then loop through them
			quarterly_report_list = []
			quarterly_information = {} #store results - use a dict, with report name as the key

			#go through table - extract relevant information from the reports which are linked
			for tr in tr_list[1:]:
				td_list = tr.find_all("td")
				report_number = td_list[0].text.strip()
				report_name = td_list[1].text.strip()
				link_one = td_list[2].a
				link_two = td_list[3].a

				#extract links
				if (link_one != None):
					#only version of report
					link_one_text = link_one.text.strip()
					if (link_one_text == "Ver"):
						link_one_url = "http://www.bcra.gov.ar/sisfin/" + link_one['href']
						report = {
							'report_number': report_number,
							'report_name': report_name,
							'url': link_one_url
						}
						quarterly_report_list.append(report)

					#if there is an individual version of report
					if (link_one_text == "Individual"):
						link_one_url = "http://www.bcra.gov.ar/sisfin/" + link_one['href']
						report = {
							'report_number': report_number + "-individual",
							'report_name': report_name + ": Individual",
							'url': link_one_url
						}
						quarterly_report_list.append(report)
				
				#consolidated version of report				
				if (link_two != None):
					link_two_text = link_two.text.strip()
					if (link_two_text == "Consolidado"):
						link_two_url = "http://www.bcra.gov.ar/sisfin/" + link_two['href']
						report = {
							'report_number': report_number + "-consolidado",
							'report_name' : report_name + ": Consolidado",
							'url': link_two_url
						}
						quarterly_report_list.append(report)

			#now go through and load/extract info from each report
			for quarterly_report in quarterly_report_list:
				report = {
					'number': quarterly_report['report_number'],
					'name': quarterly_report['report_name'],
					'data': [] #list of facts recorded
				}

				turbotlib.log("      Loading report " + quarterly_report['report_name'])
				try:
					report_page = get_doc(quarterly_report['url'])
					
					#check if we have just one table, or if there are several -- different techniques needed
					report_tables = report_page.find_all("table", attrs={"class": "Tabla_Borde"})
					if (len(report_tables) > 1):
						#we have several, so process them one-by-one
						for table in report_tables:
							#get the date from the line above the table
							table_date_string = table.find_previous("p").text.strip()
							table_date = table_date_string[3:]

							#get the headers
							tr_list = table.find_all("tr")
							header_row = tr_list[0].find_all("td")
							headers = []
							for td in header_row:
								header = td.text.strip()
								headers.append(header)

							#use indentation to record hierarchy
							hierarchy = []
							last_line = None

							#process all the rows/columns
							for tr in tr_list[1:]:
								td_list = tr.find_all("td")
								caption = td_list[0].text.strip()
								indent = td_list[0].text.find(caption)

								#now we've worked out the indent, remove initial "- " from captions
								if (len(caption) > 0):
									if (caption[0] == "-"):
										caption = caption[1:].strip()

								#set up the hierarchy on the first go
								if (tr_list.index(tr) == 1):
									hierarch_row = {
										'parent': None,
										'indent': indent
									}
									hierarchy.append(hierarch_row)

								#if we have a total row, override actual indentation and keep it at the current level
								if (caption == "TOTAL"):
									indent = hierarchy[-1]['indent']

								#work out which level of the hierarchy we're at, based on captions
								last_level = hierarchy[-1]
								last_indent = last_level['indent']
								#case 1: at the same level as before - keep the same parent
								if (indent == last_indent):
									parent = last_level['parent']
								#case 2: moving deeper
								elif (indent > last_indent):
									new_level = {
										'parent': last_line,
										'indent': indent
									}
									hierarchy.append(new_level)
									parent = last_line
								#case 3: moving shallower
								else:
									while (last_indent > indent):
										hierarchy.pop()
										#cope with a case where it goes further outdented then it started
										if (len(hierarchy) == 0):
											hierarch_row = {
												'parent': None,
												'indent': indent
											}
											hierarchy.append(hierarch_row)
										last_level = hierarchy[-1]
										last_indent = last_level['indent']
											
									parent = last_level['parent']

								#convert hierarchy into a list we can attach
								parents = [x['parent'] for x in hierarchy if x['parent'] != None]

								#now process the values from the other columns
								for td in td_list[1:]:
									data_point = {
										'date': table_date,
									}
									column = td_list.index(td)
									header = headers[column]
									value = td.text.strip()

									#if we have some data, add it to our object
									if ((len(caption) > 0) and (len(header) > 0) and ((len(value) > 0) or (len(parents) > 0))):
										data_point['caption'] = caption
										data_point['field'] = header

										#add value if we have one
										if (len(value) > 0):
											data_point['value'] = value

										#add hierarchy if there is one
										if (len(parents) > 0):
											data_point['parent_captions'] = parents
										
										report['data'].append(data_point)
										last_line = caption

					#cases where there is just one table - superficially similar, but the dates are stored in the columns (by and large)
					elif (len(report_tables) == 1):
						#as before, extract the headers
						tr_list = report_tables[0].find_all("tr")
						header_row = tr_list[0].find_all("td")
						headers = []
						for td in header_row:
							header = td.text.strip()
							headers.append(header)

						#notes report is weird - it's got no captions and has urls as values
						if (quarterly_report['report_number'] == "Notas"):
							for tr in tr_list[1:]:
								td_list = tr.find_all("td")
								for td in td_list:
									column = td_list.index(td)
									header = headers[column]
									column_date = header[3:]
									href = td.a['href']
									url = "http://www.bcra.gov.ar" + href[2:]

									if ((len(url) > 0) and (len(column_date) > 0)):
										data_point = {
											'date': column_date,
											'url': url
										}
										report['data'].append(data_point)

						#normal tables are different
						else:
							#use indentation to record hierarchy
							hierarchy = []
							last_line = None

							#now go through each row and get each data point
							for tr in tr_list[1:]:
								td_list = tr.find_all("td")
								caption = td_list[0].text.strip()
								indent = td_list[0].text.find(caption)

								#now we've worked out the indent, we can safely remove initial "- " from captions
								if (caption[0] == "-"):
									caption = caption[1:].strip()

								#set up the hierarchy on the first go
								if (tr_list.index(tr) == 1):
									hierarch_row = {
										'parent': None,
										'indent': indent
									}
									hierarchy.append(hierarch_row)

								#if we have a total row, override actual indentation and keep it at the current level
								if (caption == "TOTAL"):
									indent = hierarchy[-1]['indent']

								#work out which level of the hierarchy we're at, based on captions
								last_level = hierarchy[-1]
								last_indent = last_level['indent']
								#case 1: at the same level as before - keep the same parent
								if (indent == last_indent):
									parent = last_level['parent']
								#case 2: moving deeper
								elif (indent > last_indent):
									new_level = {
										'parent': last_line,
										'indent': indent
									}
									hierarchy.append(new_level)
									parent = last_line
								#case 3: moving shallower
								else:
									while (last_indent > indent):
										hierarchy.pop()
										#cope with a case where it goes further outdented then it started
										if (len(hierarchy) == 0):
											hierarch_row = {
												'parent': None,
												'indent': indent
											}
											hierarchy.append(hierarch_row)
										last_level = hierarchy[-1]
										last_indent = last_level['indent']		
									parent = last_level['parent']

								#convert hierarchy into a list we can attach
								parents = [x['parent'] for x in hierarchy if x['parent'] != None]

								for td in td_list[1:]:
									column = td_list.index(td)
									header = headers[column]
									value = td.text.strip()

									#most reports have the column header as the date
									if (report_number != "Anexo C"):
										column_date = header[3:]

										#found some data, so make a point and add it to the list
										if (((len(value) > 0) or (len(parents) > 0)) and (len(caption) > 0) and (len(column_date) > 0)):
											data_point = {
												'caption': caption,
												'date': column_date
											}

											#add value if we have it
											if (len(value) > 0):
												data_point['value'] = value

											#add hierarchy info
											if (len(parents) > 0):
												data_point['parent_captions'] = parents

											report['data'].append(data_point)
											last_line = caption

									#one is different - has two columns per data
									else:
										split_point = header.find("a:")
										column_field = header[:split_point - 1]
										column_date = header[split_point + 3:]

										if (((len(value) > 0) or (len(parents) > 0)) and (len(caption) > 0) and (len(column_date) > 0) and (len(column_field) > 0)):
											data_point = {
												'caption': caption,
												'date': column_date,
												'field': column_field
											}

											#add value if we have it
											if (len(value) > 0):
												data_point['value'] = value

											#add hierarchy info
											if (len(parents) > 0):
												data_point['parent_captions'] = parents

											report['data'].append(data_point)
											last_line = caption

					#if we found any data on the page, add to our object
					if (len(report['data']) > 0):
						quarterly_information[quarterly_report['report_number']] = report
				except:
					turbotlib.log("      Unable to load report " + quarterly_report['report_name'])

			#if we found any data from any of the reports, add it to our main object
			if (len(quarterly_information) > 0):
				output['quarterly_information'] = quarterly_information
		except:
			turbotlib.log("    Unable to load quarterly information page")

		print(json.dumps(output).encode("utf-8"))

	except:
		turbotlib.log("    Unable to load main page -- skipping this entity")

#****

#SECTION THREE: EXCHANGE INSTITUTIONS - PROCESS DETAILS ON EACH

# go through the three categories of exchange institution
turbotlib.log("")
turbotlib.log("**** FINANCIAL INSTITUTIONS ****")
turbotlib.log("")

for exchange_type in exchange_institution_types:
	exchange_number = unicode(exchange_institution_types.index(exchange_type))
	turbotlib.log("Loading " + exchange_type['type'] + " list (" + exchange_number + "/" + unicode(len(exchange_institution_types)) + ")")
	exchange_url =  urls['exchange_institutions'] + "?Orden=nombre&Tipo=" + exchange_type['value']
	try:
		exchange_page = get_doc(exchange_url)

		#find the table and process the entities
		exchange_table = exchange_page.find("table", attrs={"class": "Tabla_Borde"})
		tr_list = exchange_table.find_all("tr")

		#go through rows two at a time
		for row_num in xrange(1, len(tr_list), 2):
			row_one = tr_list[row_num].td
			row_two = tr_list[row_num + 1].find_all("td")
			
			#make output object for this entity
			output = {
				'sample_date': sample_date,
				'source_url': exchange_url,
				'type_of_institution': exchange_type['type'],
				'source': "Banco Central de la República Argentina"
			}

			name_string = row_one.text.strip().split(" - ")
			name = name_string[0].strip()
			number = name_string[1].strip()

			address = row_two[0].text.strip()
			zip_code = row_two[1].text.strip()
			locality = row_two[2].text.strip()
			province = row_two[3].text.strip()
			area_code = row_two[4].text.strip()
			telephone = row_two[5].text.strip()

			#add the details we have to our object - must have a name at the very least
			if (len(name) > 0):
				output['name'] = name

				if (len(number) > 0):
					output['number'] = number
				if (len(address) > 0):
					output['address'] = address
				if (len(zip_code) > 0):
					output['zip_code'] = zip_code
				if (len(locality) > 0):
					output['locality'] = locality
				if (len(province) > 0):
					output['province'] = province
				if (len(area_code) > 0):
					output['area_code'] = area_code
				if (len(telephone) > 0):
					output['telephone'] = telephone

				print(json.dumps(output).encode("utf-8"))
	except:
		turbotlib.log("Unable to load " + exchange_type['type'] + " list")


#****

#SECTION FOUR: INSTITUTIONS IN RECEIVERSHIP

turbotlib.log("")
turbotlib.log("**** INSTITUTIONS IN RECEIVERSHIP ****")
turbotlib.log("")

turbotlib.log("Loading list of institutions in receivership")
try:
	receivership_list_page = get_doc(urls['institutions_in_receivership'])
	option_list = receivership_list_page.find_all("option")

	for option in option_list[1:]:
		bco = option['value']
		option_number = unicode(option_list.index(option))
		turbotlib.log("Loading institution in receivership: " + bco + " (" + option_number + "/" + unicode(len(option_list)) + ")")

		try:
			receivership_page = get_doc(urls['institutions_in_receivership'], {"bco": bco})
			receivership_tables = receivership_page.find_all("table", attrs={"class": "Tabla_Borde"})
			
			#make an object to output
			output = {
				'sample_date': sample_date,
				'source_url': urls['institutions_in_receivership'],
				'source': "Banco Central de la República Argentina",
				'type_of_institution': "Institution in receivership",
				'name': bco.replace("  ", " ").strip()
			}

			#extract key details
			table_one = receivership_tables[0].find_all("td")
			table_two = receivership_tables[1].find_all("td")

			#get receiver details
			receiver_string = table_one[0].text.strip()
			receiver_parts = receiver_string.split(":")
			receiver = receiver_parts[1].strip()
			if (len(receiver) > 0):
				output['receiver'] = receiver

			#address details
			address_string = table_one[1].text.strip()
			address = address_string[7:] #says 'Adress ' before details we want
			if (len(address) > 0):
				output['address'] = address

			#phone, fax and business hours
			telephone = table_one[2].text.strip()[10:] #says 'Telephone ' before details we want
			if (len(telephone) > 0):
				output['telephone'] = telephone
			fax = table_one[3].text.strip()[4:] #says 'Fax ' before details we want
			if (len(fax) > 0):
				output['fax'] = fax
			business_hours = table_one[4].text.strip()[15:] #says 'Business Hours ' before details we want
			if (len(business_hours) > 0):
				output['business_hours'] = business_hours

			#details of the receivership
			receivership = {}
			receivership_decree_parts = table_two[1].text.strip().split(" ")
			directory_resolution = " ".join(receivership_decree_parts[5:])
			if (len(directory_resolution) > 0):
				receivership['resolution'] = directory_resolution

			#status
			bankruptcy_status_parts = table_two[2].text.strip().split(" ")
			bankruptcy_status = " ".join(bankruptcy_status_parts[4:])
			if (len(bankruptcy_status) > 0):
				receivership['status'] = bankruptcy_status

			#court
			court_parts = table_two[3].text.strip().split(" ")
			court = " ".join(court_parts[4:])
			if (len(court) > 0):
				receivership['court'] = court

			#add details to object and return a result
			if (len(receivership) > 0):
				output['receivership'] = receivership

			print(json.dumps(output).encode("utf-8"))

		except:
			turbotlib.log("Unable to load institution in receivership: " + bco)
except:
	turbotlib.log("Unable to load list of institutions in receivership")

#****

#SECTION FIVE: REPRESENTATIVES OF FOREIGN INSTITUTIONS

turbotlib.log("")
turbotlib.log("**** REPRESENTATIVES OF FOREIGN INSTITUTIONS ****")
turbotlib.log("")

#load table with list of entities
turbotlib.log("Loading list of representatives of foreign institutions")
try:
	foreign_page = get_doc(urls['representatives_of_foreign_institutions'])
	foreign_table = foreign_page.find("table", attrs={"class": "Tabla_Borde"})
	foreign_rows = foreign_table.find_all("tr")

	#need to go through groups of rows at a time
	for row_num in xrange(3, len(foreign_rows), 4):
		row_one = foreign_rows[row_num].find_all("td")
		row_two = foreign_rows[row_num + 1].find_all("td")
		row_three = foreign_rows[row_num + 2].find_all("td")

		#extract the name to see if we have anything to work with
		name = row_one[0].text.strip()
		if (len(name) > 0):
			#we do, so create an output object
			output = {
				'sample_date': sample_date,
				'name': name,
				'source_url': urls['representatives_of_foreign_institutions'],
				'source': "Banco Central de la República Argentina",
				'type_of_institution': "Representative of foreign financial institution not licensed in Argentina"
			}

			#now extract other details
			country = row_one[1].text.strip()
			if (len(country) > 0):
				output['country'] = country
			
			representative = row_two[0].text.strip()
			if (len(representative) > 0):
				output['representative'] = representative
			
			adjunct_representative = row_two[1].text.strip()
			if ((len(adjunct_representative) > 0) and (adjunct_representative != "-")):
				output['adjunct_representative'] = adjunct_representative

			address = row_three[0].text.strip()
			if (len(address) > 0):
				output['address'] = address

			telephone = row_three[1].text.strip()
			if (len(telephone) > 0):
				output['telephone'] = telephone

			fax = row_three[2].text.strip()
			if (len(fax) > 0):
				output['fax'] = fax

			cp_locality = row_three[3].text.strip().split("-")
			if (len(cp_locality) == 2):
				zip_code = cp_locality[0]
				locality = cp_locality[1]
				if (len(zip_code) > 0):
					output['zip_code'] = zip_code
				if (len(locality) > 0):
					output['locality'] = locality

			#print the results
			print(json.dumps(output).encode("utf-8"))
except:
	turbotlib.log("Unable to load list of representatives of foreign institutions")

#****

#SECTION SIX: FINANCIAL TRUSTS

turbotlib.log("")
turbotlib.log("**** FINANCIAL TRUSTS ****")
turbotlib.log("")

#extract list of trusts
turbotlib.log("Loading list of financial trusts")
try:
	trusts_list_page = get_doc(urls['financial_trusts'])
	option_list = trusts_list_page.find_all("option")

	#load each trust in turn
	for option in option_list[1:]:
		name = option.text.strip()
		bco = option['value']
		option_number = unicode(option_list.index(option_number))
		turbotlib.log("Loading financial trust: " + name + " (" + option_number + "/" + unicode(len(option_list)) + ")")
		try:
			trust_page = get_doc(urls['financial_trusts'] + "?bco=" + bco)

			#make an output object, plus placeholder for list of trustees
			output = {
				'name': name,
				'number': bco,
				'source_url': urls['financial_trusts'],
				'sample_date': sample_date,
				'source': 'Banco Central de la República Argentina',
				'type_of_institution': "Financial trust"
			}
			trustees = []

			#there's one table relating to each trustee. find them and extract data from each
			trustee_tables = trust_page.find_all("table", attrs={"class": "Tabla_Borde"})
			for trustee_table in trustee_tables:
				#create an object for each trustee
				trustee = {}

				#get the cells
				tr_list = trustee_table.find_all("tr")
				row_one = tr_list[0].td #only one cell in first row
				row_two = tr_list[1].find_all("td")

				#trustee name is first row
				trustee_name = row_one.text.strip()[9:].strip()
				if (len(trustee_name) > 0):
					trustee['name'] = trustee_name

				#contact details in bottom-left cell
				contact_string = row_two[0].text.strip()

				#area code in brackets
				area_code_start = contact_string.find("(")
				area_code_end = contact_string.find(")")
				area_code = contact_string[area_code_start + 1:area_code_end].strip()
				if (len(area_code) > 0):
					trustee['area_code'] = area_code

				#telephone in the middle
				telephone_start = contact_string.find("tel: ")
				telephone_end = contact_string.find("/ fax: ")
				telephone = contact_string[telephone_start + 5: telephone_end].strip()
				if (len(telephone) > 0):
					trustee['telephone'] = telephone

				#fax number next
				fax_end = contact_string.find("int: ")
				fax = contact_string[telephone_end + 7: fax_end].strip()
				if (len(fax) > 0):
					trustee['fax'] = fax

				#int number -- not sure what this is
				int_number = contact_string[fax_end + 5:].strip()
				if (len(int_number) > 0):
					trustee['int'] = int_number

				#address in bottom-right cell - just leave en masse
				address_string = row_two[1].text.strip()
				if (len(address_string) > 0):
					trustee['address'] = address_string

				#add this to the list if it has a name
				if ('name' in trustee):
					trustees.append(trustee)

			#add trustees to output if we have any
			if (len(trustees) > 0):
				output['trustees'] = trustees

			#output results
			print(json.dumps(output).encode("utf-8"))

		except:
			turbotlib.log("Unable to load financial trust: " + name)
except:
	turbotlib.log("Unable to load list of financial trusts")