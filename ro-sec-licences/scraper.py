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

def parse_table(table, further_detail=False):
	items = [] #output
	try:
		rows = table.find_all("tr") #input

		#extract headers
		headers = []
		header_row = rows[0]
		for th in header_row.find_all("th"):
			header = th.text.strip().capitalize()
			headers.append(header)

		#go through the rows - turn each into an object
		for row in rows[1:]:
			td_list = row.find_all("td")
			td_index = 0 #record how far through columns we are, so we can find right header
			item = {} #make item to store findings
			for td in td_list:
				value = td.text.strip()
				if ((len(value) > 0) and (value != "&nbsp;") and (value != "&nbsp")):
					item[headers[td_index]] = value

				#if we have a link then get the url for further details
				if (further_detail):
					if (td.a != None):
						url = td.a['href']
						if (url[:7] != "mailto:"):
							item['detail_url'] = base_href + url

				#ready for next column
				td_index += 1

			if (len(item) > 0):
				items.append(item)
	except:
		pass

	return items

#urls to use
base_href = "http://www.cnvmr.ro/asf/registru/"
front_url = base_href + "lista.php?listasect=1&lng=2"

#get going
sample_date = str(date.today())
turbotlib.log("Starting run on " + sample_date) # Optional debug logging

#Step 1: extract list of categories from front page
try:
	categories = [] #store the list as we find them
	front_page = get_doc(front_url)
	category_list = front_page.find("table", id="listaEntitati")
	category_rows = category_list.find_all("tr")

	current_category = None #maintain link to current category

	for row in category_rows:
		td_list = row.find_all("td")

		#deal only with non-empty rows
		if (len(td_list) > 0):
			#identify categories with sub-categories. to avoid double counting, we'll only add the subcategories to the list
			if (td_list[0].img != None):
				category = {
					'number': td_list[1].text.strip(),
					'symbol': td_list[2].text.strip(),
					'name': td_list[3].text.strip(),	
					'definition': base_href + td_list[4].a['href'],
					'url': base_href + td_list[3].a['href'],
				}
				current_category = category #move link to match this one

			#else we either have a main category with no subcategories, or this is a subcategory
			else:
				#if this has a red circle in column 2, it's a subcategory
				if (td_list[1].img != None):
					subcategory = {
						'number': current_category['number'],
						'symbol': td_list[2].text.strip(),
						'name': td_list[3].text.strip(),
						'definition': current_category['definition'],
						'url': base_href + td_list[3].a['href']
					}
					categories.append(subcategory)
				
				#otherwise, it's an undivided main category
				else:
					undivided_category = {
						'number': td_list[1].text.strip(),
						'symbol': td_list[2].text.strip(),
						'name': td_list[3].text.strip(),
						'definition': base_href + td_list[4].a['href'],
						'url': base_href + td_list[3].a['href']
					}
					categories.append(undivided_category)

	#monitor progress
	turbotlib.log(str(len(categories)) + " categories identified")

	#Step 2: work out what we'll actually want to parse
	category_count = 1
	for category in categories:
		#go get the page and table of details
		try:
			category_page = get_doc(category['url'])
			category_table = category_page.find("table", id="listaEntitati")
			category_items = parse_table(category_table, True)

			#monitor progress
			turbotlib.log(str(len(category_items)) + " items identified in category " + category['symbol'] + " (" + str(category_count) + " / " + str(len(categories)) + ")")
			category_count += 1

		#Step 3: go and get the details on each one of those entities (doing this while we look at the category)
			item_count = 1
			for item in category_items:
				turbotlib.log("  Parsing item " + str(item_count) + " / " + str(len(category_items)) + " in category " + category['symbol'])
				try:
					detail_page = get_doc(item['detail_url'])

					#extract the name from the top of the page
					company_name = detail_page.table.text.strip().title()
					item['company_name'] = company_name

					#all the details we can extract are in tables in frames, with regular layout
					iframes = detail_page.find_all("iframe")
					for iframe in iframes:
						try:
							label = iframe.parent.parent.parent.parent.attrs['id']
							iframe_src = base_href + iframe['src']
							iframe_doc = get_doc(iframe_src)
							iframe_table = iframe_doc.table
							if (iframe_table != None):
								details = parse_table(iframe_table)
								#only one row means add things directly
								if (len(details) == 1):
									if (len(details[0]) == 1): #literally only one field, so add it straight to object
										item[details[0].keys()[0]] = details[0].values()[0]

									else:
										item[label] = details[0]

								elif (len(details) > 1): #more than one row, so add a list
									item[label] = details #add to output
						except:
							pass

					#output our results - after adding metadata
					if (len(item) > 0):
						item['sample_date'] = sample_date
						item['source_url'] = category['url']
						item['category'] = {
							'name': category['name'],
							'number': category['number'],
							'symbol': category['symbol'],
							'definition_url': category['definition']
						}
						item['source'] = "Financial Supervisory Authority, Romania"

						print(json.dumps(item))

				except:
					pass

				item_count += 1

		except:
			pass

except:
	pass

#just confirm we're done
turbotlib.log("Finished run.")