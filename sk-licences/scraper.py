# -*- coding: utf-8 -*-

#for everything else
import json
from datetime import date
import datetime
import turbotlib
from bs4 import BeautifulSoup
import bs4
import requests

#CONSTANTS
sample_date = str(date.today()) # record when we looked
base_url = "http://www.nbs.sk" # links appear to be stored relative to this url
exclusionURLs = ["/en/financial-market-supervision/banking-sector-supervision/List-of-credit-institutions/commercial-and-savings-banks/annex-i-of-directive-2013-36-eu-of-the-european-parliament-and-of-the-council-of-26-june-2013-on-a"] #list of links not to process - regulatory information and not entity-related
date_fields = ["date_of_licence_issue", "commenced_operation", "date_of_registration", "expiry_date", "date_of_registration", "licence_date", "cessation_of_a_licence", "return_of_a_licence", "termination_of_the_licence", "date_of_entry_in_the_commercial_register", "licence_validity_date", "licence_issue_date", "licence_ceased", "date_of_closing_the_licence", "date_of_notification's_delivery_to_the_nbs", "date_of_notification's_delivery_to_the_member_state", "licence_issued_on", "licence_valid_from", "maturity", "date_of_issue", "date_of_final_decision", "date_of_notification", "date_of_service_of_notification", "effective_as_of", "finish_a_period_of_validity", "date_of_publish", "date_of_the_validity_of_the_decision", "date_of_the_issue_of_the_decision"]
replacement_labels = {
	'date_of_validiity': 'date_of_validity',
	u'dôvod_zániku_povolenia': 'reason_for_licence',
	u'sídlo': 'address',
	'adress': 'address',
	'deputy_of_mortgage_controllerr': 'deputy_of_mortgage_controller',
	'number_of_empolyees': 'number_of_employees',
	u'povolenie_číslo': 'licence_number',
	u'dátum_právoplatnosti_rozhodnutia': 'date_of_registration',
	u'dátum_udelenia_povolenia': 'licence_date',
	u'ičo': 'company_number',
	u'názov_spoločnosti': 'name',
	u'dátum_zániku_povolenia': 'expiry_date',
	"business_name": "name",
	"name_of_company": "name",
	"no._of_licence": "licence_number",
	"bider": "name",
	"name_of_the_issuer": "name",
	u'commercial_name_-_name_of_person,_that_have_approbation_nbs_on_the_application_laws_of_squeeze_out': "name"
}

#FUNCTIONS
#retrieve a document at a given URL as parsed html tree
def get_doc(source_url):
	response = requests.get(source_url)
	html = response.content
	doc = BeautifulSoup(html)
	return doc

#parse a navigation page into a list of links
def parse_link_page(source_url, exclude=exclusionURLs):
	#load the page and find the right ul element, relative to h1 header
	linkPage = get_doc(source_url)
	linkPageHeader = linkPage.find('h1', id="top")
	ul_count = 0
	for sibling in linkPageHeader.next_siblings: #find the list - second <ul> after the h1
		if (isinstance(sibling, bs4.element.Tag)):
			if (sibling.name == "ul"):
				#we are looking for the second one, not the first
				if (ul_count == 1):
					linkPageList = sibling
					break
				ul_count += 1

	#extract a list of URLs from the li items in the list
	linkList = []
	for linkPageItem in linkPageList.children:
		if (isinstance(linkPageItem, bs4.element.Tag)):
			child_count = 0
			for child in linkPageItem.children:
				if (child_count == 1):
					if (child['href'] not in exclude):
						linkList.append(base_url + child['href'])
				child_count += 1
	return linkList

def parse_detail_table(table):
	object_list = [] #list to store results
	new_object = True # flag to say if we need a new object on this loop
	data = None
	tr = table.find_next('tr')
	while (tr != None):
		#each row has two tds - the label and the value - but check and exclude blank cells
		tds_actual = tr.find_all('td')
		tds = []
		for td in tds_actual:
			if (len(parse_text(td)) > 0):
				tds.append(td)

		if (len(tds) == 0):
			new_object = True #take empty line to mean we need to do start again on the next line
			tr = tr.find_next_sibling("tr")
			continue

		if (len(tds) != 2): #not enough rows - so move on but in existing object
			tr = tr.find_next_sibling("tr")
			continue

		if (new_object):
			if ((data != None) and (data not in object_list)):
				object_list.append(data) #add the previous object if there is one
			new_object = False
			data = {}

		#parse the label and value as strings
		label = parse_text(tds[0], True)
		value = parse_text(tds[1], False)

		#empty fields are no good to man or beast
		if ((len(value) > 0) and (len(label) > 0)):

			#capital amounts - replace "th. EUR" with useful number
			if (label == "capital"):
				if "EUR" in value:
					data["capital_currency"] = "EUR" #store the currency if shown
				value = parse_float(value, ["th. EUR", "th EUR", "thEUR", "th.EUR"])

			#employee counts are a number!
			if (label == "number_of_employees"):
				value = parse_int(value)

			#format dates correctly
			if (label in date_fields):
				value = parse_date(value)

			#some activities licenced contain links - just want the text
			if (label == "activities_licensed"):
				value = parse_text(tds[1].contents, False)

			#add to json object
			add_field(data, label, value)
		tr = tr.find_next_sibling('tr')

	#add final object before leaving
	if ((data != None) and (data not in object_list)):
			object_list.append(data) #add the previous object if there is one
	
	return object_list


def parse_detail_page(source_url):
	detailPage = get_doc(source_url).find(id="mainContent")
	detailName = detailPage.find('h1', id="top").contents[0]
	dataList = []

	#get each row from the table
	detailTables = detailPage.find_all('table')
	for detailTable in detailTables:
		tableData = parse_detail_table(detailTable)
		for item in tableData: #add key data to our objects
			if (len(item) > 0):
				item['name'] = detailName
				item['source_url'] = source_url
				item['sample_date'] = sample_date
				dataList.append(item)

	#return list of parsed objects
	return dataList

def parse_multiple_detail_page(source_url):
	multiplePage = get_doc(source_url)
	contentDiv = multiplePage.find(id="mainContent")
	output = [] #return a list of items

	#if the name is in an h4, then take the name from there and look for detail in following table
	if (len(contentDiv.find_all("h4")) > 0):
		for h4 in contentDiv.find_all("h4"):
			#create a list of objects to add to with detail
			tableData = parse_detail_table(h4.find_next("table"))

			#add the parsed data to our object
			for item in tableData:
				item['source_url'] = multipleDetailURL[0]
				item['sample_date'] = sample_date
				item['name'] = parse_text(h4)
				# add_field(data, pair[0], pair[1])
			
				output.append(item)

	#otherwise, the table is the whole story
	else:
		for table in contentDiv.find_all("table"):
			tableData = parse_detail_table(table)
			for item in tableData:
				# add_field(data, pair[0], pair[1])
				item['source_url'] = multipleDetailURL[0]
				item['sample_date'] = sample_date
				output.append(item)
	return output

def parse_table_page(source_url):
	output = [] #list of output objects
	#load the page and process each table
	tableDocument = get_doc(source_url)
	tablePage = tableDocument.find(id="mainContent")
	tableList = tablePage.find_all("table")
	#Do we need to get limits for multiple tables on a page
	multipleTables = False
	if (len(tableList) > 1):
		multipleTables = True
	#process each table
	for table in tableList:
		#headers are in the top row
		headers = []
		currentRow = {}
		getHeaders = True
		#if there are more than one table on the page, then the scope of each table is in the preceeding paragraph
		if (multipleTables):
			limit = table.find_previous_sibling(["p", "h1", "h2", "h3", "h4"])
			while (limit.find("a") != None): #keep going until you get something that doesn't have a link
				limit = limit.find_previous_sibling(["p", "h1", "h2", "h3", "h4"]) #don't want it to have a link
			limitWords = limit.string.split(" ") #remove ordinal numbers
			if ((limitWords[0] == "I.") or (limitWords[0] == "II.")):
				limit = " ".join(limitWords[1:]).capitalize()
			else:
				limit = " ".join(limitWords).capitalize()
		
		rowList = table.find_all("tr")
		changed_headers = []
		for row in rowList:
			#load first row as headers
			if (getHeaders):
				#cope with fact some pages use <th> in <thead> for headers
				headerRow = row.find_all(["td", "th"])
				for item in headerRow:
					#check where we have a colspan -> merged cells in one row of header
					if ("colspan" in item.attrs):
						cols_spanned = int(item["colspan"])
						cols_count = 0
						row_below = rowList[rowList.index(row) + 1]
						while (cols_count < cols_spanned):
							#extract info from the cell below
							cell_below = row_below.find(["td", "th"]) #we are going to extract it when we're done with it, so always looking for the first one
							cell_below_contents = parse_text(cell_below)
							cell_below.decompose()
							#combine cell below and above into a new cell
							new_cell = tableDocument.new_tag("td")
							new_cell_contents = parse_text(item) + " " + cell_below_contents
							new_cell.append(new_cell_contents)
							headers.append(parse_text(new_cell, True))
							#add the new cell and remove old one when done with it
							item.insert_after(new_cell)
							if (cols_count == (cols_spanned - 1)):
								item.decompose()
							cols_count += 1
					else:
						headers.append(parse_text(item, True))
				getHeaders = False
				#check there's something there	
				if (len(''.join(headers)) == 0):
					break
			#deal with normal row
			else:
				#new object we're creating
				data = {
					'source_url': source_url,
					'sample_date': sample_date,
				}
				if (multipleTables):
					data["limit"] = limit

				newFields = False #have we added any new info to this object?
				rowItems = row.find_all("td")
				
				#deal with short rows -- to few columns, by adding columns to the end and trying again
				while (len(rowItems) < len(headers)):
					new_cell = tableDocument.new_tag("td")
					row.append(new_cell)
					rowItems = row.find_all("td")

				#now actually process the row
				cellCount = 0
				for item in rowItems:
					if (len(parse_text(item)) > 0):
						#Deal with merged rows across -> when you come across the top of it, replicate it on rows below
						if ("rowspan" in item.attrs):
							row_span = int(item["rowspan"])
							rows_below = 1
							row_index = rowList.index(row)
							while (rows_below < row_span):
								if ((row_index + rows_below) >= len(rowList)):
									break #check there is a row to drop onto
								row_below = rowList[row_index + rows_below]
								#create a new cell with a copy of the current cell's contents
								new_cell = tableDocument.new_tag("td")
								for thingy in item.contents:
									new_cell.append(parse_text(thingy).replace(u"<br/>", u"\n"))
								row_below.insert(cellCount, new_cell) #add it to the right place below
								rows_below += 1

						#process the data on this row itself
						header = headers[cellCount]
						if (header not in ["no.", "no", "row_number", u"p._č."]): #ignore row numbers
							#handle dates separately
							if (header in date_fields):
								data[header] = parse_date(parse_text(item))
							else:
								if (header == "amount_of_issue"):
									data[header] = parse_int(parse_text(item))
								else:
									#if the name is a link, add it as a url - only if it isn't one of the headers in the table
									if (item.find("a") != None):
										if (header in ["name", "business_name", "name_of_company"]):
											need_to_add = True
											for word in ["url", "website", "internet_address"]:
												if (word in headers):
													need_to_add = False
													break
											if (need_to_add):
												add_field(data, "website", parse_text(item.find("a")['href']))
												add_field(data, "name", item.find("a").string)
										else:
											link_text = parse_text(item)
											if ((link_text == "yes") or (link_text == "Here")):
												#deal with sub page containing a list of items
												sub_item_link = item.find("a")["href"]
												try:
													sub_items = parse_table_page(sub_item_link)
													add_field(data, header, sub_items)
												except:
													sub_items = parse_licensed_activity_page(sub_item_link)
													add_field(data, header, sub_items)
											else:
												#deal with normal page
												add_field(data, header, parse_text(item))
									else: #cope with special case - extract currency and process number
										if (header == "share_capital_in_eur"):
											changed_headers.append("share_capital_in_eur")
											add_field(data, 'currency', "EUR")
											number = parse_text(item).replace("EUR", "")
											add_field(data, 'share_capital', parse_int(number))
										else: #have seen a semi-colon separated list
											if ((header == "bider") and (";" in parse_text(item))):
												add_field(data, header, parse_text(item).split(";"))
											else:
												if (parse_text(item) not in ["*", "*/", "**/", "***/", "P", "DP", "DP-1", "DP-2", "DP-3"]):
													add_field(data, header, parse_text(item)) #add normal item
												else:
													changed_headers.append(header)
							newFields = True #record that there's something interesting going on
					cellCount += 1

				#output our object if we've done anything with it
				if (newFields):
					#extract name field if held differently -> need to update headers too so it will add the object
					if ("name" not in data):
						name_fields = ["business_name", "name_of_insurance_company", u"issuer´s_name", "bond_issuers", "issuers", "name/address"]
						for name_field in name_fields:
							if (name_field in data):
								add_field(data, "name", data[name_field])
								del(data[name_field])
								changed_headers.append(name_field)
								headers.append("name")
						if (("surname" in data) and ("degree_and_first_name" in data)):
							data["name"] = data["degree_and_first_name"] + " " + data["surname"]
							headers.append("name")
						if (("name_of_the_offeror" in data) and ("name_of_the_issuer" not in data)):
							data["name"] = data["name_of_the_offeror"]
							del(data["name_of_the_offeror"])
							changed_headers.append("name_of_the_offeror")
							headers.append("name")

					#only store our object if there is data for each of the fields in the table
					got_all_headers = True
					for header in headers:
						if (header not in data):
							if (header not in ["no.", "no", "row_number", u"p._č.", u"created_and_managed_funds_contributory", u"created_and_managed_funds_payout"]): #don't worry if we didn't add one of these
								if (header not in changed_headers): #don't need to worry about not having the ones we took out
									got_all_headers = False
					if (got_all_headers):
						output.append(data)
	return output

#deal with the complicated way licensed activities are shown for investment firms with license according to Act No 566/2001
def parse_licensed_activity_page(source_url):
	activity_document = get_doc(source_url)
	activity_table = activity_document.find("table", "tblBorder") #it's always the first one of these
	output = []

	#meaning of the letters mentioned - source: http://www.nbs.sk/_img/Documents/_Legislativa/_BasicActs/A566-2001.pdf
	instruments = { 
		"a": "transferable securities",
		"b": "money market instruments",
		"c": "fund shares or securities issued by foreign collective investment undertakings",
		"d": "options, futures, swaps, forwards and any other derivate contracts relating to securities",
		"e": "options, futures, swaps, forwards and any other derivative contracts relating to commodities that must be settled in cash or may be settled in cash at the option of one of the parties (otherwise than by reason of a default or other termination event)",
		"f": "options, futures, swaps and any other derivative contract relating to commodities that can be settled in cash provided that they are traded on a regulated market or a multilateral trading facility",
		"g": "options, futures, swaps, forwards and any other derivative contracts relating to commodities that can be settled in cash and are not traded on a regulated market or a mulitlateral trading facility, and not being for commercial purposes, which have the characteristics of other derivative financial instruments, having regard to whether they are cleared or settled through the clearing and settlement system or are subject to regular margin calls",
		"h": "derivative instruments for the transfer of credit risk",
		"i": "financial contracts for differences",
		"j": "options, futures, swaps, forwards and any other derivates concerning climatic variables, freight rates, emission allowances or inflation rates or other official economic statistics that must be settled in cash or may be settled at the option of one of the parties (otherwise than by reason of insolvency or other termination event), as well as any other derivatives concerning assets, rights, obligations, indices and other factors not otherwise mentioned in subparagraphs (a) to (i), which have the characteristics of other derivative financial instruments, having regard to whether they are traded on a regulated market or multilateral trading facility, are cleared or settled through the clearing and settlement system or are subject to regular margin calls"
	}
	investment_activities = {
		"a": "reception and transmission of client orders in relation to one or more financial instruments",
		"b": "execution of orders on behalf of clients",
		"c": "dealing on own account",
		"d": "portfolio management",
		"e": "investment advice",
		"f": "underwriting or placing of financial instruments on a firm commitment basis",
		"g": "placing of financial instruments without a firm commitment basis",
		"h": "operation of multilateral trading facilities"
	}
	ancillary_activities = {
		"a": "safekeeping and administration of financial instruments for the account of clients, including custodianship and related services, such as cash/collateral management",
		"b": "granting credits or loans to an investor to allow him to carry out a transaction in one or more financial instruments, where the provider of the credit or loans is involved in the transaction",
		"c": "advice on capital structure and business strategy, and advice and services relating to the merger, consolidation, transformation or splitting of undertakings or the purchase of undertakings",
		"d": "foreign exchange services where these are connected to the provision of investment services",
		"e": "investment research and financial analysis or the other forms of general recommendation relating to transactions in financial instruments",
		"f": "services related to the underwriting of financial instruments",
		"g": "services and activities mentioned in paragraph (1)(a) to (f) related to the underlying of the derivatives included in under Article 5(e) to (g) and (j), where these are connected to the provision of investment or ancillary services"
	}

	#get the headers from the top two rows
	headers = []
	table_rows = activity_table.find_all("tr")
	second_row = table_rows[1].find_all(["td", "th"])
	for cell in second_row:
		cell_text = parse_text(cell).lstrip("letter").lstrip("para").rstrip(")").strip()
		headers.append(cell_text)
	
	#now do the other rows -> work out where the combinations are
	for other_row in table_rows[2:]:
		activity_dict = investment_activities
		activity_type = "investment"
		cells = other_row.find_all("td")
		label_cell = 0 #normally, the first cell on a row is the para letter 

		#first row -> label cell isn't the top one
		if (table_rows.index(other_row) == 2):
			label_cell = 1

		#reset reference for moving over - have to work it out because it isn't fixed
		if ((len(cells) == (len(headers) + 2)) and (table_rows.index(other_row) != 2)):
			activity_dict = ancillary_activities
			activity_type = "ancillary"
			label_cell = 1

		#get the label for this one
		activity_letter = parse_text(cells[label_cell]).lstrip("letter").lstrip("para").rstrip(")").strip()

		#go through the data and find blue cells, which have a special class
		column_number = 0
		for cell in cells[(label_cell + 1):]:
			if ("class" in cell.attrs):
				if ("bgBlue" in cell.attrs["class"]):
					limit = 1
					done = 0
					#sometimes they merged cells to colour them all in
					if ("colspan" in cell.attrs):
						limit = int(cell.attrs["colspan"])
					
					while (done < limit):
						if (column_number >= (len(cells) - label_cell)):
							break #again, i bet they could get their colspan wrong and send you off the edge
						instrument = instruments[headers[column_number]]
						activity = activity_dict[activity_letter]
						result = {
							"instrument": instrument,
							"activity": activity,
							"activity_type": activity_type,
							"source_url": source_url
						}

						#check for restrictions -> done as a note elsewhere in page
						notation = parse_text(cell)
						if (len(notation) > 0):
							#look for the header above the actual restrictions
							restriction_start = activity_document.find_all(text="Restriction")[-1] #it's the last one
							while (restriction_start.name != "tr"): #it's always part of a table, so zoom out till you have the row
								restriction_start = restriction_start.parent
							restrictions = restriction_start.find_next_siblings("tr") #get the other rows below -> these are the actual restrictions
							if (len(restrictions) == 1): #only one row? grab the second cell
								restriction = parse_text(restrictions[0].find_all("td")[1])
							else: #have to work out which row we need
								number = int(notation[-1]) #last character of restriction
								restriction = parse_text(restrictions[number - 1].find_all("td")[1])

							#decode terms
							if (restriction == "The company is allowed to provide the investment servicies and to perform the investment activities pursuant to Art. 6(1)(a), (b), (c) and (e) and to provide the ancillary service pursuant to Art. 6(2)(a) of Act No 566/2001 Coll. only in relation to such financial instruments pursuant to Art. 5(1)(d) of Act No 566/2001 Coll. from which swaps are excluded."):
								restriction = "The company is not allowed to perform this service/activity in relation to swaps."
							if (restriction == "The company is allowed to provide the investment servicies and to perform the investment activities pursuant to Art. 6(1)(a), (b) and (c) and to provide the ancillary service pursuant to Art. 6(2)(a) of Act No 566/2001 Coll. only in relation to such financial instruments pursuant to Art. 5(1)(e), (f) and (g) of Act No 566/2001 Coll. which are commodity futures."):
								restriction = "The company is only allowed to perform this service/activity in relation to commodity futures."
							if (restriction == "The company is allowed to provide investment services pursuant to Art. 6(1) (g) only in relation to such financial instruments pursuant to Art. 5(1)(d) of Act No 566/2001 Coll. which are related to currencies, interest rates or yields."):
								restriction = "The company is only allowed to perform this service/activity in relation to financial instruments which are related to currencies, interest rates or yields."

							add_field(result, "restriction", restriction)

						#store the result and move to next cell
						output.append(result)
						column_number += 1
						done += 1
	return output

#parse an integer from text
def parse_int(input):
	value = input.replace(",", "") #remove commas
	value = ''.join(value.split()) #remove all whitespace
	return int(value)

#parse an floating number from text - deals with decimal points and commas. Remove parameter is an optional list of strings to remove
def parse_float(input, remove=[]):
	value = input
	value = ''.join(value.split()) #remove all whitespace
	for removeItem in remove: #remove the items we want to remove
		value = value.replace(removeItem, "")
	#is it commas for thousands and decimal points, or spaces for thousands and decimal commas?
	if ("." in value): 
		value = value.replace(",", "")
	else: #decimal commas, remove spaces and convert to point
		value = value.replace(",", ".")
	return float(value) * 1000

#parse date in text form	
def parse_date(input):
	#extract the first three words - which will be the date bit only and not extra commentary
	dateWords = input.split(" ") #split into words
	value = " ".join(dateWords[:3])
	value = value.replace("Jule", "July") #am aware of the typo
	#It would be nice if they used one format, but there are several we need to cope with...
	try:
		value = datetime.datetime.strptime(value, "%d %B %Y")
	except ValueError:
		try:
			value = datetime.datetime.strptime(value, "%d.%m.%Y")
		except ValueError:
			try:
				value = datetime.datetime.strptime(value, "%d. %B %Y")
			except ValueError:
				try:
					value = datetime.datetime.strptime(value, "%B %d, %Y")
				except ValueError:
					try:
						value = datetime.datetime.strptime(value, "%d %B, %Y")
					except ValueError:
						try:
							value = datetime.datetime.strptime(value, "%Y")
						except:
							#return a list of parsed dates
							if ("," in value):
								dateList = value.split(",")
								i = 0
								while i < len(dateList):
									dateList[i] = parse_date(dateList[i].strip())
									i += 1
								value = dateList
							else:
								return value #give up!

	if (isinstance(value, list)):
		return value
	else:
		return value.strftime("%Y-%m-%d")

def parse_text(input, label=False):
	output = ""
	if (len(input) > 0): #do stuff if there's any text to parse
		for item in input:
			contents = item
			count = 0
			#deal with links in the text...
			while (isinstance(contents, bs4.element.Tag)):
				if (len(contents.contents) == 0):
					contents = " "
					break #deal with empty tags
				contents = parse_text(contents)
				count += 1
				if (count == 100):
					break
			output += contents

	output = " ".join(output.split())
	output = output.strip()
	output = output.rstrip(":") #remove punctuation/whitespace
	if (label): #make it suitable for use as a field name
		output = output.replace(" ", "_")
		output = output.lower()
		
		#swap over any errors/translations types
		if (output in replacement_labels):
			output = replacement_labels[output]
	
	return output.strip()

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


#recursively go through elements and add all child strings -> hoping it works to alter list outside its own scope
def append_children(input_tag, existing_list):
	if (isinstance(input_tag, bs4.element.Tag)):
		for child in input_tag.children:
			#base case - there is some text to read
			if (child.string != None):
				child_text = parse_text(child.string)
				if (len(child_text) > 0):
					if (child_text.find("<xml>") == -1): #ignore anything that looks like html comments
						if (len(existing_list) > 0):
							if (child_text.replace(" ", "").replace("-", "").replace("_", "").isnumeric()): #if it's all numbers, and so is the last item, merge them 
								if (existing_list[len(existing_list) - 1].replace(" ", "").replace("-", "").replace("_", "").isnumeric()):
									existing_list[len(existing_list) - 1] += " " + child_text
								else:
									#split it by colon if there is one
									if (child_text.find(":") != -1):
										find_point = child_text.find(":")
										existing_list.append(child_text[:find_point])
										existing_list.append(child_text[find_point + 1:].strip())
									else: #otherwise add it as normal
										existing_list.append(child_text)
							else:
								existing_list.append(child_text)
						else:
							existing_list.append(child_text)
			else:
				append_children(child, existing_list)

#from a list of elements, extract the relevant text as a list of simple strings 
def gather_detail_list(elementList):
	detailList = []
	for item in elementList:
		if (item.name == "p") or (item.name == "strong"):
			for child in item.contents:
				child_text = parse_text(child)
				if (len(child_text) > 0): #ignore empty lines/line breaks
					if (child_text.replace(" ", "").isnumeric()): #if it's all numbers, and so is the last item, merge them 
						if (detailList[len(detailList) - 1].replace(" ", "").isnumeric()):
							detailList[len(detailList) - 1] += " " + child_text
						else:
							detailList.append(child_text)
					else: #otherwise add it as a new item as normal
						#if it contains a colon, split it in two
						if (child_text.find(":") != -1):
							find_point = child_text.find(":")
							detailList.append(child_text[:find_point])
							detailList.append(child_text[find_point + 1:].strip())
						else: #otherwise add it as normal
							if (not((child_text[0] == "(") and (child_text[len(child_text) - 1] == ")"))): #ignore bracketed text
								detailList.append(child_text)
		#this is to cope with the fact that the introduction to a list of items will be in the previous paragraph
		if ((item.name == "ul") or (item.name == "li") or (item.name == "table")):
			ul_list = [] #form a list which we will treat as one value
			append_children(item, ul_list)
			if (len(ul_list) > 0):
				detailList.append(ul_list)
	return detailList

#convert a list of strings into key/value pairs of the given object
def make_data_from_detail_list(detailList, data):
	for i in xrange(0, len(detailList), 2):
		if ((i + 1) < len(detailList)):
			if (parse_text(detailList[i], True) == "date_of_validiity"):
				detailList[i] = "date_of_validity" #correct spelling
			#parse dates before adding to our object
			if (parse_text(detailList[i], True) in date_fields):
				detailList[i + 1] = parse_date(detailList[i + 1])
			add_field(data, parse_text(detailList[i], True), parse_text(detailList[i + 1]))

#start from a given element and return a list of subsequent elements
def gather_element_list(startingElement, stopList=[]):
	elements = []
	element = startingElement
	if (startingElement is None):
		return []
	while (not (isinstance(element, bs4.element.Tag) and (element.name == "h1"))):
		#we're only after actual tags
		if (isinstance(element, bs4.element.Tag)):
			#have an override buffer - if we run into one of the specified tags, we've gone too far and must stop
			if (element.name in stopList):
				return elements
			elements.append(element)
		if (element.next_sibling is None):
			break
		element = element.next_sibling
	return elements

#print out the object list in a nice, readable format
def print_objects(objects):
	for item in objects:
		if ('name' in item):
			print(unicode(item['name']) + ":")
		else:
			print("unnamed item:")
		for pair in item.items():
			if (unicode(pair[0]) != "name"):
				print(u"    " + unicode(pair[0]) + u": " + unicode(pair[1]))
		print("")

#print out a list of labels from the object list, and highlight any with weird labels
def print_labels(objects):
	label_list = []
	naughty_object_list = []
	for item in objects:
		for label in item:
			if (label not in label_list):
				label_list.append(label)
	for label in label_list:
		print(label)
	if (len(naughty_object_list) > 0):
		print("")
		print_objects(naughty_object_list)

#print all the unique values for a given field
def print_field(objects, field):
	field_values = []
	for item in objects:
		if (field in item):
			if (item[field] not in field_values):
				field_values.append(item[field])
	for value in field_values:
		print(value)

#START DOING STUFF
turbotlib.log("Starting run on " + sample_date + "...") # Optional debug logging

#SOURCE URLS

#list of links to navigation pages with a list of regulated entities. Stored as a list of these: [url, description]
detailURLs = [
	["http://www.nbs.sk/en/financial-market-supervision/banking-sector-supervision/List-of-credit-institutions/commercial-and-savings-banks", "Commercial and Savings Banks in Slovakia"],
	["http://www.nbs.sk/en/financial-market-supervision/banking-sector-supervision/List-of-credit-institutions/branch-offices-of-foreign-banks/banks", "Branch offices of Foreign Banks in Slovakia"],
	["http://www.nbs.sk/en/financial-market-supervision/banking-sector-supervision/List-of-credit-institutions/branch-offices-of-foreign-banks/credit-cooperatives", "Branch offices of Foreign Credit Cooperatives in Slovakia"],
	["http://www.nbs.sk/en/financial-market-supervision/banking-sector-supervision/List-of-credit-institutions/branch-offices-of-slovak-banks-operating-abroad", "Branch offices of Slovak Banks operating aboard"],
	["http://www.nbs.sk/en/financial-market-supervision/banking-sector-supervision/List-of-credit-institutions/slovak-banks-providers-of-services-on-the-cross-border-basis-abroad", "Slovak banks providing services on the cross-border basis abroad"],
	["http://www.nbs.sk/en/financial-market-supervision/banking-sector-supervision/List-of-credit-institutions/banks-in-special-proceedings", "Banks in special proceedings"]
]

#list of links to pages which contain details of more than one regulated entity. Stored as a list of these [url, description, whether the entity name is in an h4 above the table]
multipleDetailURLs = [
	["http://www.nbs.sk/en/financial-market-supervision/banking-sector-supervision/List-of-credit-institutions/representative-offices-of-foreign-banks-in-the-slovak-republic", "Representative offices of Foreign Banks in Slovakia"],
	["http://www.nbs.sk/en/financial-market-supervision/banking-sector-supervision/List-of-credit-institutions/representative-offices-of-slovak-banks-abroad", "Representative offices of Slovak banks abroad"],
	["http://www.nbs.sk/en/financial-market-supervision/electronic-money-institutions-supervision/list-of-electronic-money-institutions/ceased-licence", "Ceased licences for Electronic Money Institutions"]
]

#Where details can include a list -> first off, let's collate the list from the navigation page
listDetailURLs = [
	["http://www.nbs.sk/en/financial-market-supervision/securities-market-supervision/collective-investment/list-of-supervised-entities/list-of-foreign-management-company-operating-through-branch-under-article-75-aoci", "Foreign management company operating through branch"],
	["http://www.nbs.sk/en/financial-market-supervision/securities-market-supervision/collective-investment/list-of-supervised-entities/list-of-compulsory-administrators", "Compulsory administrators"]
]
for link in parse_link_page("http://www.nbs.sk/en/financial-market-supervision/securities-market-supervision/collective-investment/list-of-supervised-entities/list-of-domestic-management-companies-and-their-mutual-funds"):
	listDetailURLs.append([link, "Domestic management companies and their mutual funds"])

#Only got one page so far with details of several different entities in this format
itemListDetailURLs = [
	["http://www.nbs.sk/en/financial-market-supervision/securities-market-supervision/collective-investment/list-of-supervised-entities/list-of-expired-licences", "Expired collective investment licences"]
]

#Pages with a proper actual table of data (or more than one)
tableURLs = [
	["http://www.nbs.sk/en/financial-market-supervision/payment-institutions-supervision/list-of-payment-institutions/payment-institutions-with-its-registered-office-in-the-territory-of-the-slovak-republic", "Payment institutions with registered offices in the territory of the Slovak Republic"],
	["http://www.nbs.sk/en/financial-market-supervision/payment-institutions-supervision/list-of-payment-institutions/branch-offices-of-slovak-payment-institutions-operating-abroad", "Branch offices of Slovak payment institutions operating abroad"],
	["http://www.nbs.sk/en/financial-market-supervision/payment-institutions-supervision/list-of-payment-institutions/ceased-licences", "Ceased licences for payment institutions"],
	["http://www.nbs.sk/en/financial-market-supervision/insurance-supervision/list-of-insurance-companies/ic-with-head-office-in-sr/insurance-companies-that-quit-their-activity", "Insurance companies that ceased activity"],
	["http://www.nbs.sk/en/financial-market-supervision/insurance-supervision/list-of-insurance-companies/ic-with-head-office-in-sr/ic-with-head-office-in-sr-providing-activitie-in-another-member-state/through-its-branch-office", "Slovak insurance companies providing activities in another EU member state"],
	["http://www.nbs.sk/en/financial-market-supervision/insurance-supervision/actuaries/list-of-actuaries", "Actuaries"],
	["http://www.nbs.sk/en/financial-market-supervision/pension-saving-supervision/old-age-pension-saving-system/list-of-pension-asset-management-companies", "Pension asset management companies"],
	["http://www.nbs.sk/en/financial-market-supervision/pension-saving-supervision/supplementary-pension-saving-system/list-of-supplementary-pension-asset-management-companies", "Supplementary pension asset management companies"],
	["http://www.nbs.sk/en/financial-market-supervision/securities-market-supervision/securities-issuers/stock-issuers/main-listed-market", "Stock issuers on the main listed market"],
	["http://www.nbs.sk/en/financial-market-supervision/securities-market-supervision/securities-issuers/stock-issuers/parallel-listed-market", "Stock issuers on the parallel listed market"],
	["http://www.nbs.sk/en/financial-market-supervision/securities-market-supervision/securities-issuers/stock-issuers/regulated-free-market", "Stock issuers on the regulated free market"],
	["http://www.nbs.sk/en/financial-market-supervision/securities-market-supervision/securities-issuers/bond-issuers/main-listed-market", "Bond issuers on the main listed market"],
	["http://www.nbs.sk/en/financial-market-supervision/securities-market-supervision/securities-issuers/bond-issuers/parallel-listed-market", "Bond issuers on the parallel listed market"],
	["http://www.nbs.sk/en/financial-market-supervision/securities-market-supervision/securities-issuers/bond-issuers/regulated-free", "Bond issuers on the regulated free market"],
	["http://www.nbs.sk/en/financial-market-supervision/securities-market-supervision/securities-issuers/bond-issues-under-art-114-paragraph-2-of-the-act-on-collective-investment", "Bond issuers under Article 210 paragraph 2 of the Act No 203/2011 Coll. on collective investment"],
	["http://www.nbs.sk/en/financial-market-supervision/securities-market-supervision/collective-investment/list-of-depositories1", "Depositories"],
	["http://www.nbs.sk/en/financial-market-supervision/securities-market-supervision/investment-firms/list-of-supervised-entities/566", "Investment firms with license according to Act No 566/2001"],
	["http://www.nbs.sk/en/financial-market-supervision/securities-market-supervision/investment-firms/list-of-supervised-entities/ocp/iIF-without-branch", "Investment firms providing investment services abroad without having to establish a branch"],
	["http://www.nbs.sk/en/financial-market-supervision/securities-market-supervision/investment-firms/list-of-supervised-entities/ocp/investment-firms-providing-services-abroad-through-branch", "Investment firms providing investment services abroad through a branch office"],
	["http://www.nbs.sk/en/financial-market-supervision/securities-market-supervision/investment-firms/list-of-supervised-entities/announcement-about-withdrawal-of-licence", "Companies whose licence for acting as an investment firm has been withdrawn"],
	["http://www.nbs.sk/en/financial-market-supervision/securities-market-supervision/takeover-bids-and-squezze-out-right-and-sell-out-right/list-of-takeover-bids", "List of takeover bids"],
	["http://www.nbs.sk/en/financial-market-supervision/securities-market-supervision/takeover-bids-and-squezze-out-right-and-sell-out-right/list-of-a-legal-person-or-a-natural-person", "List of legal and natural persons who have the approbation of the National Bank of Slovakia on the application laws of squeeze out"],
	["http://www.nbs.sk/en/financial-market-supervision/securities-market-supervision/public-offer/lists/list-of-offers-of-securities", "Offers of securities"],
	["http://www.nbs.sk/en/financial-market-supervision/securities-market-supervision/public-offer/lists/list-of-approved-listing-particulars-for-the-securities", "Approved listing particulars for securities"],
	["http://www.nbs.sk/en/financial-market-supervision/securities-market-supervision/public-offer/lists/list-of-offers-of-assets", "Offers of assets"]
]

#Output containers
primary_data = [] #store results at the end

#1 Navigation Lists
turbotlib.log("Scraping pages with a navigation list")
if (len(detailURLs) == 0):
	turbotlib.log("None found")
for detailURL in detailURLs:
	turbotlib.log("Identifying " + detailURL[1])
	entityList = parse_link_page(detailURL[0])
	if (len(entityList) == 0):
		turbotlib.log("None found")
	entityCount = 1
	for entityLink in entityList:
		turbotlib.log("Processing " + str(entityCount) + "/" + str(len(entityList)))
		entityItemList = parse_detail_page(entityLink)
		for entityItem in entityItemList:
			entityItem['scope'] = detailURL[1] #keep in mind where we found our source
			primary_data.append(entityItem)
		entityCount += 1

# # #2 Pages with multiple details
turbotlib.log("Scraping pages containing details of multiple entities")
if (len(multipleDetailURLs) == 0):
	turbotlib.log("None found")
multipleCount = 1
for multipleDetailURL in multipleDetailURLs:
	turbotlib.log("Processing " + str(multipleCount) + "/" + str(len(multipleDetailURLs)) + " - " + multipleDetailURL[1])
	multipleItems = parse_multiple_detail_page(multipleDetailURL[0]) #parse the item
	for item in multipleItems:
		item['scope'] = multipleDetailURL[1]
		primary_data.append(item)
	multipleCount += 1

# #3 Detail pages where one of the items is a list
turbotlib.log("Scraping pages with a detail item is a list")
if (len(listDetailURLs) == 0):
	turbotlib.log("None found")
detailCount = 1
for listDetailURL in listDetailURLs:
	turbotlib.log("Processing " + str(detailCount) + "/" + str(len(listDetailURLs)) + " - " + listDetailURL[1])
	listDetailPage = get_doc(listDetailURL[0]).find(id="mainContent")
	
	#Some pages have entity name as h4. Those seem to be the ones where there could be multiple entities per page
	h4_list = listDetailPage.find_all("h4")
	if (len(h4_list) > 0):
		for h4 in h4_list:
			#read the name from the title
			data = {
				"source_url": listDetailURL[0],
				"sample_date": sample_date,
				"name": parse_text(h4),
				"scope": listDetailURL[1]
			}
			
			elements = gather_element_list(h4.next_sibling) #gather the elements relating to this entity into a list
			detailList = gather_detail_list(elements) #now go through those elements and separate out the contents. normally saved as pairs of strong/not strong spans within a paragraph
			make_data_from_detail_list(detailList, data) #having extracted pairs of details in order from the html soup, now convert from a single line into key/value pairs

	#no h4s - so it's just one entity per page, with its name in the header
	else:
		#read the name from the title
		data = {
			"source_url": listDetailURL[0],
			"sample_date": sample_date,
			"name": parse_text(listDetailPage.find("h1", id="top")),
			"scope": listDetailURL[1]
		}
		elements = gather_element_list(listDetailPage.find("p")) #gather the elements relating to this entity into a list
		detailList = gather_detail_list(elements) #now go through those elements and separate out the contents. normally saved as pairs of strong/not strong spans within a paragraph
		make_data_from_detail_list(detailList, data) # having extracted pairs of details in order from the html soup, now convert from a single line into key/value pairs

	detailCount += 1

# # # 4 Expired collective investment licences list
turbotlib.log("Scraping pages with a list of items")
if (len(itemListDetailURLs) == 0):
	turbotlib.log("None found")
itemListDetailCount = 1
for itemListDetailURL in itemListDetailURLs:
	turbotlib.log("Processing " + str(itemListDetailCount) + "/" + str(len(itemListDetailURLs)) + " - " + itemListDetailURL[1])
	itemListDetailPage = get_doc(itemListDetailURL[0]).find(id="mainContent")
	for h4 in itemListDetailPage.find_all("h4"):
		#create an object
		data = {
			"source_url": "http://www.nbs.sk/en/financial-market-supervision/securities-market-supervision/collective-investment/list-of-supervised-entities/list-of-expired-licences",
			"sample_date": sample_date,
			"name": parse_text(h4),
			"scope": itemListDetailURL[1]
		}

		#all the details are in a next paragraph, split up by line breaks
		elements = gather_element_list(h4.find_next("p"), ["h4"])
		detailList = gather_detail_list(elements)
		make_data_from_detail_list(detailList, data)
		primary_data.append(data)

#5 Pages with a table of details in them
turbotlib.log("Scraping pages with a table of information")
if (len(tableURLs) == 0):
	turbotlib.log("None found")
tableCount = 1
for tableURL in tableURLs:
	turbotlib.log("Processing " + str(tableCount) + "/" + str(len(tableURLs)) + " - " + tableURL[1])
	#get a list of all items in this table, brand them with the scope, then add to the overall list
	table_items = parse_table_page(tableURL[0])
	for item in table_items:
		add_field(item, "scope", tableURL[1])
	primary_data.extend(table_items)
	tableCount += 1

#don't forget to tell them where they're from
for item in primary_data:
	add_field(item, 'source_authority', "National Bank of Slovakia")

#print in a nice format
# print_labels(primary_data)
# print_objects(primary_data)
# print(len(primary_data))
# print_field(primary_data, "scope")

#output the actual json data we need
for item in primary_data:
	print(json.dumps(item))