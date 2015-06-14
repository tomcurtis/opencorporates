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

#return a dict of label:value pairs for a given table
def parse_detail_table(table):
	output = {} #use defined terms
	tr_list = table.find_all("tr")
	for tr in tr_list[1:]: #ignore heading row
		td_list = tr.find_all("td")
		label = td_list[0].text.strip().replace(":", "")
		value = td_list[1].text.strip()

		if (len(value) > 0):
			if ('date' not in label):
				output[label] = value
			else:
				#reverse dd-mm-yyyy format dates into yyyy-mm-dd
				date_split = value.split("-")
				if ((len(date_split) == 3) and (len(date_split[0]) == 2) and (len(date_split[2]) == 4)):
					output[label] = date_split[2] + "-" + date_split[1] + "-" + date_split[0]
				else:
					output[label] = value

	return output

#return a list of dicts representing each row in the table
def parse_multiple_detail_table(table):
	output = []
	tr_list = table.find_all("tr")
	
	#extract headers from second row (first is just the title)
	header_cells = tr_list[1].find_all("td")
	headers = []
	for cell in header_cells:
		headers.append(cell.text.strip().replace(":", ""))

	#now process remaining rows
	for tr in tr_list[2:]:
		item = {} #let's add to this
		td_list = tr.find_all("td")
		td_count = 0
		
		#work through cells, adding label:value pairs to item
		for td in td_list:
			label = headers[td_count]
			value = td.text.strip()
			if (len(value) > 0):
				if ('date' not in label):
					item[label] = value
				else:
					#reverse dd-mm-yyyy format dates into yyyy-mm-dd
					date_split = value.split("-")
					if ((len(date_split) == 3) and (len(date_split[0]) == 2) and (len(date_split[2]) == 4)):
						item[label] = date_split[2] + "-" + date_split[1] + "-" + date_split[0]
					else:
						item[label] = value

			td_count += 1
		
		#if we found any info, let's have it
		if (len(item) > 0):
			output.append(item)

	return output

#Lists of entities to be processed
entity_lists = [
	{'url': "http://asfro.ro/em/ra/registru_en.php?reg=as", 'country': "Romania", 'category': "Section A - Insurance undertakings"},
	{'url': "http://asfro.ro/em/ra/registru_en.php?reg=ab", 'country': "Romania", 'category': "Section A - Intermediaries"},
	{'url': "http://asfro.ro/em/ra/registru_en.php?reg=bs", 'country': "Romania", 'category': "Section B - Insurance undertakings"},
	{'url': "http://asfro.ro/em/ra/registru_en.php?reg=bb", 'country': "Romania", 'category': "Section B - Intermediaries"},
	{'url': "http://asfro.ro/em/cs/cautare_en.php?tip=s&mod=d", 'country': "Overseas", 'category': "Insurance undertakings and intermediaries from EEA"}
]

#different pages needed depending on registry used
detail_urls = {
	'Romania': "http://asfro.ro/em/ra/detalii_en.php?cod=",
	'Overseas': "http://asfro.ro/em/cs/detalii_en.php?cod="
}

#get going
sample_date = str(date.today())
turbotlib.log("Starting run on " + sample_date) # Optional debug logging

#Step 1: load index page and see how many pages there are in this category
for category in entity_lists:
	try:
		turbotlib.log("Parsing category " + category['category'])
		category_page = get_doc(category['url'])
		
		#identify the relevant links and then see which has the highest number
		link_list = category_page.find_all("a")
		highest_link = 1
		for link in link_list:
			if (link['href'][0] == "?"): #these ones start with a question mark
				link_text = link.string.strip()
				if (link_text.isnumeric()):
					page_number = int(link_text)
					if (page_number > highest_link):
						highest_link = page_number
		
		#extract details from the first page and remaining pages
		code_list = parse_entity_list(category_page)
		if (category['category'] != "Insurance undertakings and intermediaries from EEA"): #only look at first page for this category because the site is broken and won't show further pages
			for page_number in xrange(2, highest_link + 1):
				try:
					new_page_url = category['url'] + "&page=" + str(page_number)
					new_page = get_doc(new_page_url)
					code_list += parse_entity_list(new_page)
				except:
					pass

		#now we have our list of pages, we need to go and get the details
		for code in code_list:
			turbotlib.log("Parsing entity " + code)
			detail_page_url = detail_urls[category['country']] + code
			try:
				detail_page = get_doc(detail_page_url)

				output = {
					'sample_date': sample_date,
					'source_url': detail_page_url,
					'source': 'Financial Supervisory Authority, Romania',
					'category': category['category']
				}
				added_detail = False #keep track of info added

				#all using the same template, so should be possible to extract same details
				first_table = detail_page.table
				name = first_table.tr.td.b.text.strip()
				if (name != None):
					output['name'] = name
				
				#all-domestic categories don't say the country, so we need to add it in. for overseas, it's shown
				if (category['country'] == "Romania"):
					output['Country'] = "Romania"

				#all should have a first table of details
				detailed_tables = first_table.find_all("table")
				table_headers = detail_page.find_all(attrs={'class': 'tableheader'})
				for table_header in table_headers:
					#if it's a relevant header, zoom out to get the whole table and then parse it
					header = table_header.text.strip()
					if ((header == "Comany card") or (header == "Company info")):
						table = table_header.parent.parent
						table_details = parse_detail_table(table)
						for label, value in table_details.items():
							output[label] = value
							added_detail = True

					if (header == "Supervisoty authority"):
						table = table_header.parent.parent
						table_details = parse_detail_table(table)
						if (len(table_details) > 0):
							output['Regulator'] = table_details
							added_detail = True

					if (header == "Kind of insurance practiced"):
						table = table_header.parent.parent
						table_details = parse_multiple_detail_table(table)
						if (len(table_details) > 0):
							output['Insurance activities'] = table_details
							added_detail = True

					if (header == "Structuri teritoriale"):
						table = table_header.parent.parent
						table_details = parse_multiple_detail_table(table)
						if (len(table_details) > 0):
							output['Territorial structure'] = table_details
							added_detail = True

				if (added_detail): #only output if we've actually added some information
					print(json.dumps(output))
			
			except:
				pass
	
	except:
		pass

turbotlib.log("Finished run")